"""
Bloque de Evaluación y Calidad — TFG Íñigo Daza.

Esta capa sólo elige qué rama se ejecuta y pinta lo que devuelve. Toda la
evaluación vive en `nucleo/` y `modulos/`: la app es un selector.

Tres pantallas, y la primera es de otra clase que las otras dos:

  · Demo              — cómo funcionaría la APLICACIÓN: entran documentos por un
                        lado y sale por el otro una decisión con autor y rastro
  · Evaluar un módulo — este BLOQUE haciendo su trabajo: baterías, métricas,
                        severidad, veredicto e informe
  · Esquema           — por dónde circula un dato y qué hace cada módulo

La separación es deliberada. La demo enseña el producto que el equipo
construiría con las cinco piezas juntas; la evaluación enseña qué se sostiene
hoy con datos reales. Mezclarlas produciría una demostración bonita que no
distingue lo que funciona de lo que se ha ensayado, que es exactamente lo que
este proyecto le reprocha a los módulos que evalúa.
"""

import html
import json
import tempfile
import time
from datetime import date

import pandas as pd
import streamlit as st

# Las tres carpetas del proyecto, antes que nada.
#
# `import esquema` era la primera línea que tocaba `modulos`, así que cuando la
# subida a GitHub se dejaba una carpeta por el camino el traceback señalaba a
# `esquema.py` —un fichero que no tiene ninguna culpa— y no decía en ningún
# sitio la única palabra que importa: **falta una carpeta**.
#
# Importarlas aquí, a mano y una a una, cuesta cuatro líneas y convierte un
# `ModuleNotFoundError` en una frase que se puede leer y arreglar. Es la misma
# idea que la comprobación de piezas de más abajo, sólo que ésta tiene que ir
# antes: si la carpeta no está, no hay piezas que comprobar.
_CARPETAS = {
    "nucleo": "el núcleo común: lectura de PDF, contraste, veredicto",
    "modulos": "una rama por módulo evaluado",
    "demo": "el recorrido de demostración y los documentos de ejemplo",
}
_sin_subir = []
for _paquete, _para_que in _CARPETAS.items():
    try:
        __import__(_paquete)
    except ModuleNotFoundError:
        _sin_subir.append((_paquete, _para_que))

if _sin_subir:
    st.error("**Falta una carpeta entera del proyecto en el repositorio.** No es "
             "un error de código: la subida a GitHub se ha dejado carpetas por el "
             "camino, que es el fallo más frecuente de este despliegue.")
    for _paquete, _para_que in _sin_subir:
        st.markdown(f"- **`{_paquete}/`** — {_para_que}")
    st.info("Una carpeta sólo existe en GitHub si contiene ficheros, y el "
            "formulario web no sube carpetas si eliges los ficheros con el "
            "explorador: hay que **arrastrarlas**. La forma que no falla es "
            "GitHub Desktop, y está explicada paso a paso en `DESPLIEGUE.md`. "
            "Comprueba también que dentro de cada carpeta esté su `__init__.py`: "
            "sin él, la carpeta está pero el paquete no.")
    st.stop()

import esquema
import modulos
import ui
from demo import caso, consola, flujo, guion, naturaleza, sesion
from modulos import auditoria, contradicciones, similitud, vigencia
from nucleo import VERSION
from nucleo import asesor, autoridad, clasificacion, historial, llm, memoria, plantilla
from nucleo import bateria as B_NUCLEO
from nucleo import pdf as P
from nucleo import veredicto as V

st.set_page_config(page_title="Evaluación y Calidad — TFG", layout="wide",
                   page_icon="◍", initial_sidebar_state="expanded")
ui.inyectar_estilo()

VERSION_REQUERIDA = 12

# Comprobación de coherencia al arrancar.
#
# Existe porque el fallo más frecuente de este proyecto no es un error de lógica:
# es subir a GitHub la mitad de los ficheros. Cuando `app.py` es nuevo y `ui.py`
# es viejo, Python revienta con un AttributeError críptico en mitad de un flujo,
# y el traceback señala la línea que llama, no el fichero que falta.
#
# Cada pieza declara qué necesita de las demás. Si algo no está, la app lo dice
# con el nombre del fichero que hay que subir, y no se ejecuta a medias.
#
# El 29/08 esta comprobación dejó pasar exactamente el fallo que existe para
# evitar. `ui.tabla_documentos` seguía existiendo en el fichero viejo —el
# `hasattr` decía que sí— pero admitía tres argumentos y `app.py` le pasaba
# cuatro. La app arrancó tan contenta y reventó al abrir el módulo de Martín.
# Desde entonces una pieza puede pedir además un **parámetro**, con la sintaxis
# `funcion:parametro`: comprobar que algo existe no es comprobar que encaja.
PIEZAS = [
    ("ui.py", ui, ["VERSION_UI", "bloque_evolucion", "bloque_asesor",
                   "bloque_severidad",
                   "bloque_procedencia", "barra_bateria", "medidor",
                   "franja_sistema", "franja_cifras", "fila_medidores",
                   "diagnostico_modelos", "selector_modo_lectura",
                   "tabla_documentos:extraer", "panel_contradicciones",
                   "panel_cambios", "linea_del_hilo", "cabecera_fase",
                   "lecturas_de_campo", "mapa_organizativo",
                   "sesion_iniciada", "cadena_de_custodia", "barra_pasos",
                   "bandeja", "aviso_incidencia", "enfrentar",
                   "rejilla_herramientas", "consulta_pedido", "recibo",
                   "barra_consola", "tarjeta_alarma", "naturaleza",
                   "ficha_sesion", "evidencia_enfrentada",
                   "registro_criterio",
                   "contexto_del_operario", "precedente",
                   "panel_memoria"]),
    ("nucleo/bateria.py", B_NUCLEO, ["SEVERIDADES", "ORDEN_SEVERIDAD"]),
    ("nucleo/plantilla.py", plantilla, ["filas", "a_markdown", "severidad_de"]),
    ("nucleo/asesor.py", asesor, ["aconsejar", "verificar_anclaje"]),
    ("nucleo/historial.py", historial, ["comparar", "instantanea", "registrar"]),
    ("nucleo/llm.py", llm, ["conformar", "modelo_en_uso", "listar_modelos"]),
    ("modulos/similitud.py", similitud, ["cargar_contribuciones",
                                         "reproducir_ranking", "PESOS_DECLARADOS"]),
    ("modulos/vigencia.py", vigencia, ["conciliar_ids", "PRORROGAS",
                                       "SALIDA_IALERT_CRED", "SALIDA_IALERT_TODAS", "familia_de",
                                       "descartar_incoherentes", "FAMILIAS"]),
    ("demo/caso.py", caso, ["observar", "gobernar", "decidir", "comprobar",
                            "numero_de_pedido", "LECTURAS_DE_CAMPO", "REGLA"]),
    ("demo/sesion.py", sesion, ["entrar", "resumen", "nueva",
                                "PROPUESTA", "VALIDADA"]),
    ("demo/naturaleza.py", naturaleza, ["PANTALLAS", "capas_de",
                                        "resumen", "ACTUA"]),
    ("demo/consola.py", consola, ["arrancar", "lotes", "contexto_operario",
                                  "acciones_para", "actuar",
                                  "analisis_incongruencias",
                                  "analisis_diligencia",
                                  "analisis_similitud", "ANALISIS",
                                  "diagnostico", "fragmento_de",
                                  "contexto_del_caso"]),
    ("nucleo/memoria.py", memoria, ["registrar", "precedentes",
                                    "sugerencia", "resumen",
                                    "olvidar", "clase_de",
                                    "aplica_a",
                                    "registrar:justificacion"]),
    ("demo/flujo.py", flujo, ["procesar", "primera_incidencia",
                              "encaminar", "impacto", "agrupar",
                              "PASOS", "HERRAMIENTAS"]),
    ("nucleo/autoridad.py", autoridad,
     ["tiene_autoridad", "quien_manda_sobre", "cargar", "confirmada",
      "categorias_confirmadas", "puede", "pertenece_al_area", "area_de"]),
    ("modulos/contradicciones.py · cadena", contradicciones,
     ["comparar_estados", "evaluar:estado_previo"]),
    ("nucleo/clasificacion.py", clasificacion,
     ["anotar_tipos", "tipo_de", "resumen"]),
    ("nucleo/llm.py · PDF y tipos", llm, ["leer_pdf",
                                          "clasificar_con_llm"]),
    ("nucleo/pdf.py", P, ["hay_ocr", "texto_ocr", "integridad",
                          "idiomas_ocr"]),
    ("nucleo/llm.py · anclaje", llm, ["anclar", "fragmento_presente"]),
]

def _falta(modulo, pieza):
    """
    ¿Le falta a este módulo la pieza que se le pide?

    `nombre` pregunta por existencia. `nombre:parametro` pregunta además por la
    firma: que la función admita ese argumento. Lo segundo es lo que distingue
    un fichero viejo que casualmente tiene el mismo nombre de función de un
    fichero al día.
    """
    nombre, _, parametro = pieza.partition(":")
    objeto = getattr(modulo, nombre, None)
    if objeto is None:
        return True
    if not parametro:
        return False
    try:
        import inspect
        return parametro not in inspect.signature(objeto).parameters
    except (TypeError, ValueError):
        return False


_faltan = []
for _fichero, _modulo, _piezas in PIEZAS:
    _ausentes = [x for x in _piezas if _falta(_modulo, x)]
    if _ausentes:
        _faltan.append((_fichero, _ausentes))

# El número propio de `ui.py`, que es el fichero que más cambia y el que más
# veces se ha quedado atrás al subirlo.
if getattr(ui, "VERSION_UI", 0) < 12:
    _faltan.append(("ui.py", [f"es la versión {getattr(ui, 'VERSION_UI', 'antigua')} "
                              f"y se necesita la 12"]))

if VERSION < VERSION_REQUERIDA or _faltan:
    st.error("**El repositorio está a medio subir.** Hay ficheros de versiones "
             "distintas conviviendo, y eso produce errores que parecen de código "
             "pero son de despliegue.")
    if VERSION < VERSION_REQUERIDA:
        st.markdown(f"- `nucleo/__init__.py` está en la versión **{VERSION}** y se "
                    f"necesita la **{VERSION_REQUERIDA}**")
    for _fichero, _ausentes in _faltan:
        st.markdown(f"- **`{_fichero}`** es de una versión anterior: le faltan "
                    f"`{'`, `'.join(_ausentes)}`")
    st.info("Sube el repositorio **completo**, no ficheros sueltos. En GitHub: "
            "borra las carpetas `nucleo/`, `modulos/` y `demo/` y vuelve a "
            "subirlas enteras, junto con `app.py`, `ui.py` y `esquema.py`.")
    st.stop()

def secreto(clave, defecto=None):
    """
    `st.secrets` no devuelve None cuando falta el fichero de secretos: levanta
    excepción y se lleva por delante la app entera. En local, sin
    `secrets.toml`, eso significa que no arranca. Aquí la ausencia de clave es
    una situación normal —el sistema funciona en determinista— así que no puede
    ser un error fatal.
    """
    try:
        return st.secrets.get(clave, defecto)
    except Exception:
        return defecto


# La clave vive en Settings → Secrets de la app, nunca en el repositorio. Si no
# está, no pasa nada: el sistema entero funciona en modo determinista y lo dice.
llm.configurar(api_key=secreto("GEMINI_API_KEY"), modelo=secreto("GEMINI_MODELO"))

