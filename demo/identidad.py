"""
Quién entra en la consola: usuario, contraseña y el puesto que hay detrás.

Por qué esto no es «autenticación»
-----------------------------------
Esta pieza **no autentica a nadie** y no pretende hacerlo. Es la puerta de la
demostración: convierte el desplegable de roles —que se entendía como un menú
de la demo— en el gesto con el que se entra a cualquier aplicación de empresa.
Lo que importa no es el candado, es lo que ocurre **después** de pasarlo: que
la pantalla siguiente ya sabe quién eres, de qué área eres y qué te deja hacer
la ontología, sin que tú se lo hayas dicho.

En un despliegue real esto lo sustituye el directorio de la empresa (LDAP,
Entra ID, lo que use GraphyCems). La contraseña vive en una variable de
entorno, es la misma para todos los usuarios de la demostración y está a la
vista en la pantalla de entrada: esconderla daría la impresión contraria a la
verdadera. Nada de lo que hay aquí debe presentarse como un control de acceso.

Aquí no hay personas: hay puestos
----------------------------------
El usuario **es el puesto** —`ingeniero.jefe`, `encargado.turno`,
`dir.comercial`— y no el nombre de nadie. No es una decisión estética:

· La autoridad la lleva el puesto, no la persona. Un sistema que enseñara
  «Carlos Ruiz puede proponer» estaría diciendo algo que la matriz de Pablo no
  dice en ninguna parte; lo que dice es que los Encargados de Turno pueden.
· Los nombres que aparecían antes salían de la ficha de puesto de Pablo, y ésa
  es documentación interna de GraphyCems. Una demostración que se va a enseñar
  fuera no tiene por qué llevarlos.
· Al quitarlos desaparecen también los nombres inventados que hacían falta para
  rellenar las áreas sin ficha. Ahora los nueve usuarios salen del mismo sitio:
  la matriz.

El único nombre propio que queda en la aplicación está **dentro del HTML de
Pablo**, que se sirve tal cual y se abre aparte.

Un hallazgo que conviene no tapar
----------------------------------
La ficha de Pablo incluye un puesto de **Mantenimiento de Planta**, que
«reporta a Dirección y da servicio transversal a ambos turnos». En la matriz de
autoridad —los ocho roles de `referencia/ontologia_autoridad.json`— **no hay
ninguna fila que le corresponda**: ni es Encargado de Turno ni es Director. Con
la ontología en la mano no puede ni proponer ni validar sobre nada, y eso no es
una decisión del sistema: es un hueco de la matriz. Se deja entrar para que el
hueco se vea, porque taparlo sería inventarse autoridad que nadie ha firmado.
"""

import os
import unicodedata
from pathlib import Path

from nucleo import autoridad

# La contraseña de la demostración. Igual para todos y a la vista: ver arriba.
CLAVE = os.environ.get("CLAVE_DEMO", "graphycems")

# Las categorías sobre las que se pregunta «¿puede?». Son las que emite el
# módulo de Mencía y las que reparte la matriz de Pablo.
CATEGORIAS = ("produccion", "comercial", "financiera")

# La carpeta que Streamlit sirve como páginas sueltas (ver `.streamlit/config.toml`).
# El organigrama vive aquí y NO dentro de `referencia/` porque no se lee desde
# Python: se abre en el navegador, en su propia pestaña.
# El organigrama vive en `static/` por costumbre —es un fichero suelto que no
# forma parte del código— pero Python lo LEE de ahí: no se sirve como estático.
# Ver `url_organigrama()`.
RUTA_ESTATICOS = Path(__file__).resolve().parent.parent / "static"

