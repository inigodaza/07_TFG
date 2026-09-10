"""
La consola: la aplicación funcionando, no un guion de pantallas.

El cambio respecto a la versión anterior
-----------------------------------------
Antes había un asistente de seis pasos con su barrita de progreso. Se entendía,
pero se entendía como una **demostración**, y lo que hay que enseñar es un
**producto**. La diferencia práctica es quién manda: en un asistente manda el
guion, y en un producto manda lo que está pasando.

Aquí el sistema ya está en marcha cuando alguien abre la pantalla. Ha leído los
documentos que había, ha contrastado cada pedido consigo mismo y tiene una cola
de alarmas abiertas. El operario no lo arranca: llega a algo que lleva rato
funcionando y se pone al mando de lo que ha ocurrido.

Las cuatro partes del esquema de Fabián
----------------------------------------
    FLUJO CONTINUO      `arrancar()` — entra documentación, se analiza, quedan
                        alarmas. Nadie ha pedido que se revise nada.
    HERRAMIENTAS        `analisis_*()` — incongruencias, diligencia y similitud.
                        Cada una hace algo de verdad o dice que no aplica.
    ONTOLOGÍA Y PERMISOS `contexto_operario()` — quién eres, dónde estás y qué te
                        deja hacer la alarma que tienes delante.
    APRENDIZAJE         `nucleo/memoria.py` — lo ya decidido vuelve como
                        precedente la próxima vez.

Lo que sigue sin fingirse
--------------------------
La salida del módulo de Juan se le entrega al sistema; no se va a buscar. La
cadena de validación reproduce la regla del módulo de Mencía, no su salida. Y el
histórico de similitud pertenece al dominio de otro cliente, así que la
herramienta lo dice en vez de disfrazarlo de respuesta sobre este pedido.
"""

import re
from datetime import date

from modulos import auditoria, vigencia
from nucleo import autoridad as AUT
from nucleo import memoria as MEM

from . import flujo

# Las tres herramientas del esquema, en el orden en que las escribió Fabián.
ANALISIS = [
    {"id": "incongruencias", "nombre": "Análisis de incongruencias",
     "modulo": "Auditoría de pedidos · Juan Salas",
     "pregunta": "¿En qué exactamente no coinciden los documentos?"},
    {"id": "diligencia", "nombre": "Análisis de diligencia",
     "modulo": "Vigencia documental · Martín de Lucas",
     "pregunta": "¿Está en vigor el contrato con este cliente?"},
    {"id": "similitud", "nombre": "Análisis de similitud",
     "modulo": "Similitud de proyectos · Álvaro Subias",
     "pregunta": "¿Hemos hecho antes algo parecido?"},
]

# Las tres cosas que puede hacer el operario con una alarma delante.
ACCIONES = {
    "aceptar": ("Aceptar el valor del cliente",
                "Se da por buena la documentación de cliente y la orden se "
                "corrige a ese valor."),
    "corregir": ("Corregir con otro valor",
                 "Ni uno ni otro: el operario fija el valor correcto y queda "
                 "registrado quién lo hizo."),
    "escalar": ("Escalar a quien pueda decidir",
                "El operario no tiene autoridad sobre esta área, así que deja "
                "constancia y la alarma sigue abierta."),
}


# ---------------------------------------------------------------------------
# Flujo continuo
# ---------------------------------------------------------------------------

def _contractuales(docs):
    """
    Los documentos que se pueden situar en el tiempo.

    El criterio no lo pone esta pantalla: lo pone el módulo de vigencia, que es
    de quien es la pregunta. Un documento del que Martín sabe decir cuándo
    empieza o cuándo acaba es documentación contractual; una orden de
    fabricación, no.
    """
    salida = []
    for d in docs:
        campos = vigencia.extraer(d.get("texto") or "")
        if campos.get("fecha_inicio") or campos.get("fecha_caducidad"):
            salida.append({"doc": d, "campos": campos})
    return salida


