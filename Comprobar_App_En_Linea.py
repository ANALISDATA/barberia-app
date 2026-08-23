"""Comprueba que la app publicada esté funcionando de verdad para un cliente.

Se ejecuta con doble clic en `Comprobar app en linea.bat`, o a mano:

    python Comprobar_App_En_Linea.py

POR QUÉ EXISTE: que las pruebas pasen aquí NO garantiza que la app esté arriba.
El 21/08/2026 el código estaba perfecto -- las 5 páginas probadas en un entorno
limpio con las mismas librerías del servidor -- y aun así la app publicada
estaba caída con un error de importación: el despliegue se quedó a medias tras
varias subidas seguidas. Sin esta comprobación, eso se descubre cuando un
cliente no puede pedir su cita.

CÓMO COMPRUEBA, y por qué así: una app de Streamlit se dibuja en el navegador,
no en el servidor. El HTML que llega por la red es el mismo esté la app sana o
rota, así que mirar ese HTML no sirve de nada (el primer intento de este script
daba falsas alarmas por eso). Hace falta un navegador de verdad que cargue la
página y mire lo que quedó pintado. Si Playwright no está instalado, se hace lo
único que se puede sin navegador -- preguntarle al servidor si está vivo -- y se
avisa claramente de que esa comprobación es más floja.
"""
import sys
from pathlib import Path
from urllib.request import Request, urlopen

URL_BASE = "https://esteban-barber.streamlit.app"
RUTAS = {"": "portada", "cita": "pedir cita", "productos": "productos"}

# El panel del barbero. Va aparte porque hay que entrar con la contraseña primero.
# POR QUÉ SE REVISA TAMBIÉN: el 23/08/2026 la agenda del panel estaba caída con un
# error y esta comprobación decía "todo en orden", porque sólo miraba lo que ve el
# cliente. El barbero se enteró abriéndola él. La mitad de la app vive detrás del
# login: si no se mira, no está comprobada.
# Las páginas del panel, con el texto del botón que lleva a cada una. Se recorren
# PULSANDO EL MENÚ y no cambiando la dirección a mano: al cambiar la dirección el
# navegador recarga y Streamlit abre una sesión nueva, o sea que se pierde la clave y
# vuelve a salir el login. Por el menú se navega sin recargar, igual que el barbero.
BOTONES_PANEL = [
    ("Agenda", "panel: agenda"),
    ("Hoy", "panel: hoy"),
    ("Semana", "panel: semana"),
    ("Top", "panel: historial"),
    ("Volver", "panel: recordar"),
    ("Ajustes", "panel: ajustes"),
]


def _clave_del_panel() -> str | None:
    """La contraseña del barbero, leída del mismo archivo que usa la app. Si no está,
    el panel simplemente no se revisa (y se dice)."""
    archivo = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if not archivo.exists():
        return None
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        if linea.strip().startswith("admin_password"):
            return linea.split("=", 1)[1].strip().strip('"').strip("'")
    return None

# Lo que Streamlit escribe en la pantalla cuando la app se rompe o está dormida.
SENALES_DE_ERROR = [
    "has encountered an error",
    "error running app",
    "traceback",
    "page not found",
    "zzzz",
    "get this app back up",
]

# Algo de esto tiene que aparecer para dar la página por buena.
SENALES_DE_QUE_CARGO = ["esteban", "barber", "cita", "productos"]

# En el panel el nombre del negocio no siempre está a la vista.
SENALES_DEL_PANEL = SENALES_DE_QUE_CARGO + [
    "agenda", "hoy", "semana", "historial", "cortes", "ingresos",
    "servicio", "horario", "cerrar sesión", "disponibles",
]


def _consola_utf8():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")


def _marco_de_la_app(pagina):
    """El marco (iframe) donde Streamlit Cloud dibuja la app.

    Hace falta para PULSAR cosas: los botones no están en la página de fuera. Se
    reconoce porque es el único marco que tiene el contenedor de Streamlit dentro.
    """
    for m in pagina.frames:
        if "statuspage.io" in m.url:
            continue
        try:
            if m.locator("[data-testid='stAppViewContainer']").count():
                return m
        except Exception:
            continue
    return pagina.main_frame


def _texto_de_la_app(pagina) -> str:
    """Todo el texto que se ve, mirando también DENTRO de los marcos internos.

    Streamlit Cloud no dibuja la app en la página principal: la mete en un marco
    (iframe) aparte. Si se mira sólo la página de fuera se ve vacía y se da la app
    por caída aunque esté perfecta -- esta comprobación llegó a dar esa falsa alarma.
    """
    partes = []
    for marco in pagina.frames:
        # El marco de la página de estado de Streamlit no es parte de la app.
        if "statuspage.io" in marco.url:
            continue
        try:
            partes.append(marco.evaluate("document.body ? document.body.innerText : ''"))
        except Exception:
            continue
    return "\n".join(p for p in partes if p).lower()


def _juzgar(texto, etiqueta, senales_de_carga) -> bool:
    """Imprime el veredicto de una pantalla y dice si tiene problema."""
    if any(x in texto for x in SENALES_DE_ERROR):
        print(f"  ✖ {etiqueta:<18} carga pero muestra un error")
        return True
    if not any(x in texto for x in senales_de_carga):
        print(f"  ✖ {etiqueta:<18} quedó en blanco")
        return True
    print(f"  ✔ {etiqueta:<18} se ve bien")
    return False