# El puesto, en primera persona y en una frase. No sale de la matriz —la matriz
# dice sobre qué se manda, no qué se hace— así que se declara redactado.
COMETIDO = {
    "CEO / Dirección General":
        "Decidir cuando el conflicto cruza áreas y ninguna de ellas puede "
        "cerrarlo sola.",
    "IT / Tecnología":
        "Sostener el sistema. No decide sobre pedidos: decide sobre la "
        "infraestructura que los procesa.",
    "Dir. Producción":
        "Responder de la planta: qué se fabrica, en qué orden y para cuándo. "
        "Cierra las incidencias de producción que los encargados le suben.",
    "Encargados de Turno":
        "Sacar el turno adelante y revisar lo que no cuadra antes de que entre "
        "en máquina. Propone la corrección y la justifica; no la cierra.",
    # Literal de la ficha de Pablo. Se copia en vez de redactarlo porque es el
    # único puesto del que la matriz no dice nada, y conviene que lo poco que
    # se sabe de él venga de su autor y no de mí.
    "Mantenimiento de Planta":
        "Mantener la planta. Reporta a Dirección y da servicio transversal a "
        "ambos turnos.",
    "Dir. Comercial":
        "Responder de lo pactado con el cliente: oferta, condiciones y cuenta.",
    "Admin. Comerciales":
        "Meter y mantener los pedidos de cliente. Es quien primero ve que un "
        "pedido y su orden no dicen lo mismo.",
    "Dir. Financiera":
        "Responder del presupuesto y de las cuentas del pedido.",
    "Admin. Financieros":
        "Facturar y llevar la contabilidad diaria de lo que sale de planta.",
}

# usuario → puesto. `rol` tiene que coincidir **literalmente** con un rol de
# la matriz de Pablo; si no coincide, el sistema lo dirá en vez de adivinarlo.
#
# `puesto` es cómo se llama el puesto en la casa y `rol` es la fila de la matriz
# que lo gobierna. Son dos cosas y a veces no se llaman igual: «Ingeniero Jefe»
# es el título del puesto en la ficha de Pablo, y la autoridad le viene de la
# fila «Dir. Producción».
PLANTILLA = [
    {"usuario": "dir.jefe", "puesto": "Dirección General",
     "rol": "CEO / Dirección General", "perfil": None},
    {"usuario": "it.tecnologia", "puesto": "IT y Tecnología",
     "rol": "IT / Tecnología", "perfil": None},
    {"usuario": "ingeniero.jefe", "puesto": "Ingeniero Jefe",
     "rol": "Dir. Producción", "perfil": "organigrama.html"},
    {"usuario": "encargado.turno", "puesto": "Encargado de Turno",
     "rol": "Encargados de Turno", "perfil": "organigrama.html"},
    {"usuario": "mantenimiento.planta", "puesto": "Mantenimiento de Planta",
     "rol": "Mantenimiento de Planta", "perfil": "organigrama.html"},
    {"usuario": "dir.comercial", "puesto": "Dirección Comercial",
     "rol": "Dir. Comercial", "perfil": None},
    {"usuario": "admin.comercial", "puesto": "Administración Comercial",
     "rol": "Admin. Comerciales", "perfil": None},
    {"usuario": "dir.financiera", "puesto": "Dirección Financiera",
     "rol": "Dir. Financiera", "perfil": None},
    {"usuario": "admin.financiero", "puesto": "Administración Financiera",
     "rol": "Admin. Financieros", "perfil": None},
]



def _plano(s):
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


def usuarios():
    """La plantilla, para poder enseñar con qué se entra."""
    return list(PLANTILLA)


def persona(usuario):
    """El puesto detrás de un nombre de usuario, o `None`."""
    u = _plano(usuario)
    return next((p for p in PLANTILLA if _plano(p["usuario"]) == u), None)


def entrar(usuario, clave):
    """
    (puesto, motivo). El puesto es `None` cuando no se entra.

    El motivo no distingue entre «no existe» y «contraseña mal»: es la única
    costumbre de una puerta de verdad que sí merece la pena copiar aquí.
    """
    if not str(usuario or "").strip() or not str(clave or ""):
        return None, "Escribe usuario y contraseña."
    p = persona(usuario)
    if not p or str(clave) != CLAVE:
        return None, "Usuario o contraseña incorrectos."
    return p, f'Sesión iniciada como {p["puesto"]}.'