def arrancar(docs, clasificar=None, modo="determinista"):
    """
    Lo que el sistema ya ha hecho antes de que nadie mire.

    Devuelve el estado de la consola: cuántos documentos ha leído, cuántos
    pedidos ha cerrado sin incidencias, qué alarmas quedan abiertas y qué
    documentación contractual hay en el expediente.
    """
    contratos = _contractuales(docs)
    del_pedido = [d for d in docs
                  if not any(c["doc"] is d for c in contratos)]

    resultados = flujo.procesar(del_pedido, clasificar, modo)
    alarmas, limpios, incompletos = [], [], []
    for r in resultados:
        if r["estado"] == "incidencia":
            peor = sorted(r["discrepancias"],
                          key=lambda d: flujo.ORDEN_SEVERIDAD.get(
                              d.get("severidad_esperada"), 9))[0]
            alarmas.append({**r, "principal": peor, "id": r["etiqueta"]})
        elif r["estado"] == "limpio":
            limpios.append(r)
        else:
            incompletos.append(r)

    return {
        "documentos": len(docs),
        "pedidos": len(resultados),
        "alarmas": alarmas,
        "limpios": limpios,
        "incompletos": incompletos,
        "contratos": contratos,
        "resultados": resultados,
    }


# ---------------------------------------------------------------------------
# Ontología, permisos y actuación
# ---------------------------------------------------------------------------

def categoria_de(alarma):
    """A qué área de la empresa afecta esta alarma."""
    from . import caso
    lecturas = caso.LECTURAS_DE_CAMPO.get(alarma["principal"]["campo"])
    return lecturas[0][0] if lecturas else None


def contexto_operario(rol, alarma, onto=None):
    """
    Quién es el operario, dónde está y qué le deja hacer ESTA alarma.

    Es el punto del esquema de Fabián que dice «la app chequea la ontología y
    determina quién es el operario». No es una comprobación de permisos genérica:
    depende de la alarma que se tenga delante, porque la misma persona puede
    cerrar una y no poder tocar otra.
    """
    onto = onto if onto is not None else AUT.cargar()
    cat = categoria_de(alarma)
    ficha = next((r for r in (onto or {}).get("roles", []) if r["rol"] == rol),
                 None)
    validar, motivo_v = AUT.puede(rol, cat, "validar", onto)
    proponer, motivo_p = AUT.puede(rol, cat, "proponer", onto)
    return {
        "rol": rol,
        "nivel": ficha["nivel"] if ficha else None,
        "area": ficha["area"] if ficha else None,
        "categoria": cat,
        "area_afectada": AUT.area_de(cat),
        "puede_validar": validar,
        "puede_proponer": proponer,
        "motivo": motivo_v if validar is not None else motivo_p,
        "manda": [r["rol"] for r in AUT.quien_manda_sobre(cat, onto)],
    }


def acciones_para(ctx):
    """
    Qué botones tiene sentido enseñarle a este operario.

    Un botón que no se puede pulsar no se enseña apagado: se sustituye por el
    que sí corresponde. Enseñar «cerrar» a quien no puede cerrar y que falle al
    pulsarlo es una forma cara de explicar los permisos.
    """
    if ctx["puede_validar"]:
        return ["aceptar", "corregir"]
    if ctx["puede_proponer"]:
        return ["aceptar", "corregir", "escalar"]
    return ["escalar"]


def contexto_del_caso(alarma):
    """
    Con qué se guarda el criterio para poder saber después si aplica.

    Es la columna «contexto de reutilización» del guion: cliente, producto, tipo
    de documento e incidencia. Sale de los documentos, no de una constante — si
    mañana entra otro cliente, el criterio no se le aplica solo.
    """
    cliente, producto = None, None
    for doc in alarma.get("grupo") or []:
        texto = doc.get("texto") or ""
        m = re.search(r"Cliente:\s*(.+)", texto)
        if m and not cliente:
            cliente = m.group(1).strip()
        m = re.search(r"Title:\s*(.+)", texto)
        if m and not producto:
            producto = m.group(1).strip()
    return {
        "cliente": cliente,
        "producto": producto,
        "tipo_documento": "orden de fabricación",
        "tipo_incidencia": "discrepancia entre documentos del mismo pedido",
        "campo": alarma["principal"]["campo"],
    }


