"""Configuración del negocio: horario, descansos, duración de la cita y precios.

Todo lo que antes había que cambiar entrando a Supabase se hace desde aquí.

Cada bloque guarda por separado (su propio botón) en vez de tener un único "Guardar"
al final: así se puede tocar el horario del martes sin miedo a arrastrar sin querer un
cambio a medio hacer en los precios.
"""
from datetime import time

import streamlit as st

from app import catalogo, db
from app.ui import menu, tema
from config import NOMBRES_DIA

# Duraciones ofrecidas. Se listan en vez de dejar un campo libre para que no se cuelen
# valores absurdos (0 minutos, 7 horas) que romperían la agenda sin explicación.
DURACIONES = [15, 20, 30, 40, 45, 50, 60, 75, 90]

HORAS = [time(h, m) for h in range(5, 24) for m in (0, 15, 30, 45)]


def _fmt(t: time) -> str:
    return t.strftime("%I:%M %p").lstrip("0").replace("AM", "a.m.").replace("PM", "p.m.")


def _pesos(valor: int) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def render():
    tema.aplicar()

    if not st.session_state.get("admin_autenticado"):
        st.warning("Entra al panel primero.")
        st.link_button("Ir al panel", "/admin", width="stretch")
        return

    if not db.disponible():
        st.warning("No hay conexión con Supabase.")
        return

    menu.pintar("configuracion")
    tema.saludo("Configuración", "Ajusta tu barbería a tu medida")

    _bloque_servicios()
    _bloque_productos()
    _bloque_horario()
    _bloque_negocio()

    tema.pie_de_pagina(db.obtener_negocio())


def _bloque_servicios():
    """Servicios: cada uno con su nombre, precio y DURACIÓN propia.

    Antes eran dos fijos ("sin barba" y "con barba") escritos en la base de datos. Ahora
    se pueden agregar los que sean -- solo barba, cejas, lo que se ofrezca -- y cada uno
    ocupa en la agenda el tiempo que de verdad toma.
    """
    tema.seccion("Servicios", eyebrow="Lo que ofreces", compacta=True)

    activos = catalogo.servicios(solo_activos=False)

    for s in activos:
        estado = "" if s["active"] else "  (apagado)"
        with st.expander(
            f'{s["name"]} — {_pesos(s["price"])} · {s.get("duration_minutes") or 45} min{estado}'
        ):
            _editor_servicio(s)

    with st.expander("＋ Agregar un servicio nuevo"):
        with st.form("nuevo_servicio"):
            nombre = st.text_input("Nombre", placeholder="Solo cejas, Solo barba, Cerquillo...")
            col_a, col_b = st.columns(2)
            precio = col_a.number_input("Precio", min_value=0, step=1000, value=15000)
            duracion = col_b.selectbox("Dura", DURACIONES, index=DURACIONES.index(15),
                                       format_func=lambda m: f"{m} minutos")
            crear = st.form_submit_button("Crear servicio", type="primary", width="stretch")

        if crear:
            if not nombre.strip():
                st.error("Ponle un nombre al servicio.")
            else:
                try:
                    catalogo.crear_servicio(nombre, int(precio), int(duracion))
                except catalogo.TipoRepetido:
                    st.error("Ya tienes un servicio con ese nombre.")
                except Exception as err:
                    st.error(
                        "No se pudo crear. Si es la primera vez, falta correr en "
                        "Supabase el archivo `supabase/003_servicios_y_productos.sql`."
                    )
                    st.caption(f"Detalle técnico: {err}")
                else:
                    st.success(f"Servicio «{nombre.strip()}» creado.")
                    st.rerun()


def _editor_servicio(s):
    with st.form(f"srv_{s['id']}"):
        nombre = st.text_input("Nombre", value=s["name"], key=f"sn_{s['id']}")
        col_a, col_b = st.columns(2)
        precio = col_a.number_input(
            "Precio", min_value=0, step=1000, value=int(s["price"]), key=f"sp_{s['id']}"
        )
        actual = s.get("duration_minutes") or 45
        duracion = col_b.selectbox(
            "Dura", DURACIONES,
            index=DURACIONES.index(actual) if actual in DURACIONES else DURACIONES.index(45),
            format_func=lambda m: f"{m} minutos", key=f"sd_{s['id']}",
        )
        guardar = st.form_submit_button("Guardar", type="primary", width="stretch")

    if guardar:
        catalogo.actualizar_servicio(s["id"], {
            "name": nombre.strip(), "price": int(precio),
            "duration_minutes": int(duracion),
        })
        st.success("Servicio actualizado.")
        st.rerun()

    if s["active"]:
        st.caption(
            "Apagarlo lo quita de la lista que ve el cliente. No se borra: las citas "
            "que ya se hicieron con él siguen contando en tus estadísticas."
        )
        if st.button("Apagar este servicio", key=f"off_{s['id']}", width="stretch"):
            if len([x for x in catalogo.servicios() if x["active"]]) <= 1:
                st.error("Tiene que quedar al menos un servicio encendido.")
            else:
                catalogo.desactivar_servicio(s["id"])
                st.rerun()
    else:
        if st.button("Volver a encenderlo", key=f"on_{s['id']}",
                     type="primary", width="stretch"):
            catalogo.activar_servicio(s["id"])
            st.rerun()