def permisos(rol, onto=None):
    """
    Lo que ese puesto puede y lo que no, **preguntándoselo a la ontología**.

    Nada de esto está escrito a mano: por cada área se le pregunta a
    `autoridad.puede()` si el rol puede proponer y si puede validar, y la
    respuesta se coloca en una de las tres listas. La tercera —`no_consta`— es
    la que no se puede quitar: un rol que la ontología no reconoce no es un rol
    sin permisos, es un rol del que no se sabe nada, y son dos cosas distintas.
    """
    onto = onto or autoridad.cargar()
    puede, no_puede, no_consta = [], [], []
    for cat in CATEGORIAS:
        area = autoridad.area_de(cat) or cat
        for accion in autoridad.ACCIONES:
            v, motivo = autoridad.puede(rol, cat, accion, onto)
            fila = {"categoria": cat, "area": area, "accion": accion,
                    "motivo": motivo,
                    "frase": (f'{"Proponer" if accion == "proponer" else "Validar y cerrar"} '
                              f'correcciones sobre contradicciones de {area}')}
            (puede if v is True else no_puede if v is False else no_consta).append(fila)
    return {"puede": puede, "no_puede": no_puede, "no_consta": no_consta}


def ficha(usuario, onto=None):
    """
    Todo lo que la pantalla del puesto necesita, en un solo objeto.

    Devuelve `None` si el usuario no existe. Si existe pero su rol no está en
    la matriz, la ficha se devuelve igual con `rol_en_la_matriz` a False: el
    sistema enseña el hueco en vez de rellenarlo.
    """
    p = persona(usuario)
    if not p:
        return None
    onto = onto or autoridad.cargar()
    r = autoridad.rol_de(p["rol"], onto) if onto else None
    perm = permisos(p["rol"], onto)
    return {
        **p,
        "rol_en_la_matriz": bool(r),
        "tiene_organigrama": bool(p.get("perfil")),
        "nivel": r["nivel"] if r else None,
        "area": r["area"] if r else None,
        "tipo_de_autoridad": r["tipo_de_autoridad"] if r else None,
        "manda_sobre": r["manda_sobre"] if r else None,
        "cometido": COMETIDO.get(p["rol"]),
        "permisos": perm,
        "tiene_perfil": bool(perfil_html(usuario)),
    }


def url_organigrama(usuario):
    """
    La dirección donde se abre el organigrama de ese puesto. `None` si no hay.

    Es una dirección de la PROPIA aplicación —`?vista=organigrama`— y no un
    fichero estático. La diferencia se descubrió desplegando: servido desde
    `static/` funcionaba en local y en Streamlit Cloud abría una pestaña en
    blanco, porque cuando la ruta no corresponde a ningún fichero Streamlit
    entrega el armazón de la aplicación y el armazón no encuentra sus recursos.
    Una vista de la aplicación no depende de ninguna configuración del servidor
    ni de que una carpeta haya llegado al repositorio.

    Y es una URL, no un trozo de HTML incrustado, porque dentro de la consola
    quedaba un `iframe` con scroll propio dentro del scroll de la página: en una
    demostración proyectada eso no se lee. Abierto en su pestaña se mira entero
    y la consola sigue donde estaba al volver.
    """
    p = persona(usuario)
    if not p or not p.get("perfil"):
        return None
    return f'?vista=organigrama&puesto={p["usuario"]}'


def perfil_html(usuario):
    """
    El HTML del organigrama, tal cual lo entregó Pablo. `None` si no hay.

    Se sirve sin tocar una coma: es documentación de otro, y reescribirla para
    que encaje con la estética de la consola sería exactamente lo que este
    proyecto le reprocha a los módulos que evalúa. La aplicación no lo lee para
    pintarlo —de eso se encarga el navegador—; esta función existe para poder
    comprobar en las pruebas que el fichero está donde se dice.
    """
    p = persona(usuario)
    if not p or not p.get("perfil"):
        return None
    ruta = RUTA_ESTATICOS / p["perfil"]
    if not ruta.is_file():
        return None
    return ruta.read_text(encoding="utf-8")
