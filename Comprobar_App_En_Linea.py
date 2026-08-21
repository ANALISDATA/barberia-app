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
from urllib.request import Request, urlopen

URL_BASE = "https://esteban-barber.streamlit.app"
RUTAS = {"": "portada", "cita": "pedir cita", "productos": "productos"}

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


def _consola_utf8():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")


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
                pagina.goto(f"{URL_BASE}/{ruta}", wait_until="networkidle", timeout=60000)
                # La app tarda en despertar si llevaba rato sin visitas.
                pagina.wait_for_timeout(9000)
                texto = pagina.inner_text("body").lower()
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

    print("  Todo en orden: un cliente puede entrar y pedir su cita.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
