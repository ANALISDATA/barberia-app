"""Clientes que llevan tiempo sin volver, para invitarlos por WhatsApp.

En módulo NUEVO, como manda la regla del proyecto (ver CLAUDE.md).

POR QUÉ NO SE ENVÍAN SOLOS, aunque sería lo cómodo: mandar WhatsApp de forma automática
exige la API oficial de WhatsApp Business (verificación del negocio ante Meta, un
proveedor intermediario y pago por mensaje). Las librerías gratis que lo simulan van
contra las reglas de WhatsApp y el riesgo real es que le bloqueen el número al barbero.
Además la app se duerme cuando nadie la usa, así que no habría quién dispare el envío.

Lo que sí se hace: preparar el mensaje y abrir WhatsApp con todo escrito. El barbero
sólo pulsa enviar. Cinco segundos por cliente, gratis y sin riesgo.

Quién entra en la lista, y por qué así:

  * Su última visita ATENDIDA fue hace `dias` o más. Se mira lo atendido, no lo
    reservado: alguien que pidió cita y no llegó no "vino" hace 15 días.
  * No tiene ninguna cita futura reservada. Sería absurdo invitar a volver a quien ya
    tiene cita para el jueves.
  * No se le escribió hace poco. Sin esto, la lista mostraría mañana a los mismos de
    hoy y acabaría mandándole el mismo mensaje tres veces a la misma persona -- que es
    justo la forma de que lo bloqueen.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from urllib.parse import quote

from app.db import NEGOCIO_ID, _cliente

DIAS_POR_DEFECTO = 15
DESCANSO_ENTRE_MENSAJES = 20  # días mínimos entre dos recordatorios a la misma persona


@dataclass(frozen=True)
class ClienteDormido:
    cliente_id: str
    nombre: str
    telefono: str
    ultima_visita: date
    veces: int
    ultimo_servicio: str
    ultimo_recordatorio: date | None

    def dias_sin_venir(self, hoy: date) -> int:
        return (hoy - self.ultima_visita).days


def hay_columna_recordatorio() -> bool:
    """Si ya se corrió la migración 005. Se pregunta antes de usarla para que la página
    avise del paso pendiente en vez de romperse."""
    try:
        _cliente().table("customers").select("ultimo_recordatorio").limit(1).execute()
        return True
    except Exception as err:
        texto = str(err).lower()
        if "ultimo_recordatorio" in texto:
            return False
        raise


def buscar(hoy: date, dias: int = DIAS_POR_DEFECTO) -> list[ClienteDormido]:
    """Los clientes a los que vale la pena escribirles, del más antiguo al más reciente."""
    campos = "id, name, phone"
    if hay_columna_recordatorio():
        campos += ", ultimo_recordatorio"

    clientes = (
        _cliente().table("customers").select(campos)
        .eq("business_id", NEGOCIO_ID).execute().data
    )
    if not clientes:
        return []

    citas = (
        _cliente()
        .table("appointments")
        .select("customer_id, date, status, service_type")
        .eq("business_id", NEGOCIO_ID)
        .execute()
        .data
    )

    ultima_visita: dict[str, date] = {}
    ultimo_servicio: dict[str, str] = {}
    veces: dict[str, int] = {}
    tiene_cita_futura: set[str] = set()

    for c in citas:
        cid = c["customer_id"]
        fecha = date.fromisoformat(c["date"])

        # Cualquier cita por venir que no esté cancelada cuenta como "ya va a volver".
        if fecha >= hoy and c["status"] in ("confirmada", "atendida"):
            tiene_cita_futura.add(cid)

        if c["status"] != "atendida":
            continue
        veces[cid] = veces.get(cid, 0) + 1
        if cid not in ultima_visita or fecha > ultima_visita[cid]:
            ultima_visita[cid] = fecha
            ultimo_servicio[cid] = c["service_type"]

    dormidos = []
    for cli in clientes:
        cid = cli["id"]
        if cid not in ultima_visita or cid in tiene_cita_futura:
            continue
        if (hoy - ultima_visita[cid]).days < dias:
            continue

        recordado = cli.get("ultimo_recordatorio")
        recordado = date.fromisoformat(recordado) if recordado else None

        # El descanso entre mensajes sólo cuenta si el mensaje se quedó SIN respuesta.
        # Si la persona vino después de que se le escribió, el mensaje cumplió y la
        # cuenta vuelve a cero. Sin esta condición, un cliente que se motila cada ocho
        # días desaparecía de la lista veinte días por haberle escrito una vez -- justo
        # al revés de lo que se busca.
        sin_respuesta = recordado is not None and recordado > ultima_visita[cid]
        if sin_respuesta and (hoy - recordado).days < DESCANSO_ENTRE_MENSAJES:
            continue

        dormidos.append(
            ClienteDormido(
                cliente_id=cid,
                nombre=cli.get("name") or "—",
                telefono=cli.get("phone") or "",
                ultima_visita=ultima_visita[cid],
                veces=veces.get(cid, 0),
                ultimo_servicio=ultimo_servicio.get(cid, ""),
                ultimo_recordatorio=recordado,
            )
        )

    return sorted(dormidos, key=lambda c: c.ultima_visita)


def marcar_escrito(cliente_id: str, hoy: date) -> None:
    if not hay_columna_recordatorio():
        return
    _cliente().table("customers").update(
        {"ultimo_recordatorio": hoy.isoformat()}
    ).eq("id", cliente_id).execute()


def mensaje(
    cliente: ClienteDormido,
    negocio: dict,
    enlace: str,
    horario: str = "",
    servicio: str = "",
) -> str:
    """El texto que se le manda.

    Se escribe como lo escribiría el barbero, no como lo escribiría un sistema: tutea,
    saluda por el nombre, menciona lo que suele pedir y se firma. Un mensaje que suena
    a robot se ignora; uno que suena a que el barbero se acordó de uno, no.

    Los emojis van al principio de cada línea a modo de viñeta -- así el mensaje se lee
    de un vistazo en la pantalla del celular, sin ser un bloque de texto corrido.
    """
    nombre_corto = cliente.nombre.split()[0].title() if cliente.nombre else ""
    saludo = f"¡Hola {nombre_corto}!" if nombre_corto else "¡Hola!"

    lineas = [f"{saludo} ✂️", ""]

    # Mencionar lo que suele pedir demuestra que se le recuerda. Sin el dato, se omite:
    # inventarse un servicio quedaría peor que no decir nada.
    if servicio:
        lineas.append(f"Ya va siendo hora de tu *{servicio.lower()}* 💈")
    else:
        lineas.append("Ya va siendo hora de tu corte 💈")

    lineas += [
        "Aparta tu cita cuando quieras, sin llamar y sin hacer fila.",
        "",
        "📅 *Elige el día y la hora que te sirva:*",
        enlace,
        "",
    ]

    if negocio.get("address"):
        lineas.append(f"📍 {negocio['address']}")
    if horario:
        lineas.append(f"🕐 {horario}")
    if negocio.get("phone"):
        lineas.append(f"📲 {negocio['phone']}")

    lineas += ["", "¡Te esperamos! 🔥", f"*{negocio.get('name', '')}*"]

    return "\n".join(lineas)


def url_whatsapp(cliente: ClienteDormido, texto: str) -> str:
    solo_digitos = "".join(c for c in cliente.telefono if c.isdigit())
    if not solo_digitos:
        return ""
    numero = solo_digitos if solo_digitos.startswith("57") else f"57{solo_digitos}"
    # api.whatsapp.com y NO wa.me: comprobado con el usuario en su celular, wa.me
    # entrega los emojis rotos (llegan como "?") mientras los acentos pasan bien.
    # api.whatsapp.com los respeta. Las dos son direcciones oficiales de WhatsApp.
    return f"https://api.whatsapp.com/send?phone={numero}&text={quote(texto)}"