def actuar(alarma, accion, ctx, valor=None, propuesta_previa=None,
           justificacion=None, diagnostico_clave=None):
    """
    El operario actúa. Devuelve qué ha pasado y si la alarma queda cerrada.

    La regla es la de siempre y no se duplica aquí: quien manda sobre el área
    cierra, quien sólo está en ella propone. Lo que cambia es que ahora la
    decisión, cuando se cierra, **se guarda** — y por eso la próxima incidencia
    de la misma clase llegará con su precedente puesto.
    """
    principal = alarma["principal"]

    # La justificación se exige ANTES de mirar los permisos, y no es un detalle
    # de orden: el guion dice «el encargado propone **y justifica**». Una
    # propuesta sin motivo le deja al que valida el mismo trabajo que si no la
    # hubiera, y además no se puede reutilizar como criterio.
    if not (justificacion or "").strip():
        return {
            "cerrada": False, "accion": accion, "propuesta_por": None,
            "falta_justificacion": True, "registro": None,
            "mensaje": ("Falta la justificación. Una decisión sin motivo no se "
                        "puede reutilizar como criterio: dentro de seis meses "
                        "quedaría el número y nadie sabría por qué."),
        }

    if accion == "escalar" or not ctx["puede_validar"]:
        return {
            "cerrada": False,
            "accion": accion,
            "propuesta_por": ctx["rol"] if ctx["puede_proponer"] else None,
            "justificacion": justificacion.strip(),
            "mensaje": (
                f"Queda constancia de que {ctx['rol']} ha revisado la alarma, "
                f"pero **no se cierra**: sobre {ctx['area_afectada']} manda "
                f"{', '.join(ctx['manda']) or 'nadie declarado'}."
                if ctx["puede_proponer"] else
                f"{ctx['rol']} no puede intervenir en esta alarma. {ctx['motivo']}."),
            "registro": None,
        }

    decidido = valor if accion == "corregir" else principal["valor_cliente"]
    diag = diagnostico(alarma) if diagnostico_clave is None else None
    registro = MEM.registrar(
        principal, accion, ctx["rol"], alarma["etiqueta"],
        propuesta_por=propuesta_previa,
        justificacion=justificacion.strip(),
        evidencias=[d["nombre"] for d in alarma.get("documentos") or []],
        contexto=contexto_del_caso(alarma),
        autorizados=ctx.get("manda") or [],
        diagnostico=diagnostico_clave or (diag or {}).get("clave"))
    return {
        "cerrada": True,
        "accion": accion,
        "valor": decidido,
        "propuesta_por": propuesta_previa,
        "mensaje": (f"Alarma cerrada por {ctx['rol']}. El pedido "
                    f"{alarma['etiqueta']} responde ya con "
                    f"{principal['etiqueta'].lower()} = {decidido}."),
        "registro": registro,
    }


# ---------------------------------------------------------------------------
# Las tres herramientas de análisis
# ---------------------------------------------------------------------------