def _bloque_productos():
    tema.seccion("Productos", eyebrow="Lo que vendes", compacta=True)

    if not catalogo.hay_tabla_productos():
        st.info(
            "Para manejar los productos desde aquí falta un paso de una sola vez: "
            "correr en Supabase el archivo `supabase/003_servicios_y_productos.sql`."
        )
        return

    lista = catalogo.productos(solo_activos=False)
    if not lista:
        st.caption(
            "Todavía no hay productos en la base de datos. Mientras tanto, el catálogo "
            "público sigue mostrando los 6 que venían cargados en la app."
        )
        if st.button("Pasar esos 6 productos aquí para poder editarlos",
                     type="primary", width="stretch"):
            cuantos = _importar_productos_iniciales()
            st.success(f"{cuantos} producto(s) importados. Ya puedes editarlos.")
            st.rerun()

    for prod in lista:
        with st.expander(f'{prod["nombre"]} — {_pesos(prod["precio"])}'):
            _editor_producto(prod)

    with st.expander("＋ Agregar un producto nuevo"):
        with st.form("nuevo_producto"):
            nombre = st.text_input("Nombre", placeholder="Cera, tónico, shampoo...")
            precio = st.number_input("Precio", min_value=0, step=1000, value=30000)
            descripcion = st.text_area("Descripción", height=80,
                                       placeholder="Para qué sirve, qué efecto tiene...")
            foto = st.file_uploader("Foto", type=["jpg", "jpeg", "png", "webp"])
            crear = st.form_submit_button("Crear producto", type="primary", width="stretch")

        if crear:
            if not nombre.strip():
                st.error("Ponle un nombre al producto.")
            else:
                imagen = catalogo.preparar_imagen(foto) if foto else None
                catalogo.crear_producto(nombre, int(precio), descripcion, imagen)
                st.success(f"Producto «{nombre.strip()}» creado.")
                st.rerun()


def _importar_productos_iniciales() -> int:
    """Pasa a la base de datos los productos que venían escritos en el código, con sus
    fotos. Se hace una sola vez y con un botón, no automático: escribir datos sin que
    nadie lo pida siempre acaba en sorpresas."""
    import base64
    from pathlib import Path

    from app.productos import PRODUCTOS

    importados = 0
    for p in PRODUCTOS:
        ruta = Path("assets/productos") / p["imagen"]
        imagen = None
        if ruta.exists():
            imagen = base64.b64encode(ruta.read_bytes()).decode()
        catalogo.crear_producto(p["nombre"], p["precio"], p["descripcion"], imagen)
        importados += 1
    return importados


def _editor_producto(prod):
    if prod.get("imagen_base64"):
        st.image(f"data:image/jpeg;base64,{prod['imagen_base64']}", width=140)

    with st.form(f"prod_{prod['id']}"):
        nombre = st.text_input("Nombre", value=prod["nombre"], key=f"pn_{prod['id']}")
        precio = st.number_input("Precio", min_value=0, step=1000,
                                 value=int(prod["precio"]), key=f"pp_{prod['id']}")
        descripcion = st.text_area("Descripción", value=prod.get("descripcion") or "",
                                   height=80, key=f"pd_{prod['id']}")
        foto = st.file_uploader("Cambiar la foto", type=["jpg", "jpeg", "png", "webp"],
                                key=f"pf_{prod['id']}")
        guardar = st.form_submit_button("Guardar", type="primary", width="stretch")

    if guardar:
        datos = {
            "nombre": nombre.strip(), "precio": int(precio),
            "descripcion": descripcion.strip(),
        }
        # Sólo se toca la foto si subieron una nueva: si no, se conserva la que había.
        if foto:
            datos["imagen_base64"] = catalogo.preparar_imagen(foto)
        catalogo.actualizar_producto(prod["id"], datos)
        st.success("Producto actualizado.")
        st.rerun()

    if st.button("Borrar este producto", key=f"del_{prod['id']}", width="stretch"):
        catalogo.borrar_producto(prod["id"])
        st.rerun()


def _bloque_horario():
    tema.seccion("Horario y descansos", eyebrow="Día por día", compacta=True)

    horario = db.obtener_horario_semanal()
    descansos = db.obtener_descansos()

    for dia in range(7):
        abierto = horario.get(dia) is not None
        inicio, fin = horario.get(dia) or (time(7, 0), time(20, 0))
        lista_descansos = descansos.get(dia, [])

        resumen = (
            f"{_fmt(inicio)} – {_fmt(fin)}"
            + (f" · {len(lista_descansos)} descanso(s)" if lista_descansos else "")
            if abierto
            else "Cerrado"
        )
        with st.expander(f"{NOMBRES_DIA[dia]} — {resumen}"):
            _editor_dia(dia, abierto, inicio, fin, lista_descansos)