if not P.hay_pdftotext():
    st.error("No se encuentra `pdftotext`. En Streamlit Cloud, añade un fichero "
             "`packages.txt` con la línea `poppler-utils` y vuelve a desplegar.")
    st.stop()

# El OCR no para la app —hay ramas que no leen documentos— pero sí condiciona por
# completo la de Martín: sus trece documentos reales son fotocopias y ninguno
# tiene capa de texto. Sin OCR, el veredicto correcto sobre todos ellos es «no se
# ha podido comprobar», que es honesto y no sirve para nada. Se avisa arriba y
# con el nombre del paquete que falta, porque el mensaje que sale abajo —«sin
# capa de texto extraíble»— describe el síntoma y no la causa.
SIN_OCR = not P.hay_ocr()
if SIN_OCR:
    st.warning(
        "**No hay OCR en este despliegue, y sin él los documentos escaneados no "
        "se pueden leer.** Los trece documentos reales de Martín son fotocopias "
        "sin capa de texto: sobre ellos el evaluador sólo podrá decir «no se ha "
        "podido comprobar».\n\n"
        "· **En Streamlit Cloud** — `packages.txt` tiene que contener "
        "`poppler-utils`, `tesseract-ocr` y `tesseract-ocr-spa`. Los paquetes de "
        "sistema **sólo se instalan al reconstruir el contenedor**: después de "
        "subirlo hay que ir a *Manage app → Reboot app*, no basta con que se "
        "vuelva a desplegar el código.\n"
        "· **En local** — `sudo apt install tesseract-ocr tesseract-ocr-spa "
        "poppler-utils`.")
elif "spa" not in P.idiomas_ocr():
    st.warning("El OCR está disponible pero **sin el idioma español** "
               "(`tesseract-ocr-spa`). Funcionará en inglés: reconoce las cifras "
               "y las fechas, pero come tildes y eñes, y eso hace fallar citas "
               "que son buenas.")


# ===========================================================================
# Navegación
# ===========================================================================

# Tres pantallas, no cinco. «El hilo» y «Demo» eran la misma cosa contada dos
# veces —una con un texto escrito a mano y otra módulo a módulo— y ninguna de las
# dos dejaba meter un caso y verlo recorrer el sistema. Ahora es una sola y se
# ejecuta con los documentos que le pongas delante.
PANTALLAS = ["Consola", "Evaluar un módulo", "Esquema del sistema"]

with st.sidebar:
    st.markdown('<div class="eyebrow">TFG · Íñigo Daza</div>'
                '<div style="font-size:1.15rem;font-weight:650;line-height:1.25;'
                'margin-bottom:1rem">Evaluación y Calidad</div>',
                unsafe_allow_html=True)
    pantalla = st.radio("Pantalla", PANTALLAS, label_visibility="collapsed")
    st.markdown("---")
    operativas = len(modulos.operativas())
    st.markdown(
        f'<div style="font-size:.8rem;color:var(--tinta-2);line-height:1.7">'
        f'<b>{operativas}</b> de <b>{len(modulos.RAMAS)}</b> módulos evaluables<br>'
        f'<b>{len(modulos.con_bateria())}</b> con batería diseñada<br>'
        f'<span style="color:var(--tinta-3)">núcleo v{VERSION}</span></div>',
        unsafe_allow_html=True)
    st.markdown("---")
    _ocr_ok = P.hay_ocr()
    _idiomas = P.idiomas_ocr()
    st.markdown(
        f'<div style="font-size:.8rem;color:var(--tinta-2);line-height:1.7">'
        f'<b>Lectura de documentos</b><br>'
        f'{"✓" if P.hay_pdftotext() else "✗"} pdftotext'
        f'<br>{"✓" if _ocr_ok else "✗"} OCR (tesseract)'
        f'<br>{"✓" if "spa" in _idiomas else "✗"} idioma español'
        f'</div>', unsafe_allow_html=True)
    if not _ocr_ok:
        st.caption("Sin OCR no se leen escaneos. Sube el `.ocr.txt` junto al PDF, "
                   "o instala `tesseract-ocr` y reinicia la app.")
    st.markdown("---")
    ui.panel_ia()
    ui.diagnostico_modelos()


# ===========================================================================
# Pantalla: esquema del sistema
# ===========================================================================

def pantalla_esquema():
    st.markdown('<div class="hero"><div class="eyebrow">Arquitectura</div>'
                '<h1>Esquema del sistema</h1>'
                '<div class="meta">Qué hace cada módulo y por dónde circula un dato '
                'hasta el veredicto</div></div>', unsafe_allow_html=True)
    ui.franja_sistema(modulos.fichas(), modulos.ESTADOS_CONEXION)
    st.markdown(f'<div class="esquema">{esquema.dibujar()}</div>',
                unsafe_allow_html=True)
    ui.nota("El dibujo se genera desde el registro de módulos: si mañana añado una "
            "rama, aparece aquí sola. <b>Probada</b> significa que un dato real ha "
            "recorrido el sistema de extremo a extremo, no que yo haya mirado los "
            "datos a mano — y quien la prueba es siempre quien la consume, no quien "
            "la produce.", acento=True)


# ===========================================================================
# Pantalla: demo
# ===========================================================================

ICONO = {"ejecutado": ("p-bien", "✓", "Ejecutado"),
         "a_medias": ("p-acento", "◐", "A medias"),
         "no_operativo": ("p-espera", "◌", "No operativo")}


def _miles(x):
    """
    3000 → «3.000». Las cantidades de una tirada se leen con separador.

    Ojo con el punto: aquí llegan dos cosas distintas. De los documentos llegan
    cadenas donde el punto son los miles («30.000») y del cálculo del impacto
    llegan números donde el punto es el decimal (27000.0). Quitar los puntos a
    ciegas convertía 27000.0 en 270.000 — un cero de más contando ceros de más,
    que es la errata más embarazosa posible en esta pantalla.
    """
    if isinstance(x, (int, float)):
        return f"{int(round(x)):,}".replace(",", ".")
    try:
        return f"{int(float(str(x).replace('.', '').replace(',', '.'))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(x)


def _consola_docs():
    """La bandeja: la de ejemplo, o la que se suba."""
    # En la barra lateral, no en la pantalla: de dónde salen los documentos es
    # configuración, y en un producto la configuración no ocupa el primer sitio
    # que ve el operario.
    with st.sidebar:
        st.markdown("---")
        st.markdown("**Origen de los documentos**")
        fuente = st.radio(
            "Origen", ["Bandeja de ejemplo", "Subir los míos"],
            horizontal=True, label_visibility="collapsed", key="consola_fuente")
        if fuente == "Bandeja de ejemplo":
            st.caption("Tres pedidos y un contrato marco, inventados de "
                       "principio a fin y marcados como tales. Uno de los "
                       "pedidos cuadra y dos no, y los dos que no llevan el "
                       "mismo error: es lo que permite ver la memoria "
                       "funcionando.")
            docs = guion.documentos_de("ejemplo")
            if not docs:
                st.error("No hay documentos de ejemplo. Genéralos con "
                         "`python demo/generar_ejemplo.py`.")
                st.stop()
            return docs

        subidos = st.file_uploader(
            "Documentos en PDF", type=["pdf", "txt"],
            accept_multiple_files=True, key="consola_up")
        if not subidos:
            st.info("Sube órdenes de fabricación, documentación de cliente y, "
                    "si los hay, contratos. El sistema los reparte solo.")
            st.stop()
        firmas = tuple((f.name, hash(f.getvalue())) for f in subidos)
        memo = st.session_state.setdefault("_consola_leidos", {})
        if firmas not in memo:
            with st.spinner("Leyendo…"):
                with tempfile.TemporaryDirectory() as tmp:
                    memo.clear()
                    memo[firmas] = P.leer_subidos(subidos, tmp, ocr=P.hay_ocr())
        return [d for d in memo[firmas] if not d.get("huerfano")]


def _herramientas(alarma, estado):
    """Las tres herramientas de análisis del esquema, cada una haciendo algo."""
    st.markdown("#### Herramientas de análisis")
    st.caption("Las del equipo, disponibles sobre esta alarma. Cada una responde "
               "una pregunta distinta, y la que no puede responder lo dice.")

    a1, a2, a3 = consola.ANALISIS

    # 1 · Incongruencias — la herramienta que le corresponde a esta alarma.
    #     Es la pantalla 5 del guion: evidencia y diagnóstico.
    with st.expander(f"{a1['nombre']} — {a1['pregunta']}", expanded=True):
        st.caption(a1["modulo"])
        ui.naturaleza(naturaleza.capas_de("evidencia"))

        diag = consola.diagnostico(alarma)
        ui.evidencia_enfrentada(diag["apoyan_cliente"], diag["apoyan_orden"])
        pastilla = ("p-mal" if diag["clave"] == "error_probable" else
                    "p-espera" if diag["clave"] != "cambio_documentado"
                    else "p-acento")
        st.markdown(
            ui.pastilla(diag["etiqueta"], pastilla, "◆")
            + f'&nbsp;&nbsp;<span style="font-size:.87rem;color:var(--tinta-2)">'
              f'{html.escape(diag["por_que"])}</span>', unsafe_allow_html=True)
        st.caption(f'Y en cualquier caso: {diag["y_ademas"][1]}')

        if len(alarma["discrepancias"]) > 1:
            st.markdown("**Las demás diferencias del mismo pedido**")
            st.dataframe(pd.DataFrame([{
                "Campo": d["etiqueta"],
                "Dice el cliente": _miles(d["valor_cliente"]),
                "Dice la orden": _miles(d["valor_orden"]),
                "Gravedad si se propaga": d["severidad_esperada"],
            } for d in alarma["discrepancias"]
                if d is not alarma["principal"]]), use_container_width=True,
                hide_index=True)

        st.markdown("**Contraste con la salida del módulo**")
        st.caption("La salida del módulo se le entrega al sistema; no se va a "
                   "buscar. Es la frontera declarada de este trabajo.")
        if "consola_respuesta" not in st.session_state:
            st.session_state.consola_respuesta = ""
        c1, c2 = st.columns([1, 3])
        if c1.button("Cargar la salida del módulo", use_container_width=True,
                     key="consola_ej"):
            st.session_state.consola_respuesta = auditoria.EJEMPLO
        c2.caption("Carga la respuesta real que el módulo de Juan emitió sobre "
                   "un pedido con esta misma pareja de discrepancias.")
        resp = st.text_area("Salida", key="consola_respuesta", height=120,
                            label_visibility="collapsed")
        an = consola.analisis_incongruencias(alarma, resp)
        for av in an["avisos"]:
            st.warning(av)
        if an["hay_salida"]:
            obs = an["observacion"]
            ui.fila_kpis([
                ui.kpi("Reporta el módulo", str(len(an["reportados"])),
                       "incidencias"),
                ui.kpi("Confirmadas", f'{len(obs["vistas"])}/'
                       f'{len(obs["discrepancias"])}',
                       "por la lectura propia del sistema", acento=True),
                ui.kpi("Sin sostener", str(len(obs["inventadas"])),
                       "no aparecen en los documentos"),
            ])
            if not obs["no_vistas"] and not obs["inventadas"]:
                st.success("El sistema ha leído los documentos por su cuenta y "
                           "confirma, una a una, las incidencias del módulo. "
                           "**Nadie tiene que fiarse: se comprueba.**")

    # 2 · Diligencia — el contrato del cliente.
    with st.expander(f"{a2['nombre']} — {a2['pregunta']}"):
        st.caption(a2["modulo"])
        dil = consola.analisis_diligencia(estado["contratos"], date.today())
        if not dil["aplica"]:
            ui.nota(dil["motivo"], tono="espera")
        else:
            for d in dil["documentos"]:
                tono = "p-bien" if d["estado"] == "vigente" else "p-mal"
                st.markdown(
                    ui.pastilla(d["etiqueta"], tono,
                                "✓" if d["estado"] == "vigente" else "✕")
                    + f'&nbsp;&nbsp;<b>{html.escape(d["nombre"])}</b>',
                    unsafe_allow_html=True)
                ui.fila_kpis([
                    ui.kpi("En vigor desde",
                           d["inicio"].strftime("%d/%m/%Y") if d["inicio"] else "—",
                           "según el propio documento"),
                    ui.kpi("Hasta",
                           d["fin"].strftime("%d/%m/%Y") if d["fin"] else "—",
                           f'quedan {d["dias"]} días' if d["dias"] is not None
                           else "sin plazo declarado", acento=True),
                    ui.kpi("Preaviso",
                           f'{d["preaviso"]} días' if d["preaviso"] else "—",
                           "para denunciar el contrato"),
                ])
                if d["preaviso_urgente"]:
                    st.error("**La ventana de preaviso se está cerrando.** Si se "
                             "quiere denunciar el contrato hay que hacerlo ya.")
                st.caption(d["por_que"])

    # 3 · Similitud — y aquí el sistema dice que no puede.
    with st.expander(f"{a3['nombre']} — {a3['pregunta']}"):
        st.caption(a3["modulo"])
        sim = consola.analisis_similitud()
        ui.nota(sim["motivo"], tono="espera")
        if sim.get("ejemplo"):
            st.caption(f'Consulta del módulo: {sim["ejemplo"]["consulta"]} · '
                       f'{sim["ejemplo"]["descartados"]} candidatas descartadas '
                       f'antes de puntuar.')
            st.dataframe(pd.DataFrame([{
                "Posición": r["posicion"], "Proyecto": r["id_proyecto"],
                "Puntuación": round(r["puntuacion"], 3),
            } for r in sim["ejemplo"]["resultados"]]),
                use_container_width=True, hide_index=True)