def fragmento_de(texto, valor, ancho=90):
    """
    El trozo literal del documento donde aparece ese valor.

    Es lo que convierte una tabla en una evidencia. Un sistema que dice «la orden
    pone 30.000» y no enseña dónde lo pone está pidiendo que se le crea, y la
    tesis de este proyecto es justamente que nadie tenga que creerse nada.

    Se buscan las formas en que un mismo número puede estar escrito —30000,
    30.000, 30,000— porque el documento no tiene por qué haberlo escrito como lo
    normalizó el extractor. Si no se encuentra, se devuelve `None`: **no
    encontrarlo es un dato**, y aguas abajo se convierte en «evidencia
    insuficiente» en vez de en una cita inventada.
    """
    if valor is None or not texto:
        return None
    crudo = str(valor).strip()
    formas = {crudo}
    if crudo.replace(".", "").replace(",", "").isdigit():
        n = int(crudo.replace(".", "").replace(",", ""))
        formas |= {str(n), f"{n:,}".replace(",", "."), f"{n:,}"}
    for forma in sorted(formas, key=len, reverse=True):
        i = texto.find(forma)
        if i == -1:
            continue
        ini = max(0, i - ancho // 2)
        fin = min(len(texto), i + len(forma) + ancho // 2)
        trozo = " ".join(texto[ini:fin].split())
        return {"texto": trozo, "forma": forma,
                "linea": texto[:i].count("\n") + 1}
    return None


# Los cuatro estados de diagnóstico del guion de Fabián. El último no es un
# fallo del sistema: es la salida honesta cuando los tres primeros no encajan.
DIAGNOSTICOS = {
    "error_probable": (
        "Error probable",
        "Toda la documentación de cliente dice lo mismo y sólo la orden se "
        "aparta. Lo más probable es un error de transcripción al lanzarla."),
    "cambio_documentado": (
        "Cambio documentado",
        "La documentación de cliente no es unánime: hay un documento que "
        "respalda el valor de la orden. Puede ser un cambio acordado y no un "
        "error."),
    "evidencia_insuficiente": (
        "Evidencia insuficiente",
        "No se ha podido localizar el valor en el texto de alguno de los "
        "documentos, así que la discrepancia se declara pero no se sostiene "
        "con una cita."),
    "requiere_humana": (
        "Requiere decisión humana",
        "El sistema puede decir qué no cuadra, pero no cuál de los dos valores "
        "debe prevalecer. Eso lo decide una persona con autoridad."),
}


def diagnostico(alarma, discrepancia=None):
    """
    Qué clase de problema parece ser, con el motivo.

    No es una opinión: sale de comparar la documentación de cliente entre sí. Si
    el presupuesto y el pedido dicen lo mismo y sólo la orden se aparta, lo
    probable es un error al lanzarla. Si uno de los documentos de cliente
    respalda el valor de la orden, puede ser un cambio acordado — y entonces
    acusar de error sería precipitado.

    Devuelve siempre además `requiere_humana`, porque ninguno de los tres
    diagnósticos anteriores decide cuál de los dos valores vale.
    """
    d = discrepancia or alarma["principal"]
    campo = d["campo"]
    grupo = alarma.get("grupo") or []

    apoyos = {"cliente": [], "orden": []}
    faltan = []
    for doc in grupo:
        tipo = doc.get("tipo") or auditoria.clasificar(doc["texto"])
        campos = (auditoria.campos_orden(doc["texto"]) if tipo == "orden"
                  else auditoria.campos_cliente(doc["texto"]))
        valor = campos.get(campo)
        if valor is None:
            continue
        frag = fragmento_de(doc["texto"], valor)
        if frag is None:
            faltan.append(doc.get("nombre"))
        entrada = {"documento": doc.get("nombre"), "tipo": tipo,
                   "valor": valor, "fragmento": frag}
        if str(valor) == str(d["valor_orden"]):
            apoyos["orden"].append(entrada)
        elif str(valor) == str(d["valor_cliente"]):
            apoyos["cliente"].append(entrada)

    # El pedido de cliente manda sobre el presupuesto como cita principal: es el
    # documento con el que el cliente encarga, no con el que se le ofertó.
    orden_tipos = {"pedido_cliente": 0, "presupuesto": 1, "orden": 0}
    for lado in apoyos.values():
        lado.sort(key=lambda e: orden_tipos.get(e["tipo"], 9))

    de_cliente_con_la_orden = [e for e in apoyos["orden"]
                               if e["tipo"] != "orden"]
    if faltan:
        clave = "evidencia_insuficiente"
    elif de_cliente_con_la_orden:
        clave = "cambio_documentado"
    elif len(apoyos["cliente"]) >= 1:
        clave = "error_probable"
    else:
        clave = "requiere_humana"

    etiqueta, por_que = DIAGNOSTICOS[clave]
    return {
        "clave": clave, "etiqueta": etiqueta, "por_que": por_que,
        "apoyan_cliente": apoyos["cliente"],
        "apoyan_orden": apoyos["orden"],
        "sin_fragmento": faltan,
        # Siempre, y no como excusa: el sistema puede decir qué no cuadra y no
        # cuál vale. Es la frase que más le va a servir a Íñigo delante de un
        # cliente que pregunte si esto sustituye a alguien.
        "y_ademas": DIAGNOSTICOS["requiere_humana"],
    }


def analisis_incongruencias(alarma, respuesta_modulo=""):
    """Herramienta 1 — el detalle de la discrepancia, contrastado y con citas."""
    from . import caso
    reportados, avisos = auditoria.interpretar(respuesta_modulo or "",
                                               "determinista")
    obs = caso.observar(alarma["discrepancias"], reportados)
    return {"observacion": obs, "avisos": avisos, "reportados": reportados,
            "hay_salida": bool((respuesta_modulo or "").strip()),
            "diagnostico": diagnostico(alarma)}


def analisis_diligencia(contratos, fecha=None):
    """
    Herramienta 2 — ¿está en vigor el contrato con este cliente?

    Si no hay documentación contractual en el expediente, se dice. «No aplica a
    este caso» es una respuesta, y bastante mejor que un panel vacío.
    """
    fecha = fecha or date.today()
    if not contratos:
        return {"aplica": False,
                "motivo": "No hay documentación contractual en este expediente: "
                          "ningún documento de la bandeja se puede situar en el "
                          "tiempo."}
    salida = []
    for c in contratos:
        campos = c["campos"]
        estado, por_que = vigencia.estado_esperado(campos, fecha)
        dias = ((campos["fecha_caducidad"] - fecha).days
                if campos.get("fecha_caducidad") else None)
        salida.append({
            "nombre": c["doc"].get("nombre"),
            "estado": estado,
            "etiqueta": vigencia.ESTADOS.get(estado, estado),
            "por_que": por_que,
            "inicio": campos.get("fecha_inicio"),
            "fin": campos.get("fecha_caducidad"),
            "dias": dias,
            "preaviso": campos.get("preaviso_dias"),
            # El aviso útil de verdad: si hay que denunciar el contrato con N
            # días y quedan menos de N + margen, la ventana se está cerrando.
            "preaviso_urgente": bool(
                campos.get("preaviso_dias") and dias is not None
                and 0 < dias <= campos["preaviso_dias"] + 30),
        })
    return {"aplica": True, "fecha": fecha, "documentos": salida}


def analisis_similitud(ruta_ejemplo=None):
    """
    Herramienta 3 — ¿hemos hecho antes algo parecido?

    Y aquí el sistema tiene que ser honesto: el histórico que hay cargado es el
    de otro cliente y otro dominio —intercambiadores de calor, no libros—, así
    que **no puede contestar la pregunta sobre este pedido**. Lo dice, y enseña
    cómo responde el módulo sobre su propio caso, que es lo que se puede
    sostener. Disfrazar la salida de un dominio como si fuera del otro sería
    exactamente el tipo de cosa que este proyecto existe para detectar.
    """
    import json
    from pathlib import Path

    from modulos import similitud

    ruta = Path(ruta_ejemplo or (flujo.__file__ and
                                 Path(__file__).resolve().parent / "datos" /
                                 "similitud" / "caso1_syn0047_acierto.json"))
    if not ruta.is_file():
        return {"aplica": False,
                "motivo": "No hay histórico de proyectos cargado."}
    datos, _ = similitud.interpretar(ruta.read_text(encoding="utf-8"))
    if not datos:
        return {"aplica": False, "motivo": "El histórico no se ha podido leer."}
    return {
        "aplica": False,
        "motivo": ("El histórico cargado es de otro dominio —equipos "
                   "industriales, no libros—, así que la herramienta **no puede "
                   "contestar sobre este pedido**. Lo que sí se puede enseñar es "
                   "cómo responde el módulo sobre su propio caso."),
        "ejemplo": {
            "consulta": datos.get("pedido_consultado"),
            "resultados": (datos.get("resultados") or [])[:3],
            "descartados": len(datos.get("descartados") or []),
        },
    }