def _editor_dia(dia, abierto, inicio, fin, lista_descansos):
    activo = st.toggle("Abierto este día", value=abierto, key=f"abre_{dia}")

    col_a, col_b = st.columns(2)
    nuevo_inicio = col_a.selectbox(
        "Abre a las", HORAS, index=HORAS.index(inicio) if inicio in HORAS else 8,
        format_func=_fmt, key=f"ini_{dia}", disabled=not activo,
    )
    nuevo_fin = col_b.selectbox(
        "Cierra a las", HORAS, index=HORAS.index(fin) if fin in HORAS else 60,
        format_func=_fmt, key=f"fin_{dia}", disabled=not activo,
    )

    st.markdown("**Descansos**")
    st.caption("Almuerzo, una vuelta, lo que necesites. Puedes poner varios.")

    # Cuántas filas de descanso mostrar. Vive en session_state para que el botón
    # "Agregar descanso" pueda añadir una fila sin perder lo ya escrito.
    clave_n = f"n_desc_{dia}"
    if clave_n not in st.session_state:
        st.session_state[clave_n] = max(len(lista_descansos), 1)

    nuevos_descansos = []
    for i in range(st.session_state[clave_n]):
        actual = lista_descansos[i] if i < len(lista_descansos) else None
        c1, c2 = st.columns(2)
        d_ini = c1.selectbox(
            f"Desde ({i + 1})", [None] + HORAS,
            index=(HORAS.index(actual[0]) + 1) if actual else 0,
            format_func=lambda t: "—" if t is None else _fmt(t),
            key=f"di_{dia}_{i}", disabled=not activo,
        )
        d_fin = c2.selectbox(
            f"Hasta ({i + 1})", [None] + HORAS,
            index=(HORAS.index(actual[1]) + 1) if actual else 0,
            format_func=lambda t: "—" if t is None else _fmt(t),
            key=f"df_{dia}_{i}", disabled=not activo,
        )
        if d_ini and d_fin:
            nuevos_descansos.append((d_ini, d_fin))

    if st.button("＋ Agregar otro descanso", key=f"add_{dia}", width="stretch"):
        st.session_state[clave_n] += 1
        st.rerun()

    if st.button(f"Guardar {NOMBRES_DIA[dia].lower()}", type="primary",
                 key=f"save_{dia}", width="stretch"):
        if activo and nuevo_inicio >= nuevo_fin:
            st.error("La hora de cierre tiene que ser posterior a la de apertura.")
            return
        for d_ini, d_fin in nuevos_descansos:
            if d_ini >= d_fin:
                st.error(f"El descanso {_fmt(d_ini)} – {_fmt(d_fin)} está al revés.")
                return
            if activo and (d_ini < nuevo_inicio or d_fin > nuevo_fin):
                st.error(
                    f"El descanso {_fmt(d_ini)} – {_fmt(d_fin)} se sale del horario "
                    "de ese día."
                )
                return

        db.guardar_horario_dia(dia, nuevo_inicio, nuevo_fin, activo)
        db.guardar_descansos_dia(dia, nuevos_descansos)
        st.session_state.pop(clave_n, None)
        st.success(f"{NOMBRES_DIA[dia]} actualizado.")
        st.rerun()


def _bloque_negocio():
    tema.seccion("Datos del negocio", eyebrow="Lo que ve el cliente", compacta=True)

    negocio = db.obtener_negocio()
    nombre = st.text_input("Nombre", value=negocio.get("name") or "")
    descripcion = st.text_area(
        "Frase de la portada", value=negocio.get("description") or "", height=80
    )
    direccion = st.text_input("Dirección", value=negocio.get("address") or "")
    st.caption("La dirección es la que abre Waze, escríbela como la buscarías ahí.")
    telefono = st.text_input("Teléfono / WhatsApp", value=negocio.get("phone") or "")

    col_a, col_b = st.columns(2)
    llegar = col_a.number_input(
        "Llegar antes (minutos)", min_value=0, max_value=60,
        value=int(negocio.get("arrive_minutes_before") or 10),
    )
    cancelar = col_b.number_input(
        "Cancelar con (horas)", min_value=0, max_value=48,
        value=int(negocio.get("cancellation_hours") or 3),
    )

    if st.button("Guardar datos", type="primary", width="stretch"):
        db.guardar_datos_negocio({
            "name": nombre.strip(),
            "description": descripcion.strip(),
            "address": direccion.strip(),
            "phone": telefono.strip(),
            "arrive_minutes_before": int(llegar),
            "cancellation_hours": int(cancelar),
        })
        st.success("Datos actualizados.")
        st.rerun()


render()