def pantalla_consola():
    """
    La aplicación: un sistema que ya está funcionando y un operario que llega.

    Por qué no es un recorrido de pantallas
    ----------------------------------------
    La versión anterior era un asistente de seis pasos con su barra de progreso.
    Se entendía, pero se entendía como una demostración. Lo que hay que enseñar
    es un producto, y la diferencia práctica es quién manda: en un asistente
    manda el guion, y en un producto manda lo que está ocurriendo.

    Aquí el sistema ya ha leído la documentación que había, ha contrastado cada
    pedido consigo mismo y tiene una cola de alarmas abiertas antes de que nadie
    abra la pantalla. El operario no arranca nada: se pone al mando.

    Las cuatro partes del esquema
    ------------------------------
    · flujo continuo — la barra de arriba y la cola de alarmas
    · herramientas   — tres análisis sobre la alarma que se esté atendiendo
    · ontología      — quién eres y qué te deja hacer ESTA alarma
    · aprendizaje    — lo ya decidido vuelve como precedente
    """
    docs = _consola_docs()
    docs, avisos = clasificacion.anotar_tipos(
        docs, auditoria.clasificar, auditoria.TIPOS, "determinista",
        permiso=llm.permiso_de(auditoria.FICHA))

    # El sistema procesa lo que ha ENTRADO, no todo lo que haya en la carpeta.
    # La diferencia importa para que la demo se entienda: si la alarma ya está
    # ahí al abrir, no se ve de dónde sale.
    todos_lotes = consola.lotes(docs)
    recibidos = st.session_state.setdefault("consola_recibidos", set())
    entrados = [d for lote, ds in todos_lotes.items() if lote in recibidos
                for d in ds]
    estado = consola.arrancar(entrados, auditoria.clasificar)
    resueltas = st.session_state.setdefault("consola_resueltas", set())
    abiertas = [a for a in estado["alarmas"] if a["etiqueta"] not in resueltas]

    onto = autoridad.cargar()
    todos = (onto or {}).get("roles", [])
    # De más bajo a más alto. El operario que abre la consola en una empresa no
    # suele ser el director general, y además así el primer intento enseña el
    # escalón que hay que enseñar.
    roles = [r["rol"] for r in sorted(todos, key=lambda r: -r["nivel"])]
    operario = st.session_state.get("consola_rol") or (roles[0] if roles else None)

    # ------------------------------------------------- 1 · ENTRADA DEL USUARIO
    #
    # La pantalla 1 del guion de Fabián. Va antes que nada porque su comprensión
    # es «la aplicación sabe quién soy y qué puedo hacer», y eso no se puede
    # enseñar después de haber visto ya media aplicación.
    if not st.session_state.get("consola_dentro"):
        st.markdown(
            '<div class="hero"><div class="eyebrow">GraphyCems · entrada</div>'
            '<h1>Identifícate para entrar en la consola</h1>'
            '<div class="meta">La identidad, el rol y los permisos no se '
            'infieren: se leen de la ontología de la empresa, y de ellos '
            'depende qué vas a poder hacer con lo que encuentres.</div></div>',
            unsafe_allow_html=True)
        ui.naturaleza(naturaleza.capas_de("sesion"))
        if not roles:
            st.error("No hay organigrama cargado: sin él no se puede saber quién "
                     "es nadie ni qué puede hacer.")
            st.stop()
        elegido = st.selectbox(
            "Entra como", roles, key="consola_rol",
            format_func=lambda n: next(
                f'{r["rol"]} — nivel {r["nivel"]}, {r["area"]}'
                for r in todos if r["rol"] == n))
        ficha = next(r for r in todos if r["rol"] == elegido)
        ui.ficha_sesion(
            ficha["rol"], f'{ficha["nivel"]} · {ficha["tipo_de_autoridad"]}',
            ficha["area"], "GraphyCems", ficha["manda_sobre"],
            (f'{memoria.resumen()["decisiones"]} decisiones registradas en el '
             f'sistema') if memoria.resumen()["decisiones"] else
            "sin actividad registrada todavía")
        st.button("Entrar", type="primary", key="consola_entrar",
                  on_click=lambda: st.session_state.update(consola_dentro=True))
        return

    # --------------------------------------------- 2 · RECEPCIÓN Y PROCESAMIENTO
    #
    # La pantalla 2 del guion, y la que faltaba para que la demo se creyera. Una
    # alarma que ya está ahí cuando abres la aplicación no enseña de dónde sale;
    # hay que ver entrar los documentos y ver al sistema pararse en uno.
    #
    # Se puede volver aquí en cualquier momento y meter más: eso es lo que hace
    # que parezca un sistema en marcha y no un guion. En la demostración vale la
    # pena guardarse un lote para el final y verlo levantar una alarma en vivo.
    pendientes = {k: v for k, v in todos_lotes.items() if k not in recibidos}

    if st.session_state.get("consola_pantalla") == "recepcion" or not recibidos:
        st.markdown(
            '<div class="hero"><div class="eyebrow">GraphyCems · recepción</div>'
            '<h1>Entrada de documentación</h1>'
            '<div class="meta">Así es como entra el trabajo: por tandas, según '
            'la manda el cliente o la genera producción. El sistema las lee, '
            'agrupa por pedido y contrasta cada grupo consigo mismo.</div></div>',
            unsafe_allow_html=True)
        ui.naturaleza(naturaleza.capas_de("procesamiento"))

        if recibidos:
            st.caption(f'Ya procesados: {", ".join(sorted(recibidos))}. '
                       f'{estado["pedidos"]} pedido(s) analizados, '
                       f'{len(abiertas)} alarma(s) abierta(s).')

        if not pendientes:
            st.success("No queda documentación por recibir. Todo lo que había "
                       "en la bandeja está procesado.")
            st.button("Ir a la consola", type="primary", key="rec_ir",
                      on_click=lambda: st.session_state.update(
                          consola_pantalla="consola"))
            return

        st.markdown("**Tandas en espera**")
        elegidos = []
        for lote, ds in pendientes.items():
            etiqueta = (f'{lote} — {len(ds)} documento(s)'
                        if lote != "expediente" else
                        f'{lote} — contrato marco del cliente')
            if st.checkbox(etiqueta, value=True, key=f"rec_{lote}"):
                elegidos.append(lote)
        st.caption("Puedes dejar alguna sin recibir y meterla después: la "
                   "alarma saltará entonces, delante de quien esté mirando.")

        if not st.button("Recibir y procesar", type="primary", key="rec_procesar"):
            if recibidos:
                st.button("Volver a la consola", key="rec_volver",
                          on_click=lambda: st.session_state.update(
                              consola_pantalla="consola"))
            return
        if not elegidos:
            st.warning("Marca al menos una tanda.")
            return

        # Se pintan de una en una, con una pausa corta. No es adorno: lo que hay
        # que ver es que el sistema **va leyendo** y que se para en un sitio
        # concreto. Una tabla que aparece entera cuenta el resultado, no el
        # trabajo.
        nuevas = 0
        hueco = st.empty()
        pintado = []
        for lote in elegidos:
            del_lote = todos_lotes[lote]
            paso = consola.arrancar(del_lote, auditoria.clasificar)
            for r in paso["resultados"]:
                pintado.append((lote, r))
            if paso["contratos"]:
                pintado.append((lote, {
                    "etiqueta": "Documentación contractual",
                    "estado": "contrato",
                    "documentos": [{"nombre": c["doc"]["nombre"],
                                    "tipo": "contrato"}
                                   for c in paso["contratos"]],
                }))
            nuevas += len(paso["alarmas"])

            with hueco.container():
                for _l, r in pintado:
                    filas = [{
                        "nombre": d["nombre"], "tipo": d["tipo"],
                        "estado": "leído",
                        "dispara": r["estado"] == "incidencia"
                        and d["tipo"] == "orden",
                    } for d in r["documentos"]]
                    ui.recibo(f'Tanda {_l} · {r.get("etiqueta", "")}', filas,
                              estado=r["estado"])
                    if r["estado"] == "limpio":
                        st.success(f'{r["etiqueta"]}: los documentos dicen lo '
                                   f'mismo. Sin incidencias.')
                    elif r["estado"] == "incidencia":
                        p_ = r["discrepancias"][0]
                        st.error(f'**Posible incongruencia · {r["etiqueta"]}** — '
                                 f'{p_["etiqueta"]}: '
                                 f'{_miles(p_["valor_cliente"])} contra '
                                 f'{_miles(p_["valor_orden"])}. '
                                 f'{len(r["discrepancias"])} diferencia(s) en '
                                 f'total.')
                    elif r["estado"] == "contrato":
                        ui.nota("Documentación contractual: no pertenece a "
                                "ningún pedido. Queda en el expediente del "
                                "cliente y la usa la herramienta de "
                                "diligencia.", tono="espera")
                    else:
                        ui.nota(f'{r["etiqueta"]}: no se puede contrastar '
                                f'todavía. {r.get("motivo", "")}', tono="espera")
            time.sleep(0.5)

        st.session_state.consola_recibidos = recibidos | set(elegidos)
        st.session_state.consola_pantalla = "consola"
        if nuevas:
            st.button(f'Atender {nuevas} alarma(s)', type="primary",
                      key="rec_alarmas")
        else:
            st.button("Ir a la consola", type="primary", key="rec_sin")
        return

    ui.barra_consola(
        "GraphyCems · Consola de control",
        f'En marcha · {estado["documentos"]} documentos leídos',
        operario)

    mem = memoria.resumen()
    ui.franja_cifras([
        (estado["pedidos"], "pedidos analizados"),
        (len(estado["limpios"]) + len(resueltas), "despachados"),
        (len(abiertas), "alarmas abiertas"),
        (mem["decisiones"], "decisiones en memoria"),
    ])

    # Se puede volver a recepción en cualquier momento. Es lo que convierte la
    # demo en un sistema: metes otra tanda y la alarma salta delante de quien
    # está mirando, en vez de haber estado ahí desde el principio.
    if pendientes:
        c_rec, _ = st.columns([2, 3])
        if c_rec.button(f'Entra más documentación ({len(pendientes)} tanda(s) '
                        f'en espera)', use_container_width=True,
                        key="ir_recepcion"):
            st.session_state.consola_pantalla = "recepcion"
            st.rerun()
    for a in avisos:
        st.info(a)

    # Una alarma recién cerrada NO desaparece de la pantalla: se queda enseñando
    # cómo quedó, con su rastro, hasta que el operario vuelve a la cola. Si se
    # cerrara sola se perdería justo el momento que hay que ver — el pedido
    # respondiendo ya con el valor decidido.
    activa = st.session_state.get("consola_alarma")
    if activa and activa not in [a["etiqueta"] for a in estado["alarmas"]]:
        activa = st.session_state.consola_alarma = None

    # ------------------------------------------------------------- LA COLA
    if not activa:
        # El marcador del guion: «4 correctos · 1 incidencia». Dice de un
        # vistazo que el sistema no avisa de todo lo que mira.
        st.markdown(
            f'**{len(estado["limpios"]) + len(resueltas)} correctos · '
            f'{len(abiertas)} incidencia(s)** — el sistema ha contrastado los '
            f'{estado["pedidos"]} pedidos que había en la bandeja.')
        ui.naturaleza(naturaleza.capas_de("vigilancia"))
        st.markdown("### Alarmas abiertas")
        if not abiertas:
            st.success("No queda ninguna alarma abierta. El sistema sigue "
                       "leyendo lo que entre.")
        for a in abiertas:
            p = a["principal"]
            imp = flujo.impacto(p)
            ui.tarjeta_alarma(
                p.get("severidad_esperada", "—").upper(),
                f'Pedido {a["etiqueta"]} · {a["n"]} documentos',
                f'{p["etiqueta"]}: el cliente pide {_miles(p["valor_cliente"])} '
                f'y la orden manda fabricar {_miles(p["valor_orden"])}',
                (f'**{_miles(imp["exceso"])} unidades de más**, '
                 f'{imp["veces"]:g} veces lo pedido.' if imp else "")
                + (f' Y {len(a["discrepancias"]) - 1} diferencia(s) menor(es) '
                   f'en el mismo pedido.' if len(a["discrepancias"]) > 1 else ""))
            if st.button(f'Atender la alarma del pedido {a["etiqueta"]}',
                         key=f'atender_{a["etiqueta"]}', type="primary"):
                st.session_state.consola_alarma = a["etiqueta"]
                st.rerun()

        if estado["limpios"]:
            with st.expander(f'Despachados sin incidencias '
                             f'({len(estado["limpios"])})'):
                st.caption("El sistema los ha contrastado y no ha encontrado "
                           "nada. No han molestado a nadie, y ésa es la mitad "
                           "del trabajo que hace.")
                for r in estado["limpios"]:
                    st.markdown(f'- **Pedido {r["etiqueta"]}** — '
                                f'{r["n"]} documentos, todos coinciden.')
        if estado["incompletos"]:
            with st.expander(f'Sin poder contrastar '
                             f'({len(estado["incompletos"])})'):
                for r in estado["incompletos"]:
                    ui.nota(f'<b>{r["etiqueta"]}</b> — {r["motivo"]}',
                            tono="espera")

        st.markdown("### Memoria del sistema")
        st.caption("Lo que se ha ido decidiendo. No hay ningún modelo "
                   "entrenado: hay precedente, que es lo que se puede abrir, "
                   "leer y discutir.")
        ui.panel_memoria(mem)
        if mem["decisiones"]:
            if st.button("Olvidar todo (para repetir la demostración)",
                         key="consola_olvidar"):
                memoria.olvidar()
                st.session_state.consola_resueltas = set()
                st.rerun()
        return

    # -------------------------------------------- EL DASHBOARD DE LA ALARMA
    alarma = next(a for a in estado["alarmas"] if a["etiqueta"] == activa)
    resultado = st.session_state.get(f'resultado_{alarma["etiqueta"]}')
    ya_cerrada = alarma["etiqueta"] in resueltas
    principal = alarma["principal"]
    imp = flujo.impacto(principal)

    if st.button("← Volver a la cola", key="consola_volver"):
        st.session_state.consola_alarma = None
        st.rerun()

    ui.naturaleza(naturaleza.capas_de("panel"), pie=False)
    ui.aviso_incidencia(
        f'Pedido {alarma["etiqueta"]}: la orden manda fabricar '
        f'{_miles(principal["valor_orden"])} de los '
        f'{_miles(principal["valor_cliente"])} que pidió el cliente'
        if imp else f'Pedido {alarma["etiqueta"]}: {principal["etiqueta"]}',
        "Nadie ha pedido que se revise este pedido. El sistema lo encontró al "
        "contrastar la orden de fabricación con la documentación de cliente, "
        "mientras despachaba el resto de la bandeja sin molestar a nadie.")

    ui.enfrentar(
        {"que": "Pidió el cliente", "valor": _miles(principal["valor_cliente"]),
         "fuente": next((d["nombre"] for d in alarma["documentos"]
                         if d["tipo"] == "pedido_cliente"), "")},
        {"que": "Iba a fabricarse", "valor": _miles(principal["valor_orden"]),
         "fuente": next((d["nombre"] for d in alarma["documentos"]
                         if d["tipo"] == "orden"), "")})

    if imp:
        with st.expander("Ponerle precio (opcional)"):
            st.caption("El sistema no se inventa el coste. Si quieres verlo en "
                       "euros, escribe tú el coste unitario.")
            cu = st.number_input("Coste unitario (€)", min_value=0.0, step=0.10,
                                 value=0.0, key="consola_coste")
            if cu:
                st.metric("Coste de fabricar lo que nadie pidió",
                          f'{flujo.impacto(principal, cu)["coste"]:,.2f} €'
                          .replace(",", "."))

    # --- Ontología: quién eres y qué te deja hacer esta alarma -------------
    st.markdown("#### Quién está al mando")
    ui.naturaleza(naturaleza.capas_de("autoridad"))
    c1, c2 = st.columns([2, 1])
    rol = c1.selectbox(
        "Operario", roles, key="consola_rol",
        index=roles.index(operario) if operario in roles else 0,
        label_visibility="collapsed")
    with c2.popover("Ver el organigrama", use_container_width=True):
        st.caption("La ontología de la empresa. De aquí sale si tu puesto puede "
                   "cerrar esta alarma o sólo proponer.")
        ui.mapa_organizativo(onto, "consola",
                             consola.categoria_de(alarma), autoridad)

    ctx = consola.contexto_operario(rol, alarma, onto)
    ui.contexto_del_operario(ctx)

    # --- Aprendizaje: ¿esto ya ha pasado? ---------------------------------
    sug = memoria.sugerencia(principal,
                             contexto=consola.contexto_del_caso(alarma),
                             excepto=alarma["etiqueta"])
    if sug:
        ui.precedente(sug)
        if sug.get("descartados"):
            st.caption(f'{len(sug["descartados"])} caso(s) parecido(s) '
                       f'descartado(s): {sug["descartados"][0].get("descartado_porque", "")}.')

    _herramientas(alarma, estado)

    # --- Actuación --------------------------------------------------------
    if ya_cerrada:
        r = resultado or {}
        st.markdown("#### Cierre, memoria y aprendizaje")
        ui.naturaleza(naturaleza.capas_de("memoria"))
        st.success(r.get("mensaje", "Alarma cerrada."))
        ui.consulta_pedido(
            f'{principal["etiqueta"]} · pedido {alarma["etiqueta"]}',
            _miles(r.get("valor", principal["valor_cliente"])),
            "El pedido ya responde con el valor decidido y no vuelve a mostrar "
            "el conflicto. Lo que se guarda no es sólo el número: es **quién lo "
            "decidió y con qué autoridad**.",
            ["Detectada por el sistema al contrastar la orden con la "
             "documentación de cliente."]
            + ([f'Revisada antes por **{r["propuesta_por"]}**, que está en el '
                f'área pero no manda sobre ella.']
               if r.get("propuesta_por") else [])
            + [f'Cerrada por **{r.get("cerrada_por", ctx["rol"])}**, con '
               f'autoridad declarada sobre {ctx["area_afectada"]}.',
               'Registrada en la memoria: la próxima alarma de esta clase '
               'llegará con este precedente puesto.'])

        if r.get("registro"):
            st.markdown("**El criterio que queda guardado**")
            st.caption("Dos mitades, y las dos hacen falta. La izquierda permite "
                       "auditar la decisión dentro de seis meses; la derecha "
                       "permite saber si el criterio **aplica** a un caso nuevo. "
                       "Un precedente sin condiciones es una regla disfrazada.")
            ui.registro_criterio(r["registro"])

        st.button("← Volver a la cola", key="consola_volver_pie",
                  type="primary",
                  on_click=lambda: st.session_state.update(consola_alarma=None))
        return

    st.markdown("#### Actuación")
    ui.naturaleza(naturaleza.capas_de("decision"))
    posibles = consola.acciones_para(ctx)
    st.caption("Sólo aparecen las acciones que tu puesto permite. Un botón que "
               "no se puede pulsar no se enseña apagado: se sustituye por el que "
               "sí corresponde.")

    propuesta = st.session_state.get(f'propuesta_{alarma["etiqueta"]}')
    if propuesta:
        just_previa = st.session_state.get(f'just_{alarma["etiqueta"]}')
        ui.nota(f'<b>Ya revisada por {html.escape(propuesta)}</b>, pendiente de '
                f'validación. Es el aviso que salta en el módulo de Mencía '
                f'cuando entra alguien con autoridad.'
                + (f'<br>Lo justificó así: «{html.escape(just_previa)}»'
                   if just_previa else ""), tono="espera")

    # La justificación no es un campo más: es lo que convierte una decisión en un
    # criterio reutilizable. Sin ella, dentro de seis meses queda un número y
    # nadie sabe por qué. Fabián lo dice explícito en la pantalla 7 —«el
    # encargado propone y justifica»— y el sistema no registra sin ella.
    justificacion = st.text_area(
        "Por qué decides esto", height=80,
        key=f'entrada_just_{alarma["etiqueta"]}',
        placeholder="El pedido y el presupuesto coinciden en 3.000; la orden "
                    "lleva un cero de más.")
    if sug and sug.get("ultimo", {}).get("justificacion"):
        st.caption(f'La vez anterior se justificó así: '
                   f'«{sug["ultimo"]["justificacion"]}»')

    valor = None
    if "corregir" in posibles:
        with st.expander("Corregir con otro valor"):
            valor = st.text_input(
                f'{principal["etiqueta"]} correcta', key="consola_valor",
                placeholder=str(principal["valor_cliente"]))

    cols = st.columns(len(posibles))
    for col, acc in zip(cols, posibles):
        etiqueta, _ = consola.ACCIONES[acc]
        if col.button(etiqueta, key=f'acc_{acc}', use_container_width=True,
                      type="primary" if acc == "aceptar" else "secondary"):
            r = consola.actuar(alarma, acc, ctx, valor, propuesta,
                               justificacion=justificacion)
            r["cerrada_por"] = ctx["rol"]
            st.session_state[f'resultado_{alarma["etiqueta"]}'] = r
            if r["cerrada"]:
                st.session_state.consola_resueltas = resueltas | {alarma["etiqueta"]}
            elif r.get("propuesta_por"):
                st.session_state[f'propuesta_{alarma["etiqueta"]}'] = r["propuesta_por"]
                st.session_state[f'just_{alarma["etiqueta"]}'] = r.get("justificacion")
            st.rerun()

    r = st.session_state.get(f'resultado_{alarma["etiqueta"]}')
    if r and not r["cerrada"]:
        if r.get("falta_justificacion"):
            st.error(f'**No se ha registrado nada.** {r["mensaje"]}')
        else:
            ui.nota(r["mensaje"], tono="espera")


