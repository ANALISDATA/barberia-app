"""Catálogo de productos que vende la barbería.

PARA CAMBIAR PRECIOS, NOMBRES O DESCRIPCIONES: se edita esta lista y ya. No hay que
tocar nada más ni entrar a Supabase.

Las fotos viven en `assets/productos/`. Si se agrega un producto nuevo, se pone su foto
ahí con el mismo nombre que se escriba en `imagen`.

Los datos salen del catálogo real de WhatsApp del negocio; las descripciones se
completaron con lo que dice el empaque de cada producto.
"""

PRODUCTOS = [
    {
        "nombre": "Cera en polvo AGIVA",
        "precio": 37000,
        "imagen": "agiva-polvo.jpg",
        "descripcion": (
            "Efecto matte (seco), buena fijación y aroma. Ideal para cabellos "
            "delgados: le da volumen al cabello."
        ),
    },
    {
        "nombre": "Cera Inmortal azul",
        "precio": 30000,
        "imagen": "inmortal-azul.jpg",
        "descripcion": "Cera en crema. Brillo y fijación flexible fuerte.",
    },
    {
        "nombre": "Cera Inmortal amarilla",
        "precio": 30000,
        "imagen": "inmortal-amarilla.jpg",
        "descripcion": "Pomada con brillo y fijación fuerte.",
    },
    {
        "nombre": "Cera Inmortal verde",
        "precio": 30000,
        "imagen": "inmortal-verde.jpg",
        "descripcion": "Efecto matte, acabado seco y fijación fuerte.",
    },
    {
        "nombre": "Cera Inmortal roja",
        "precio": 30000,
        "imagen": "inmortal-roja.jpg",
        "descripcion": "Efecto brillante y fijación fuerte.",
    },
    {
        "nombre": "Minoxigrow",
        "precio": 40000,
        "imagen": "minoxigrow.jpg",
        "descripcion": (
            "Tónico para el crecimiento del cabello. Minoxidil 5% con biotina, "
            "frasco de 60 ml para un mes de tratamiento."
        ),
    },
]