def _revisar_el_panel(contexto) -> list[str]:
    """Entra al panel con la contraseña y recorre sus seis pantallas por el menú."""
    clave = _clave_del_panel()
    if not clave:
        print("  ⚠ panel              sin contraseña a mano: no se revisó")
        return []

    problemas = []
    pagina = contexto.new_page()
    try:
        pagina.goto(f"{URL_BASE}/admin", wait_until="domcontentloaded", timeout=60000)
        pagina.wait_for_timeout(12000)

        marco = _marco_de_la_app(pagina)
        if marco is None:
            print("  ✖ panel              no cargó la pantalla de entrar")
            return ["panel"]

        casilla = marco.locator("input[type=password]").first
        casilla.wait_for(timeout=30000)
        casilla.fill(clave)
        marco.get_by_role("button", name="Entrar").first.click()
        pagina.wait_for_timeout(9000)

        texto = _texto_de_la_app(pagina)
        if "contrase" in texto and "incorrecta" in texto:
            print("  ✖ panel              la contraseña no fue aceptada")
            return ["panel"]

        for boton, etiqueta in BOTONES_PANEL:
            try:
                marco = _marco_de_la_app(pagina)
                marco.get_by_role("button", name=boton, exact=False).first.click()
                pagina.wait_for_timeout(7000)
            except Exception as err:
                print(f"  ✖ {etiqueta:<18} no se pudo abrir ({type(err).__name__})")
                problemas.append(etiqueta)
                continue
            if _juzgar(_texto_de_la_app(pagina), etiqueta, SENALES_DEL_PANEL):
                problemas.append(etiqueta)
    except Exception as err:
        print(f"  ✖ panel              falló al revisarlo ({type(err).__name__})")
        problemas.append("panel")
    finally:
        pagina.close()
    return problemas


def _revisar_con_navegador() -> list[str] | None:
    """Devuelve la lista de páginas con problema, o None si no hay navegador."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    problemas = []
    with sync_playwright() as p:
        try:
            navegador = p.chromium.launch()
        except Exception:
            return None
        contexto = navegador.new_context()
        for ruta, etiqueta in RUTAS.items():
            pagina = contexto.new_page()
            try:
                pagina.goto(f"{URL_BASE}/{ruta}", wait_until="domcontentloaded", timeout=60000)
                # La app tarda en despertar si llevaba rato sin visitas.
                pagina.wait_for_timeout(12000)
                texto = _texto_de_la_app(pagina)
            except Exception as err:
                print(f"  ✖ {etiqueta:<12} no cargó ({type(err).__name__})")
                problemas.append(etiqueta)
                pagina.close()
                continue

            if any(s in texto for s in SENALES_DE_ERROR):
                print(f"  ✖ {etiqueta:<12} carga pero muestra un error")
                problemas.append(etiqueta)
            elif not any(s in texto for s in SENALES_DE_QUE_CARGO):
                print(f"  ✖ {etiqueta:<12} quedó en blanco")
                problemas.append(etiqueta)
            else:
                print(f"  ✔ {etiqueta:<12} se ve bien")
            pagina.close()

        print()
        print("  --- el panel del barbero ---")
        problemas += _revisar_el_panel(contexto)
        navegador.close()
    return problemas


def _revisar_sin_navegador() -> list[str]:
    """Sólo pregunta si el servidor responde. No ve si la app se rompió al dibujarse."""
    print("  (sin navegador instalado: sólo se comprueba que el servidor responda)")
    try:
        peticion = Request(
            f"{URL_BASE}/_stcore/health", headers={"User-Agent": "Mozilla/5.0"}
        )
        with urlopen(peticion, timeout=30) as respuesta:
            vivo = respuesta.status == 200
    except Exception as err:
        print(f"  ✖ el servidor no responde ({err})")
        return ["servidor"]

    if vivo:
        print("  ✔ el servidor responde")
        print("  ⚠ OJO: esto no garantiza que la app se vea bien, sólo que está encendida.")
        return []
    print("  ✖ el servidor respondió mal")
    return ["servidor"]


def main() -> int:
    _consola_utf8()
    print("=" * 66)
    print("  ¿ESTÁ FUNCIONANDO LA APP DE LA BARBERÍA?")
    print("=" * 66)
    print()

    problemas = _revisar_con_navegador()
    if problemas is None:
        problemas = _revisar_sin_navegador()

    print()
    if problemas:
        print("-" * 66)
        print("  LA APP TIENE PROBLEMAS.")
        print()
        print("  Qué hacer, en este orden:")
        print("   1. Entra a  https://share.streamlit.io")
        print("   2. Busca la app  esteban-barber  y ábrela.")
        print('   3. Abajo a la derecha: "Manage app" → menú (⋮) → "Reboot app".')
        print("   4. Espera 2 minutos y vuelve a correr esta comprobación.")
        print()
        print("  Si después de reiniciar sigue fallando, en esa misma pantalla")
        print("  salen los mensajes del servidor: cópialos y mándalos.")
        print("-" * 66)
        return 1

    print("  Todo en orden: un cliente puede pedir su cita y el panel abre bien.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