# ===========================================================================
# Pantalla: evaluar un módulo
# ===========================================================================

def rejilla_modulos():
    st.markdown('<div class="hero"><div class="eyebrow">Bloque de Evaluación y '
                'Calidad</div><h1>Elige el módulo que quieres auditar</h1>'
                '<div class="meta">Están los cinco módulos del proyecto, no sólo '
                'aquellos con los que he avanzado. Todos emiten el mismo objeto, con '
                'las mismas dos métricas y la misma regla de anclaje: lo comparable '
                'no son los módulos, es el veredicto.</div></div>',
                unsafe_allow_html=True)

    # Aquí iba una franja con el recuento del proyecto —módulos evaluables, casos
    # diseñados, conexiones probadas— y una tira con los cinco módulos y su
    # estado de conexión.
    #
    # Se ha quitado por dos motivos. El primero es que **repetía las tarjetas que
    # vienen justo debajo**: los mismos cinco módulos, dos veces, una de ellas sin
    # poder pulsarse. El segundo es de fondo: esas cifras cuentan cómo va el
    # trabajo, no la calidad de ningún módulo, y esta pantalla sirve para elegir
    # qué auditar. Un marcador del propio avance encabezando una herramienta de
    # calidad se lee raro, y además cambia cada semana.
    #
    # Las cifras no se pierden: viven en «Esquema del sistema», que es la pantalla
    # que sí existe para contar el estado real del conjunto.
    fichas = modulos.fichas()
    for inicio in range(0, len(fichas), 3):
        cols = st.columns(3, gap="medium")
        for ficha, col in zip(fichas[inicio:inicio + 3], cols):
            if ui.tarjeta_modulo(ficha, col):
                st.session_state.modulo = ficha["id"]
                st.rerun()
        # Rellena la última fila para que las tarjetas no se estiren
        for col in cols[len(fichas[inicio:inicio + 3]):]:
            col.empty()


def pantalla_no_operativa(ficha):
    ui.cabecera(ficha)
    ui.nota(ficha.get("pendiente", "Rama no operativa todavía."))
    if ficha["casos"]:
        st.markdown("**Batería diseñada**")
        st.dataframe(pd.DataFrame([{"#": n, "Caso": t}
                                   for n, t in ficha["casos"].items()]),
                     use_container_width=True, hide_index=True)
        st.caption("Los casos están diseñados y no ejecutados. Se enseñan porque el "
                   "estado de diseño y el de ejecución son cosas distintas y conviene "
                   "que se vea cuál es cuál.")
    else:
        st.markdown("**Batería**")
        st.caption("No hay ninguna. Escribir casos sin haber visto una salida real "
                   "sería exactamente el error que le mido a los demás: dar por hecho "
                   "algo que no se ha comprobado.")
    if ficha.get("siguiente_paso"):
        st.markdown("**Siguiente paso**")
        st.write(ficha["siguiente_paso"])


def subir_documentos(ficha, clave, carpeta_demo=None):
    """
    Paso 1: de qué documentos parte la evaluación.

    **Elegir de los que ya están manda sobre subirlos**, y el orden no es
    cosmético. Subir un PDF encadena tres cosas que fallan por separado: que el
    despliegue tenga OCR instalado, que el reconocimiento aguante en memoria, y
    que el nombre del fichero case con el de su texto. Con el corpus de Martín
    —trece fotocopias sin una letra de texto— cualquiera de las tres deja el
    módulo inservible, y las tres han fallado ya al menos una vez.

    Los documentos que viajan en el repositorio llevan su lectura hecha al lado.
    Elegirlos de una lista no depende de nada: ni de tesseract, ni de la memoria
    de la máquina, ni de cómo se llame el fichero. Subir sigue estando, para
    documentos nuevos, pero deja de ser el camino obligatorio.
    """
    st.subheader("1 · Documentos")
    st.caption(ficha["entrada"])

    # `carpeta_demo` admite una carpeta o varias. La pantalla del caso ofrece dos:
    # la de los documentos reales —que no se versionan por ser documentación de
    # cliente— y la del par sintético, para que el recorrido se pueda enseñar en
    # un despliegue limpio en vez de quedarse pidiendo ficheros que no están.
    carpetas = ([carpeta_demo] if isinstance(carpeta_demo, str)
                else list(carpeta_demo or []))
    disponibles = [d for c in carpetas for d in guion.documentos_de(c)]
    por_nombre = {d["id"]: d for d in disponibles}
    docs = []

    if disponibles:
        listos = sum(1 for d in disponibles if d.get("legible"))
        st.markdown("**Documentos ya cargados en el sistema**")
        st.caption(f"{len(disponibles)} documentos con su lectura hecha "
                   f"({listos} legibles). Elegirlos de aquí no necesita OCR ni "
                   f"esperar: el texto ya está reconocido y viaja con el "
                   f"repositorio.")
        # Los botones no pueden escribir en la clave del propio `multiselect`:
        # Streamlit prohíbe tocar el estado de un widget que ya se ha creado en
        # esta ejecución, y lo hace con una excepción que se lleva la pantalla
        # entera por delante. Se deja el encargo en otra clave y se aplica aquí,
        # **antes** de instanciarlo, que es el único momento en que está
        # permitido. Con las carpetas vacías el fallo nunca llegó a verse.
        encargo = st.session_state.pop(f"sel_pend_{clave}", None)
        if encargo is not None:
            st.session_state[f"sel_docs_{clave}"] = encargo
        elegidos = st.multiselect(
            "Elige los documentos que quieres evaluar",
            options=sorted(por_nombre),
            key=f"sel_docs_{clave}",
            format_func=lambda n: n.replace("_", " "))
        c1, c2 = st.columns(2)
        if c1.button("Seleccionar todos", key=f"todos_{clave}",
                     use_container_width=True):
            st.session_state[f"sel_pend_{clave}"] = sorted(por_nombre)
            st.rerun()
        if c2.button("Quitar la selección", key=f"ninguno_{clave}",
                     use_container_width=True):
            st.session_state[f"sel_pend_{clave}"] = []
            st.rerun()
        docs = [por_nombre[n] for n in elegidos if n in por_nombre]

    with st.expander("…o subir documentos nuevos", expanded=not disponibles):
        st.caption(
            "Para documentos que el sistema todavía no conoce. Si son escaneos "
            "hace falta OCR instalado, o subir el `.ocr.txt` junto al PDF.")
        subidos = st.file_uploader(
            "Documentos en PDF (y, si los tienes, sus `.ocr.txt`)",
            type=["pdf", "txt"], accept_multiple_files=True, key=f"up_{clave}")
        ocr = st.checkbox(
            "Reconocer el texto de los escaneos (OCR)", value=P.hay_ocr(),
            disabled=not P.hay_ocr(), key=f"ocr_{clave}",
            help="Un escaneo tarda cerca de un minuto por documento."
                 if P.hay_ocr() else
                 "No hay OCR en este despliegue: sube el `.ocr.txt` junto al PDF.")
        if subidos:
            firmas = tuple((f.name, hash(f.getvalue())) for f in subidos)
            memo = st.session_state.setdefault("_docs_leidos", {})
            llave = (clave, firmas, bool(ocr))
            if llave not in memo:
                with st.spinner("Leyendo los documentos…"):
                    with tempfile.TemporaryDirectory() as tmp:
                        memo.clear()
                        memo[llave] = P.leer_subidos(subidos, tmp, ocr=ocr)
            nuevos = memo[llave]
            huerfanos = [d for d in nuevos if d.get("huerfano")]
            if huerfanos:
                st.warning(
                    "**Estos textos reconocidos no se han emparejado con ningún "
                    "PDF:** " + ", ".join(d["nombre"] for d in huerfanos)
                    + ". El emparejamiento ignora mayúsculas, espacios, guiones y "
                      "tildes; si aun así no casa, los nombres son distintos.")
            docs = docs + [d for d in nuevos if not d.get("huerfano")]

    if not docs:
        st.info("Elige al menos un documento de la lista, o sube uno nuevo.")
        st.stop()

    # Qué se ha podido leer y por qué vía. Va después de elegir y antes de
    # evaluar, porque condiciona todo lo que viene detrás.
    escaneos = [d for d in docs if d.get("via") == "ocr"]
    ilegibles = [d for d in docs if not d.get("legible")]
    if escaneos:
        ui.nota(f"<b>{len(escaneos)} de {len(docs)} documento(s) son escaneos sin "
                f"capa de texto</b> y se leen por OCR. El veredicto lo declara: "
                f"lo que se compara es una lectura del evaluador contra una "
                f"lectura del módulo, así que una discrepancia sobre una fecha no "
                f"demuestra por sí sola que el módulo se equivoque.", acento=True)
    if ilegibles:
        st.error("**Sin texto ni con OCR:** "
                 + ", ".join(d["nombre"] for d in ilegibles)
                 + ". Estos documentos no producen «sin incidencias»: producen "
                   "«no se ha podido comprobar».")
        for d in ilegibles:
            for f in (d.get("fallos_lectura") or []):
                st.caption(f"· {d['nombre']}: {f}")
    for d in docs:
        integ = d.get("integridad") or {}
        if integ.get("completo") is False:
            st.warning(f"**{d['nombre']}** está incompleto: su pie declara "
                       f"{integ['paginas_declaradas']} páginas y el fichero tiene "
                       f"{integ['paginas_fichero']} (faltan "
                       f"{', '.join(str(n) for n in integ['faltantes'])}). No "
                       f"puntúa contra el módulo; se registra como hallazgo.")
    return docs


def evaluar_pulsado(clave, etiqueta="Evaluar la salida del módulo"):
    """
    El botón de evaluar, con memoria.

    Streamlit reejecuta el script entero en cada interacción y un `st.button`
    sólo devuelve True en la ejecución en la que se pulsa. Sin recordar que ya se
    evaluó, cualquier botón posterior —convocar al panel, redactar el informe—
    haría desaparecer el resultado al pulsarlo. Se anota en el estado de sesión y
    se limpia lo que dependía de la evaluación anterior.
    """
    if st.button(etiqueta, type="primary", key=f"btn_eval_{clave}"):
        st.session_state[f"evaluado_{clave}"] = True
        st.session_state.pop(f"panel_{clave}", None)
        st.session_state.pop(f"informe_{clave}", None)
        st.session_state.pop(f"asesor_{clave}", None)
    return bool(st.session_state.get(f"evaluado_{clave}"))


def flujo_vigencia(rama):
    ficha = rama.FICHA
    ui.cabecera(ficha)
    modo = ui.selector_modo_lectura(ficha, "vigencia")

    docs = subir_documentos(ficha, "vigencia", carpeta_demo="vigencia")
    docs, avisos_tipo = clasificacion.anotar_tipos(
        docs, rama.clasificar, rama.TIPOS, modo,
        permiso=llm.permiso_de(ficha))
    for _a in avisos_tipo:
        st.info(_a)
    ui.tabla_documentos(docs, rama.TIPOS, rama.clasificar, rama.extraer)

    c1, c2 = st.columns(2)
    fecha = c1.date_input(
        "Fecha de consulta", value=date.today(),
        help="Un estado de vigencia sin fecha de consulta no es verificable: el "
             "mismo documento está vigente antes de su vencimiento y caducado "
             "después. Queda escrita en el veredicto.")
    ventana = c2.number_input(
        "Ventana de vencimientos (días)", min_value=1, max_value=365,
        value=rama.VENTANA_DIAS,
        help="La pregunta 2 de la prueba inicial: qué documentos vencen en los "
             "próximos N días, sin incluir los ya vencidos ni los posteriores.")

    try:
        esperados, ctx = rama.verdad_de_campo(docs, fecha, modo)
    except llm.NoDisponible as e:
        # No se degrada en silencio: se dice qué ha pasado y con qué se ha leído.
        st.error(f"La lectura asistida ha fallado y se ha vuelto al modo "
                 f"determinista. {e}")
        modo = "determinista"
        esperados, ctx = rama.verdad_de_campo(docs, fecha, modo)

    with st.expander("Verdad de campo calculada por el evaluador", expanded=False):
        st.dataframe(pd.DataFrame([{
            "Documento": e["id_documento"],
            "Cadena documental": e["cadena"] or "—",
            "Emisión": e["fecha_emision"].strftime("%d/%m/%Y") if e["fecha_emision"] else "—",
            "Vencimiento": e["fecha_caducidad"].strftime("%d/%m/%Y") if e["fecha_caducidad"] else "—",
            "Estado": rama.ESTADOS[e["estado"]], "Por qué": e["motivo"],
        } for e in esperados]), use_container_width=True, hide_index=True)
        cadenas = {k: v for k, v in ctx["cadenas"].items() if len(v) > 1}
        if cadenas:
            st.caption("Cadenas documentales con más de una versión: "
                       + "; ".join(f"«{k}» → " + ", ".join(x["id_documento"] for x in v)
                                   for k, v in cadenas.items()))
        st.caption("Ningún dato de esta tabla procede del módulo evaluado. Un "
                   "documento sin fecha de vencimiento no se declara vigente: la "
                   "ausencia de plazo no es vigencia indefinida.")

    ui.bloque_procedencia(ctx.get("procedencias"), modo)

    if modo != "determinista" and llm.esta_disponible():
        with st.expander("¿Es estable la lectura del modelo?", expanded=False):
            st.caption("El evaluador se aplica a sí mismo el caso que exige a los "
                       "demás. Lee el mismo documento varias veces saltándose la "
                       "caché y enseña qué campos cambian. Si la lectura baila, la "
                       "verdad de campo no es reproducible, y entonces el veredicto "
                       "que salga de ella tampoco: hay que declararlo. Cuesta una "
                       "llamada por repetición, así que no se hace solo.")
            c1, c2 = st.columns([2, 1])
            cual = c1.selectbox("Documento", [d["nombre"] for d in docs],
                                key="est_doc")
            k = c2.number_input("Repeticiones", 2, 5, 3, key="est_k")
            if st.button(f"Medir estabilidad · {int(k)} llamadas", key="est_btn"):
                doc = next(d for d in docs if d["nombre"] == cual)
                try:
                    r = llm.medir_estabilidad(doc["texto"], ficha["esquema_campos"],
                                              ficha["prompt_extraccion"], int(k))
                except llm.NoDisponible as e:
                    st.error(str(e))
                else:
                    if r["estable"]:
                        st.success(f"Estable: {r['ejecuciones']} lecturas de "
                                   f"{cual} devuelven los mismos {r['campos']} "
                                   f"campos.")
                    else:
                        st.warning(f"{len(r['inestables'])} de {r['campos']} campos "
                                   f"cambian entre lecturas.")
                        st.dataframe(pd.DataFrame([
                            {"Campo": c, "Valores distintos": " · ".join(v)}
                            for c, v in r["inestables"].items()]),
                            use_container_width=True, hide_index=True)

    st.subheader("2 · Salida del módulo")
    st.caption(ficha["entrada_respuesta"])
    c_pega, c_ej = st.columns([3, 1])
    with c_ej:
        st.caption("Salidas reales de IAlert ya transcritas:")
        if st.button("Cargar todas", use_container_width=True,
                     help="Las fichas que IAlert emite para los documentos de "
                          "RALSA, transcritas de la pantalla de Martín. Lo que no "
                          "se veía en el vídeo no se ha rellenado."):
            st.session_state["resp_vigencia"] = (
                rama.SALIDA_IALERT_CRED + "\n\n" + rama.SALIDA_IALERT_TODAS)
        if st.button("Sólo el contrato CRED", use_container_width=True):
            st.session_state["resp_vigencia"] = rama.SALIDA_IALERT_CRED
    respuesta = c_pega.text_area(
        "Salida del módulo de vigencia", height=220, key="resp_vigencia",
        label_visibility="collapsed",
        placeholder="Copia la ficha del documento entera desde la pantalla de "
                    "IAlert —el estado, la alerta y la tabla de campos— y pégala "
                    "aquí. Da igual si al copiar la tabla queda con el nombre del "
                    "campo y su valor en líneas separadas: se reconoce igual. "
                    "También se acepta JSON o CSV.")
    reportados, avisos = rama.interpretar(respuesta, modo)
    for a in avisos:
        st.warning(a)
    eventos = [r for r in reportados if r.get("tipo") == "evento"]
    reportados = [r for r in reportados if r.get("tipo", "estado") == "estado"]

    st.markdown("**Interpretación de la salida**")
    if reportados:
        st.caption("Revisa que coincide con lo que dice el módulo. Puedes corregir "
                   "cualquier celda antes de evaluar.")
        reportados = ui.editor(reportados, rama, "rev_vigencia")
    elif respuesta.strip():
        # No basta con decir que no se ha reconocido: hay que decir qué se ha
        # visto. Si no, la única salida es probar formatos hasta que uno cuele.
        diag = rama.diagnosticar(respuesta)
        st.error(f"**No se ha reconocido ningún documento.** De las "
                 f"{diag['lineas']} líneas pegadas, {len(diag['reconocidas'])} "
                 f"corresponden a campos que el evaluador conoce.")
        with st.expander("Qué ha leído el evaluador", expanded=True):
            if diag["reconocidas"]:
                st.markdown("**Campos reconocidos:** "
                            + ", ".join(f"`{l[:40]}`" for l in diag["reconocidas"][:12]))
            if diag["sueltas"]:
                st.markdown("**Líneas que no encajan con ningún campo:**")
                st.code("\n".join(diag["sueltas"]), language=None)
            st.caption("Etiquetas que el intérprete reconoce: "
                       + ", ".join(diag["conocidas"]) + ". Si IAlert las llama de "
                       "otra manera, dímelo y se añaden — o rellena la tabla de "
                       "abajo a mano, que también vale.")
        st.caption("Mientras tanto puedes introducir el estado a mano:")
        reportados = ui.editor([], rama, "rev_vigencia_manual")
    else:
        st.info("Sin respuesta introducida. Si continúas, se evaluará como ausencia "
                "total de clasificación.")

    if eventos:
        st.markdown("**Eventos y alertas reconocidos**")
        st.caption("Un evento no es un estado: alimenta el caso de la ventana de "
                   "vencimientos y el del aviso anticipado, no el de clasificación.")
        st.dataframe(pd.DataFrame([{
            "Documento": e["id_documento"], "Evento": e["evento"] or "—",
            "Fecha": e["fecha_evento"] or "—",
            "Días": e["dias"] if e["dias"] is not None else "—",
            "Preaviso declarado": e["preaviso_dias"] or "—"} for e in eventos]),
            use_container_width=True, hide_index=True)

    with st.expander("Segunda ejecución · repetibilidad (opcional)"):
        st.caption("Vuelve a pasar los mismos documentos por el módulo sin cambiar "
                   "nada y pega aquí la nueva salida. La redacción puede variar, el "
                   "estado asignado no debería.")
        respuesta_2 = st.text_area("Segunda ejecución", height=110,
                                   key="resp2_vigencia", label_visibility="collapsed")
    repeticion = None
    if respuesta_2.strip():
        repeticion, avisos_2 = rama.interpretar(respuesta_2, modo)
        for a in avisos_2:
            st.warning(f"Segunda ejecución: {a}")

    st.subheader("3 · Evaluación")
    if not evaluar_pulsado("vigencia"):
        st.stop()

    ev = rama.evaluar(esperados, reportados + eventos, fecha, repeticion, modo,
                      ventana_dias=int(ventana), contexto=ctx)
    er = V.evaluation_result(ficha, ev, rama.sujeto(esperados), fecha)

    # Cuando el evaluador se abstiene, decir qué lo cerraría. Un «pendiente» que
    # no explica cómo dejar de estarlo es un callejón.
    if ev.get("abstenidos") and modo == "determinista":
        st.warning(
            f"**El evaluador se abstiene sobre "
            f"{len(ev['abstenidos'])} documento(s)** — no ha sabido leerles la "
            f"cláusula de duración, así que no entran en el contraste y sus casos "
            f"quedan pendientes en lugar de contar como fallo del módulo. Esto pasa "
            f"con los escaneos antiguos: el reconocimiento devuelve texto con "
            f"erratas y ninguna regla saca de ahí una fecha. **El modo asistido lo "
            f"cierra**: el modelo lee los mismos campos sobre el mismo texto —no "
            f"decide el estado, eso lo sigue haciendo la regla— y cada valor queda "
            f"marcado con su procedencia. Se cambia arriba, en «cómo lee el "
            f"evaluador».")
    elif ev.get("abstenidos"):
        # Dos causas muy distintas bajo la misma palabra. Confundirlas manda a
        # buscar el problema donde no está: una se arregla instalando un paquete
        # y la otra leyendo el documento a mano.
        _ilegibles = [e for e in ev["abstenidos"] if not e.get("legible")]
        _sin_clausula = [e for e in ev["abstenidos"] if e.get("legible")]
        if _ilegibles:
            st.error(
                f"**{len(_ilegibles)} documento(s) no se han podido leer**: "
                + ", ".join(e["id_documento"] for e in _ilegibles)
                + ". No es que el modelo no los entienda — es que no ha llegado a "
                  "ver ningún texto. Son escaneos y el OCR no está disponible en "
                  "este despliegue"
                + (" (ver el aviso del principio de la página)." if SIN_OCR
                   else ", o el reconocimiento no ha devuelto nada legible.")
                + " El modo asistido no arregla esto: el modelo lee texto, no "
                  "imágenes.")
        if _sin_clausula:
            st.warning(
                f"**{len(_sin_clausula)} documento(s) se han leído pero no se "
                f"les ha encontrado la cláusula de duración**: "
                + ", ".join(e["id_documento"] for e in _sin_clausula)
                + ". Ni las reglas ni el modelo la sostienen con una cita del "
                  "texto. Mira la tabla de procedencia: si hay descartes por "
                  "anclaje, el modelo sí propuso un valor y el evaluador no se lo "
                  "ha aceptado. Confírmalo a mano o déjalo como no evaluable.")

    ui.bloque_contraste(ficha, ev)
    ui.bloque_hallazgos(ev)
    df = ui.bloque_casos(ficha, ev)
    ui.bloque_requisitos(ficha, er)
    ui.bloque_severidad(ficha, ev)
    ui.bloque_veredicto(er)
    ui.bloque_evolucion(ficha, er, ev, "vigencia")
    panel = ui.bloque_asesor(ficha, er, ev, rama.evidencia_panel(respuesta),
                             "vigencia", "vigencia")
    ui.bloque_informe(ficha, er, ev, panel, "vigencia", "vigencia")
    ui.exportar(ficha, er, ev, df, "vigencia", panel,
                f"{len(docs)} documento(s) en PDF + salida pegada de IAlert")


def flujo_auditoria(rama):
    ficha = rama.FICHA
    ui.cabecera(ficha)
    modo = ui.selector_modo_lectura(ficha, "auditoria")

    docs = subir_documentos(ficha, "auditoria", carpeta_demo="auditoria")

    # De qué tipo es cada documento, y quién lo ha decidido. En modo
    # asistido, lo que la regla no reconoce se le pregunta al modelo —y
    # sólo eso—. Va antes que nada porque la rama entera depende del tipo:
    # un documento sin identificar no entra en la comparación, y hasta
    # ahora eso ocurría en silencio.
    docs, avisos_tipo = clasificacion.anotar_tipos(
        docs, rama.clasificar, rama.TIPOS, modo,
        permiso=llm.permiso_de(ficha))
    for _a in avisos_tipo:
        st.info(_a)
    ui.tabla_documentos(docs, rama.TIPOS, rama.clasificar)

    try:
        esperados, contexto = rama.verdad_de_campo(docs, modo)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    except llm.NoDisponible as e:
        st.error(f"La lectura asistida ha fallado y se ha vuelto al modo "
                 f"determinista. {e}")
        modo = "determinista"
        esperados, contexto = rama.verdad_de_campo(docs, modo)

    with st.expander("Campos extraídos de los documentos", expanded=False):
        st.dataframe(pd.DataFrame([{
            "Campo": etiqueta,
            "Documentación de cliente": contexto["cliente"].get(k, "—"),
            "Orden de fabricación": contexto["orden"].get(k, "—"),
        } for k, etiqueta in rama.ETIQUETAS.items()]), use_container_width=True,
            hide_index=True)
        respaldos = {k: v for k, v in contexto["orden"].items()
                     if k in ("cantidad_logistica", "cantidad_impresion")}
        if respaldos:
            st.caption("Valores de respaldo hallados dentro de la propia orden: "
                       + " · ".join(f"{k.replace('cantidad_', '')}: {v}"
                                    for k, v in respaldos.items()))

    st.subheader("2 · Respuesta del módulo")
    st.caption(ficha["entrada_respuesta"])
    if "resp_auditoria" not in st.session_state:
        st.session_state.resp_auditoria = ""
    b1, b2 = st.columns([1, 3])
    if b1.button("Pegar la respuesta del 42805", use_container_width=True):
        st.session_state.resp_auditoria = rama.EJEMPLO
    b2.caption("Atajo para la demostración: carga la respuesta que el módulo emitió "
               "sobre el pedido 42805.")
    respuesta = st.text_area("Respuesta del módulo", key="resp_auditoria", height=220,
                             label_visibility="collapsed")

    reportados, avisos = rama.interpretar(respuesta, modo)
    for a in avisos:
        st.warning(a)

    st.markdown("**Interpretación de la respuesta**")
    if reportados:
        st.caption("Revisa que coincide con lo que dice el módulo. Puedes corregir "
                   "cualquier celda antes de evaluar.")
        reportados = ui.editor(reportados, rama, "rev_auditoria")
    elif respuesta.strip():
        st.info("No se ha reconocido ninguna incidencia. Si el módulo efectivamente "
                "no reportó nada, continúa: el evaluador comprobará si esa ausencia "
                "era correcta.")
    else:
        st.info("Sin respuesta introducida. Si continúas, se evaluará como ausencia "
                "de incidencias.")

    with st.expander("Segunda ejecución · repetibilidad (opcional)"):
        respuesta_2 = st.text_area("Segunda ejecución", height=110,
                                   key="resp2_auditoria", label_visibility="collapsed")
    repeticion = None
    if respuesta_2.strip():
        repeticion, avisos_2 = rama.interpretar(respuesta_2, modo)
        for a in avisos_2:
            st.warning(f"Segunda ejecución: {a}")

    evidencias = ui.bloque_evidencia(rama, "auditoria")

    st.subheader("3 · Evaluación")
    if not evaluar_pulsado("auditoria"):
        st.stop()

    ev = rama.evaluar(esperados, reportados, contexto, respuesta, repeticion, modo,
                      evidencias=evidencias)
    er = V.evaluation_result(ficha, ev, rama.sujeto(contexto))
    ui.bloque_contraste(ficha, ev)
    ui.bloque_hallazgos(ev)
    df = ui.bloque_casos(ficha, ev)
    ui.bloque_requisitos(ficha, er)
    ui.bloque_severidad(ficha, ev)
    ui.bloque_veredicto(er)
    ui.bloque_evolucion(ficha, er, ev, "auditoria")
    panel = ui.bloque_asesor(ficha, er, ev, rama.evidencia_panel(respuesta),
                             "auditoria", contexto["pedido"])
    ui.bloque_informe(ficha, er, ev, panel, "auditoria", contexto["pedido"])
    ui.exportar(ficha, er, ev, df, contexto["pedido"], panel,
                f"orden de fabricación y documentos de cliente del pedido "
                f"{contexto['pedido']}, en PDF")


def flujo_similitud(rama):
    ficha = rama.FICHA
    ui.cabecera(ficha)

    st.subheader("1 · Consulta exportada")
    ui.nota("<b>Aquí no se suben documentos, y no es un olvido.</b> El módulo de "
            "Álvaro no lee PDF: recibe un pedido, busca en un histórico de "
            "proyectos ya indexado y devuelve un ranking de los más parecidos. Lo "
            "único que existe es esa exportación en JSON, que es <b>a la vez el dato "
            "de origen y la salida a evaluar</b>.<br><br>"
            "Por eso el evaluador no contrasta contra una fuente externa: "
            "<b>rehace la aritmética</b> —recalcula la puntuación desde las señales "
            "y el peso declarados, y el orden desde las puntuaciones—, <b>decide por "
            "su cuenta qué proyectos son equivalentes al pedido</b> con los "
            "parámetros que el propio módulo publica, y <b>rehace la ordenación "
            "entera desde los pesos que Álvaro declara</b>.")

    ejemplos = sorted((guion.RAIZ / "similitud").glob("caso*.json")) \
        if (guion.RAIZ / "similitud").is_dir() else []
    texto = None
    if ejemplos:
        # Etiquetas legibles: el nombre del fichero no dice de qué va cada consulta.
        etiquetas = {"— subir un fichero —": None}
        for f in ejemplos:
            try:
                r = rama.resumen_consulta(json.loads(f.read_text(encoding="utf-8")))
                et = f"{r['pedido']} — {r['nota'].split(' · ')[0] if r['nota'] else 'sin nota'}"
            except Exception:
                et = f.name
            etiquetas[et] = f
        elegido = st.selectbox("Consulta", list(etiquetas), key="sel_similitud")
        if etiquetas[elegido] is not None:
            texto = etiquetas[elegido].read_text(encoding="utf-8")
    if texto is None:
        subido = st.file_uploader("Exportación en JSON", type="json",
                                  key="up_similitud")
        if subido:
            texto = subido.getvalue().decode("utf-8")
    if texto is None:
        st.info("Esperando la exportación de una consulta.")
        st.stop()

    datos, avisos = rama.interpretar(texto)
    for a in avisos:
        st.warning(a)
    if datos is None:
        st.stop()

    # Qué es esta consulta, antes de enseñar ningún veredicto sobre ella. El nombre
    # del fichero no dice nada a quien no lo escribió.
    rc = rama.resumen_consulta(datos)
    st.markdown(f"**Pedido consultado:** {rc['pedido']}")
    if rc["nota"]:
        st.caption(f"Álvaro anota sobre este caso: {rc['nota']}")
    ui.fila_kpis([
        ui.kpi("Corpus evaluado", rc["corpus"], "proyectos del histórico"),
        ui.kpi("Pasan el filtro", rc["resultados"],
               f"{rc['descartados']} descartados en la Capa 1"),
        ui.kpi("Equivalentes", rc["equivalentes"],
               "que determina el evaluador por su cuenta", acento=True),
        ui.kpi("Peso semántico", rc["peso_semantico"],
               "0 = la puntuación es sólo paramétrica"),
    ])
    if rc["lista_vacia"]:
        ui.nota("Esta consulta <b>no devuelve ningún resultado</b>: el filtro de la "
                "Capa 1 excluyó a todas las candidatas. Lo que se evalúa aquí es si "
                "el módulo lo explica bien, no si acierta el ranking.", acento=True)
    elif rc["equivalentes"]:
        ui.nota(f"El evaluador considera equivalentes al pedido a "
                f"<b>{', '.join(rc['ids_equivalentes'])}</b> — coinciden en todos los "
                f"parámetros categóricos y no se desvían más del "
                f"{rc['tolerancia']:.1%} en ninguno de los numéricos. Ésa es la "
                f"verdad de campo: lo que se comprueba es si el módulo los pone "
                f"arriba.", acento=True)

    # El umbral no se elige: se lee del propio conjunto buscando el salto entre las
    # candidatas parecidas y las que no lo son. La barra existe para lo contrario de
    # lo que parece — no para ajustar hasta que salga bien, sino para comprobar si el
    # veredicto aguanta cuando se mueve.
    # Tabla de contribución por parámetro. Sin ella el caso 11 queda pendiente —no
    # falla— porque la ordenación no se puede rehacer desde la salida sola. Que
    # haya que pedirla aparte es justamente el hallazgo de trazabilidad.
    contrib = None
    ruta_csv = guion.RAIZ / "similitud" / "contribuciones_peso_semantico_0.csv"
    with st.expander("Tabla de contribución por parámetro · reproducir la "
                     "ordenación", expanded=False):
        st.caption("Una fila por candidata y parámetro, con lo que cada uno aporta "
                   "al bruto. Es lo único que permite rehacer una puntuación sin "
                   "tener el corpus delante. Álvaro la aportó el 27/08 para los "
                   "grupos SYN-0041 y SYN-0052.")
        usar = st.checkbox("Usar la tabla aportada por Álvaro (27/08)",
                           value=ruta_csv.is_file(), key="chk_contrib_similitud",
                           disabled=not ruta_csv.is_file())
        subido_csv = st.file_uploader("O aportar otra tabla (CSV)", type="csv",
                                      key="up_contrib_similitud")
        crudo = None
        if subido_csv:
            crudo = subido_csv.getvalue().decode("utf-8")
        elif usar and ruta_csv.is_file():
            crudo = ruta_csv.read_text(encoding="utf-8")
        if crudo:
            try:
                contrib = rama.cargar_contribuciones(crudo)
                st.success("Tabla cargada: "
                           + ", ".join(f"{g} ({len(c)} candidatas)"
                                       for g, c in contrib.items()))
            except Exception as e:
                contrib = None
                st.error(f"No se pudo leer la tabla: {e}")

    esperados, ctx = rama.verdad_de_campo(datos, contribuciones=contrib)
    diag = ctx["umbral"]

    if diag.get("automatico"):
        ui.nota(f"<b>Umbral de equivalencia {ctx['tolerancia']:.1%}, derivado del "
                f"propio conjunto.</b> {diag['motivo'].capitalize()}.", acento=True)
    else:
        ui.nota(f"<b>Umbral de respaldo {ctx['tolerancia']:.1%}.</b> "
                f"{diag['motivo'].capitalize()} — aquí la frontera la pone el "
                f"evaluador, no los datos, y eso hace discutible el caso del ranking.")

    with st.expander("Análisis de sensibilidad · ¿aguanta el veredicto si muevo el "
                     "umbral?", expanded=False):
        st.caption("Un umbral derivado sólo vale si el resultado no depende de él. "
                   "Esta tabla recorre el rango entero y enseña dónde cambia la "
                   "respuesta. Si el veredicto es el mismo en toda la banda del "
                   "salto, el corte no está sostenido con pinzas.")
        filas = []
        for pct in range(2, 31, 2):
            e_i, c_i = rama.verdad_de_campo(datos, pct / 100, contrib)
            ev_i = rama.evaluar(e_i, c_i)
            ct = ev_i["contraste"]
            filas.append({"Umbral": f"{pct} %", "Equivalentes": len(e_i),
                          "Exhaustividad": f"{ct['exhaustividad']}%"
                                           if ct["exhaustividad"] is not None else "—",
                          "Precisión": f"{ct['precision']}%"
                                       if ct["precision"] is not None else "—",
                          "Caso del ranking":
                              ui.B.TEXTO[ev_i["casos"][4]["resultado"]],
                          "": "◀ derivado" if abs(pct / 100 - ctx["tolerancia"]) < 0.01
                              else ""})
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

        manual = st.checkbox("Fijar el umbral a mano", value=False, key="man_similitud")
        if manual:
            pct = st.slider("Umbral", 1, 30, int(round(ctx["tolerancia"] * 100)), 1,
                            format="%d %%", key="umb_similitud")
            esperados, ctx = rama.verdad_de_campo(datos, pct / 100, contrib)
            st.warning(f"Umbral impuesto a mano: {pct} %. El veredicto lo declarará "
                       f"como tal.")

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Consulta**  \n{ctx['consulta']}")
    c2.markdown(f"**Peso semántico**  \n{ctx['peso']}")
    c3.markdown(f"**Candidatas**  \n{ctx['n_resultados']} en el ranking · "
                f"{ctx['n_descartados']} descartadas")
    st.caption(f"Pedido: {datos.get('pedido_consultado', '—')}")

    with st.expander("Verdad de campo calculada por el evaluador", expanded=False):
        st.dataframe(pd.DataFrame([{
            "Posición": p["posicion"], "Proyecto": p["id_proyecto"],
            "Desviación máxima": f"{p['desviacion']:.1%}",
            "Categóricos que no coinciden":
                ", ".join(p["categoricos_distintos"]) or "—",
            "Equivalente al pedido": "Sí" if p["equivalente"] else "No",
        } for p in ctx["perfiles"]]), use_container_width=True, hide_index=True)
        peor, mejor = ctx["margen"]
        if peor is not None and mejor is not None:
            st.caption(f"Margen del conjunto: el equivalente que más se desvía está "
                       f"al {peor:.1%} y el no equivalente que menos, al {mejor:.1%}. "
                       f"Cuanto mayor sea el hueco, menos discutible es el umbral.")

    st.subheader("2 · Segunda ejecución · repetibilidad (opcional)")
    with st.expander("Aportar una segunda exportación de la misma consulta"):
        subido2 = st.file_uploader("Segunda exportación", type="json",
                                   key="up2_similitud")
    repeticion = None
    if subido2:
        repeticion, avisos2 = rama.interpretar(subido2.getvalue().decode("utf-8"))
        for a in avisos2:
            st.warning(f"Segunda ejecución: {a}")

    st.subheader("3 · Evaluación")
    if not evaluar_pulsado("similitud"):
        st.stop()

    ev = rama.evaluar(esperados, ctx, repeticion,
                      estado_previo=estado_previo)
    er = V.evaluation_result(ficha, ev, rama.sujeto(ctx))
    ui.bloque_contraste(ficha, ev)
    ui.bloque_hallazgos(ev)
    df = ui.bloque_casos(ficha, ev)
    ui.bloque_requisitos(ficha, er)
    ui.bloque_severidad(ficha, ev)
    ui.bloque_veredicto(er)
    nombre = ctx["consulta"] or "similitud"
    ui.bloque_evolucion(ficha, er, ev, "similitud")
    panel = ui.bloque_asesor(ficha, er, ev, rama.evidencia_panel(datos),
                             "similitud", nombre)
    ui.bloque_informe(ficha, er, ev, panel, "similitud", nombre)
    ui.exportar(ficha, er, ev, df, nombre, panel,
                "exportación JSON de la consulta")


def flujo_contradicciones(rama):
    ficha = rama.FICHA
    ui.cabecera(ficha)

    st.subheader("1 · Exportación del pedido")
    st.caption(ficha["entrada"])
    ui.nota("Aquí el contraste es el más limpio del sistema: la exportación trae "
            "en el mismo fichero <b>los hechos extraídos de cada documento</b> y "
            "<b>las contradicciones que el módulo declara</b>. El evaluador "
            "<b>ignora la tabla de contradicciones y la recalcula desde los "
            "hechos</b> —dos hechos activos del mismo campo con valores distintos "
            "son una contradicción, la haya visto el módulo o no— y sólo entonces "
            "compara. No hay lectura de por medio que pueda introducir error.")

    carpeta = guion.RAIZ / "contradicciones"
    ejemplos = sorted(carpeta.glob("*.json")) if carpeta.is_dir() else []
    texto = None
    if ejemplos:
        nombres = ["— subir un fichero —"] + [f.name for f in ejemplos]
        elegido = st.selectbox("Exportación", nombres, key="sel_contradicciones")
        if elegido != nombres[0]:
            texto = next(f for f in ejemplos
                         if f.name == elegido).read_text(encoding="utf-8")
    if texto is None:
        subido = st.file_uploader("Exportación en JSON", type="json",
                                  key="up_contradicciones")
        if subido:
            texto = subido.getvalue().decode("utf-8")
    if texto is None:
        st.info("Esperando la exportación de un pedido.")
        st.stop()

    datos, avisos = rama.interpretar(texto)
    for a in avisos:
        st.warning(a)
    if datos is None:
        st.stop()

    esperados, ctx = rama.verdad_de_campo(datos)

    ui.panel_contradicciones(datos, esperados, ctx)

    with st.expander("Todos los hechos extraídos, tal cual vienen"):
        st.caption("La tabla completa, por si hace falta comprobar un hecho que no "
                   "entra en ninguna contradicción.")
        st.dataframe(pd.DataFrame([{
            "#": h["id"], "Documento": h["documento"], "Campo": h["campo"],
            "Etiqueta en el documento": h["etiqueta"], "Valor": h["valor"],
            "Activo": "sí" if h["activo"] else "no"} for h in datos["hechos"]]),
            use_container_width=True, hide_index=True)

    ui.fila_kpis([
        ui.kpi("Hechos activos", ctx["hechos_activos"],
               f"de {ctx['hechos_totales']} extraídos"),
        ui.kpi("Contradicciones derivadas", len(esperados),
               "recalculadas desde los hechos", acento=True),
        ui.kpi("Contradicciones emitidas", len(datos["contradicciones"]),
               "declaradas por el módulo"),
        ui.kpi("Revisiones humanas",
               sum(1 for c in datos["contradicciones"] if c.get("resolucion")),
               "con rastro registrado"),
    ])

    st.subheader("2 · El estado anterior · la decisión en el tiempo")
    ui.nota("Este módulo no es un lector: registra <b>decisiones humanas</b> y "
            "promete conservarlas. Una promesa sobre el tiempo no se comprueba con "
            "una sola foto. Sube aquí la exportación del <b>mismo pedido tomada "
            "antes</b> de que alguien resolviera, y el evaluador podrá ver tres "
            "cosas que de una en una son invisibles: lo que cambió, lo que "
            "<b>no debía</b> cambiar, y lo que se perdió por el camino.")
    subido0 = st.file_uploader("Exportación anterior (antes de resolver)",
                               type="json", key="up0_contradicciones")
    estado_previo = None
    if subido0:
        estado_previo, avisos0 = rama.interpretar(subido0.getvalue().decode("utf-8"))
        for a in avisos0:
            st.warning(f"Exportación anterior: {a}")
        if estado_previo:
            ui.panel_cambios(estado_previo, datos, rama.comparar_estados)

    st.subheader("3 · Segunda ejecución · repetibilidad (opcional)")
    st.caption("Vuelve a exportar el mismo pedido sin cambiar nada. El módulo emite "
               "una huella por contradicción, así que la comparación es inmediata.")
    subido2 = st.file_uploader("Segunda exportación", type="json",
                               key="up2_contradicciones", label_visibility="collapsed")
    repeticion = None
    if subido2:
        repeticion, avisos2 = rama.interpretar(subido2.getvalue().decode("utf-8"))
        for a in avisos2:
            st.warning(f"Segunda exportación: {a}")

    st.subheader("4 · Evaluación")
    if not evaluar_pulsado("contradicciones"):
        st.stop()

    ev = rama.evaluar(esperados, ctx, repeticion,
                      estado_previo=estado_previo)
    er = V.evaluation_result(ficha, ev, rama.sujeto(ctx))
    ui.bloque_contraste(ficha, ev)
    ui.bloque_hallazgos(ev)
    df = ui.bloque_casos(ficha, ev)
    ui.bloque_requisitos(ficha, er)
    ui.bloque_severidad(ficha, ev)
    ui.bloque_veredicto(er)
    nombre = datos["grupo"] or "contradicciones"
    ui.bloque_evolucion(ficha, er, ev, "contradicciones")
    panel = ui.bloque_asesor(ficha, er, ev, rama.evidencia_panel(datos),
                             "contradicciones", nombre)
    ui.bloque_informe(ficha, er, ev, panel, "contradicciones", nombre)
    ui.exportar(ficha, er, ev, df, nombre, panel,
                "exportación JSON del pedido")


FLUJOS = {"auditoria": flujo_auditoria, "vigencia": flujo_vigencia,
          "similitud": flujo_similitud,
          "contradicciones": flujo_contradicciones}


def pantalla_evaluar():
    id_modulo = st.session_state.get("modulo")
    if not id_modulo:
        rejilla_modulos()
        return

    if st.button("← Todos los módulos"):
        st.session_state.modulo = None
        st.rerun()

    rama = modulos.rama(id_modulo)
    if not rama.FICHA["operativo"]:
        pantalla_no_operativa(rama.FICHA)
        return
    FLUJOS[id_modulo](rama)


if pantalla == "Esquema del sistema":
    pantalla_esquema()
elif pantalla == "Consola":
    pantalla_consola()
else:
    pantalla_evaluar()
