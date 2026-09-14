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

# Lo que puede hacer el operario con una alarma delante.
#
# Son cuatro y no tres porque faltaba la más interesante. Con «aceptar el valor
# del cliente» y «corregir» se pueden resolver los errores, pero no se puede
# decir lo que un encargado dice diez veces al día: **«esto es tolerable, tira
# para adelante»**. Una cubierta de 250 g donde el cliente pidió 240 no es un
# error de nadie: es una diferencia que alguien con autoridad tolera. Sin esa
# cuarta opción había que fingirla escribiendo 250 a mano en «corregir», y en
# pantalla se leía como una corrección lo que era exactamente lo contrario.
ACCIONES = {
    "aceptar": ("Aceptar el valor del cliente",
                "Se da por buena la documentación de cliente y la orden se "
                "corrige a ese valor."),
    # «Tolerable» es la palabra de Juan, y por eso es la que se usa.
    #
    # Confirmado por él el 14 sep sobre este mismo caso —240 g contra 250 en
    # cubierta—: «sí, en el vídeo creo que le doy a tolerable, y eso lo deja
    # marcado; y si vuelve a salir ese mismo aviso en otro pedido sale como que
    # es un fallo tolerable». Su módulo ya tiene el concepto y ya tiene la
    # memoria. Poner aquí «dar por buena la orden» habría sido inventar
    # vocabulario nuevo para algo que en GraphyCems ya se llama de una manera.
    "dar_por_buena": ("Marcar como tolerable",
                      "La diferencia no es un error que corregir: se fabrica con "
                      "lo que dice la orden y queda constancia de quién la "
                      "toleró."),
    "corregir": ("Corregir con otro valor",
                 "Ni uno ni otro: el operario fija el valor correcto y queda "
                 "registrado quién lo hizo."),
    "escalar": ("Escalar a quien pueda decidir",
                "El operario no tiene autoridad sobre esta área, así que deja "
                "constancia y la alarma sigue abierta."),
}

# Cómo llama el módulo de Juan a cada nivel de gravedad.
#
# Su salida sobre el pedido 42805 —el mismo caso que enseña la demo— no da una
# lista de errores: da DOS categorías, «INCONGRUENCIA» y «A REVISAR», y mete el
# gramaje en la segunda. Nuestra escala interna de severidad no cambia; lo que
# cambia es cómo se rotula en pantalla, porque el nombre de una gravedad lo pone
# quien audita y no quien evalúa.
ETIQUETA_SEVERIDAD = {
    "critica": "INCONGRUENCIA",
    "alta": "INCONGRUENCIA",
    "media": "A REVISAR",
    "menor": "A REVISAR",
}


def etiqueta_severidad(discrepancia):
    return ETIQUETA_SEVERIDAD.get(
        (discrepancia.get("severidad_esperada") or "").lower(),
        (discrepancia.get("severidad_esperada") or "—").upper())


def nota_de_revision(discrepancia):
    """
    Por qué una diferencia sale «a revisar» y no como incongruencia.

    La hipótesis del redondeo es de Juan, literal de la salida de su módulo
    sobre el pedido 42805: «podría ser el redondeo estándar de GraphyCems, no
    necesariamente un error». No la he deducido yo, y por eso se puede enseñar
    sin asterisco. `None` cuando la diferencia no es de las pequeñas.
    """
    if (discrepancia.get("severidad_esperada") or "").lower() not in ("menor",
                                                                     "media"):
        return None
    if "gramaje" in (discrepancia.get("campo") or ""):
        return ("Podría ser el **redondeo estándar de GraphyCems**, no "
                "necesariamente un error. Si es tolerable lo decide producción, "
                "no el sistema.")
    return ("Diferencia pequeña: puede no ser un error. Si es tolerable lo "
            "decide quien manda sobre el área, no el sistema.")


def etiqueta_accion(accion, ctx):
    """
    Cómo se llama el botón para QUIEN lo tiene delante.

    Mencía lo dijo con estas palabras el 14 sep: «el encargado no puede
    corregir; lo único que puede hacer es proponérselo al superior». Por dentro
    el sistema ya hacía justo eso —su pulsación queda como propuesta y no cierra
    nada— pero el botón le decía «Corregir con otro valor», que en su pantalla
    es sencillamente falso. Un botón que nombra algo que quien lo pulsa no puede
    hacer enseña mal el permiso justo donde más importa que se entienda.
    """
    etiqueta = ACCIONES[accion][0]
    if accion == "escalar" or ctx.get("puede_validar"):
        return etiqueta
    return f"Proponer: {etiqueta[0].lower()}{etiqueta[1:]}"


# Las dos que cierran ACEPTANDO la diferencia en vez de arreglarla.
#
# Importan aparte porque son las dos en las que tiene sentido preguntar si lo
# decidido vale para la próxima: aceptar es decir «esta diferencia está bien», y
# eso es lo que se puede generalizar. Corregir a un tercer valor es resolver un
# caso concreto.
ACEPTACIONES = ("aceptar", "dar_por_buena")


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


def lotes(docs):
    """
    Los documentos repartidos en lotes tal como llegarían: por carpeta.

    En una empresa la documentación no entra de golpe ni ordenada por pedido:
    entra por tandas, según la va mandando el cliente o la va generando
    producción. Cada carpeta de la bandeja es una tanda, y poder recibirlas por
    separado es lo que permite enseñar el sistema **reaccionando** en vez de
    enseñar un resultado ya cocinado.
    """
    from pathlib import Path
    salida = {}
    for d in docs:
        ruta = d.get("ruta")
        carpeta = Path(ruta).parent.name if ruta else "sueltos"
        salida.setdefault(carpeta, []).append(d)
    return dict(sorted(salida.items()))


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
            # UNA INCONGRUENCIA, UNA ALARMA.
            #
            # Antes un pedido con dos diferencias producía una sola alarma: la
            # más grave mandaba y el resto viajaba de paquete como «y 1
            # diferencia menor». Eso obliga a resolverlas juntas, y es
            # justamente lo que no se puede hacer: en el pedido 90002 la
            # cantidad (3.000 contra 30.000) es un error que hay que corregir, y
            # el gramaje de cubierta (240 contra 250) puede ser perfectamente
            # asumible. Son dos decisiones distintas, de dos personas
            # potencialmente distintas, y cada una deja su propio criterio.
            #
            # El pedido sigue siendo `etiqueta`, porque es lo que se enseña. Lo
            # que cambia es que la clave única pasa a ser `id`, pedido + campo.
            for d in sorted(r["discrepancias"],
                            key=lambda x: flujo.ORDEN_SEVERIDAD.get(
                                x.get("severidad_esperada"), 9)):
                alarmas.append({**r, "principal": d, "discrepancias": [d],
                                "id": f'{r["etiqueta"]}·{d["campo"]}'})
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


def contexto_operario(rol, alarma, onto=None, persona=None):
    """
    Quién es el operario, dónde está y qué le deja hacer ESTA alarma.

    Es el punto del esquema de Fabián que dice «la app chequea la ontología y
    determina quién es el operario». No es una comprobación de permisos genérica:
    depende de la alarma que se tenga delante, porque la misma persona puede
    cerrar una y no poder tocar otra.

    `persona` es quien ha iniciado sesión, y **no cambia ni un permiso**: la
    autoridad la lleva el puesto, no el nombre. Sirve sólo para firmar. Hoy la
    consola no la usa —se entra por puesto, no por persona— y el registro firma
    con la fila de la matriz; el día que la empresa conecte su directorio, el
    registro podrá guardar las dos cosas, que son las dos que hacen falta a los
    seis meses: a quién preguntarle por qué, y con qué autoridad lo hizo.
    """
    onto = onto if onto is not None else AUT.cargar()
    cat = categoria_de(alarma)
    ficha = next((r for r in (onto or {}).get("roles", []) if r["rol"] == rol),
                 None)
    validar, motivo_v = AUT.puede(rol, cat, "validar", onto)
    proponer, motivo_p = AUT.puede(rol, cat, "proponer", onto)
    return {
        "rol": rol,
        "persona": persona,
        "quien": f"{persona} ({rol})" if persona else rol,
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
        return ["aceptar", "dar_por_buena", "corregir"]
    if ctx["puede_proponer"]:
        return ["aceptar", "dar_por_buena", "corregir", "escalar"]
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
           justificacion=None, diagnostico_clave=None, es_criterio=False):
    """
    El operario actúa. Devuelve qué ha pasado y si la alarma queda cerrada.

    La regla es la de siempre y no se duplica aquí: quien manda sobre el área
    cierra, quien sólo está en ella propone.

    Todo lo que se cierra queda anotado —eso es el historial— y `es_criterio`
    decide si además **vuelve** la próxima vez que aparezca una incidencia de la
    misma clase. No lo decide el sistema: se le pregunta a quien cierra, y sólo
    cuando la acción es una aceptación. Aceptar es decir «esta diferencia está
    bien», y eso es lo que se puede generalizar; corregir a un tercer valor
    resuelve un caso concreto y no dice nada de los siguientes.
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

    # Corregir sin decir a qué no es corregir.
    #
    # Va aquí, junto a la justificación y antes de los permisos, por el mismo
    # motivo: son las dos formas de cerrar una alarma dejando el hueco donde
    # debería estar la decisión. Antes se cerraba igual y el pedido acababa
    # respondiendo «cantidad = », que es peor que no haberla atendido — la cola
    # queda limpia y el dato, vacío.
    if accion == "corregir" and not str(valor or "").strip():
        return {
            "cerrada": False, "accion": accion, "propuesta_por": None,
            "falta_valor": True, "registro": None,
            "mensaje": ("Falta el valor correcto. «Corregir» sin decir a qué "
                        "cerraría la alarma dejando el pedido sin dato: "
                        "escríbelo en «Corregir con otro valor», o acepta el "
                        "valor del cliente si es el bueno."),
        }

    if accion == "escalar" or not ctx["puede_validar"]:
        # La propuesta TAMBIÉN se anota.
        #
        # Antes sólo quedaba en la pantalla del que validaba después. Eso deja
        # fuera del registro justo lo que más cuesta reconstruir a los seis
        # meses: que alguien miró la incidencia, dijo qué haría y por qué, y no
        # pudo cerrarla. Trabajo que no consta es trabajo que no se hizo, y el
        # encargado de turno es el que más veces está en esa situación.
        registro = None
        if ctx["puede_proponer"]:
            registro = MEM.registrar(
                principal, accion, None, alarma["etiqueta"],
                propuesta_por=ctx["quien"],
                justificacion=justificacion.strip(),
                evidencias=[d["nombre"] for d in alarma.get("documentos") or []],
                contexto=contexto_del_caso(alarma),
                autorizados=ctx.get("manda") or [],
                diagnostico=diagnostico_clave,
                valor_decidido=(valor if accion == "corregir" else
                                principal["valor_orden"]
                                if accion == "dar_por_buena" else
                                principal["valor_cliente"]
                                if accion == "aceptar" else None),
                fase="propuesta")
        return {
            "cerrada": False,
            "accion": accion,
            "propuesta_por": ctx["quien"] if ctx["puede_proponer"] else None,
            "justificacion": justificacion.strip(),
            "mensaje": (
                f"Queda constancia de que {ctx['quien']} ha revisado la alarma, "
                f"pero **no se cierra**: sobre {ctx['area_afectada']} manda "
                f"{', '.join(ctx['manda']) or 'nadie declarado'}."
                if ctx["puede_proponer"] else
                f"{ctx['quien']} no puede intervenir en esta alarma. "
                f"{ctx['motivo']}."),
            "registro": registro,
        }

    # Qué valor prevalece, según lo que se haya decidido.
    decidido = {"aceptar": principal["valor_cliente"],
                "dar_por_buena": principal["valor_orden"],
                "corregir": valor}.get(accion, principal["valor_cliente"])
    # Sólo una aceptación puede dejar criterio; una corrección, no (ver arriba).
    criterio = bool(es_criterio) and accion in ACEPTACIONES
    diag = diagnostico(alarma) if diagnostico_clave is None else None
    registro = MEM.registrar(
        principal, accion, ctx["quien"], alarma["etiqueta"],
        propuesta_por=propuesta_previa,
        justificacion=justificacion.strip(),
        evidencias=[d["nombre"] for d in alarma.get("documentos") or []],
        contexto=contexto_del_caso(alarma),
        autorizados=ctx.get("manda") or [],
        diagnostico=diagnostico_clave or (diag or {}).get("clave"),
        es_criterio=criterio, valor_decidido=decidido)
    cola = ((" Queda marcado como **fallo tolerable**: si vuelve a salir este "
             "mismo aviso en otro pedido del mismo tipo de documento, saldrá ya "
             "como tolerable."
             if accion == "dar_por_buena" else
             " Queda además como criterio: la próxima incidencia de esta clase "
             "sobre el mismo tipo de documento llegará con esta decisión "
             "puesta.")
            if criterio else
            " Queda como decisión de este caso, **no** como criterio: no se "
            "propondrá en los siguientes.")
    return {
        "cerrada": True,
        "accion": accion,
        "valor": decidido,
        "es_criterio": criterio,
        "propuesta_por": propuesta_previa,
        "mensaje": (f"Alarma cerrada por {ctx['quien']}. El pedido "
                    f"{alarma['etiqueta']} responde ya con "
                    f"{principal['etiqueta'].lower()} = {decidido}." + cola),
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


# Los pasos que da el sistema al auditar una tanda. Están aquí, enumerados,
# porque cada uno ocurre de verdad: no es una barra de progreso decorativa.
PASOS_AUDITORIA = [
    ("Leyendo los documentos", "capa de texto del PDF, u OCR si no la tiene"),
    ("Reconociendo de qué tipo es cada uno",
     "por señales del contenido, no por el nombre del fichero"),
    ("Extrayendo los campos", "cantidad, páginas, gramajes, ISBN y formato"),
    ("Agrupando por pedido", "usando el ISBN, que es lo que de verdad los une"),
    ("Contrastando cada pedido consigo mismo",
     "campo a campo, entre la orden y la documentación de cliente"),
]


def cotejo(resultado):
    """
    Campo a campo, qué dice cada lado del pedido y si coinciden.

    Sirve igual cuando hay incongruencia y cuando no, y esto último es lo que
    faltaba: un «sin incidencias» que no dice qué se ha mirado no tranquiliza a
    nadie. Lo que tranquiliza es ver los campos comparados.
    """
    ctx = resultado.get("contexto") or {}
    cliente, orden = ctx.get("cliente") or {}, ctx.get("orden") or {}
    rangos = cliente.get("rangos") or {}
    discrepantes = {d["campo"] for d in resultado.get("discrepancias") or []}

    filas = []
    for clave, (etiqueta, _sev) in auditoria.CAMPOS.items():
        a, b = cliente.get(clave), orden.get(clave)
        if a is None and b is None:
            continue
        nota = ""
        if a is None or b is None:
            # Que falte un lado no es que coincida: es que no se ha podido
            # comparar, y decirlo es la mitad del valor de esta tabla.
            coincide = None
            nota = ("sólo consta en la orden" if a is None
                    else "sólo consta en la documentación de cliente")
        elif clave in rangos:
            coincide = clave not in discrepantes
            nota = ("dentro de la horquilla que pide el cliente" if coincide
                    else "fuera de la horquilla")
        else:
            coincide = clave not in discrepantes
        filas.append({"campo": etiqueta,
                      "cliente": "—" if a is None else a,
                      "orden": "—" if b is None else b,
                      "coincide": coincide is not False,
                      "comparado": coincide is not None,
                      "nota": nota})
    return filas


def cuadros_del_caso(alarma_o_resultado, estado, con_incidencia=True):
    """
    Lo que cada una de las tres herramientas sabe de este caso.

    Es el panel que pide Fabián: un centro de control, no seis aplicaciones. La
    que le corresponde a la incidencia trae **los datos dentro** —la
    discrepancia con sus dos cifras— y las otras dos dicen qué harían y por qué
    no aplican aquí. Verlas apagadas es lo que hace entender que había dónde
    elegir y que eligió el sistema.
    """
    r = alarma_o_resultado
    a1, a2, a3 = ANALISIS

    lineas = []
    if con_incidencia and r.get("principal"):
        p = r["principal"]
        lineas = [
            ("Pedido", r.get("etiqueta", ""), False),
            (f'{p["etiqueta"]} · cliente', str(p["valor_cliente"]), False),
            (f'{p["etiqueta"]} · orden', str(p["valor_orden"]), True),
        ]
        if len(r.get("discrepancias") or []) > 1:
            lineas.append(("Otras diferencias",
                           str(len(r["discrepancias"]) - 1), False))

    dil = analisis_diligencia(estado.get("contratos") or [])
    if dil["aplica"]:
        d = dil["documentos"][0]
        v_dil = (f'Contrato **{d["etiqueta"].lower()}**'
                 + (f', quedan {d["dias"]} días' if d["dias"] is not None else "")
                 + ".")
    else:
        v_dil = "No hay documentación contractual en este expediente."

    return [
        {"id": a1["id"], "nombre": a1["nombre"], "modulo": a1["modulo"],
         "descripcion": "Compara la orden de fabricación con la documentación "
                        "de cliente del mismo pedido y señala en qué campo "
                        "exactamente no coinciden.",
         "activo": con_incidencia,
         "estado": "Le corresponde" if con_incidencia else "Sin incidencias",
         "lineas": lineas,
         "veredicto": (None if con_incidencia else
                       "Los documentos de este pedido dicen lo mismo.")},
        {"id": a2["id"], "nombre": a2["nombre"], "modulo": a2["modulo"],
         "descripcion": "Sitúa en el tiempo los contratos y anexos del cliente: "
                        "si están en vigor, cuándo vencen y con cuánto preaviso "
                        "hay que denunciarlos.",
         "activo": False, "estado": "Consultable",
         "veredicto": v_dil},
        {"id": a3["id"], "nombre": a3["nombre"], "modulo": a3["modulo"],
         "descripcion": "Busca en el histórico trabajos parecidos al que se "
                        "acaba de encargar, para reaprovechar lo que ya se "
                        "hizo y no presupuestar dos veces lo mismo.",
         # «Pendiente de conectar», y no «no puede contestar».
         #
         # Dicen lo mismo de distinta manera y la diferencia importa en una
         # demostración: «no puede contestar» suena a que el módulo de Álvaro
         # falla, y no falla — lo que pasa es que su histórico es de otro
         # dominio (equipos industriales, no libros) y todavía no está
         # enchufado a este expediente. El matiz no es cosmético: aquí se está
         # hablando del trabajo de un compañero delante de gente.
         "activo": False, "estado": "Pendiente de conectar",
         "veredicto": "Todavía no está enchufado a este expediente. El "
                      "histórico disponible es de otro dominio —equipos "
                      "industriales, no libros—, así que cuando se conecte "
                      "hará falta también el histórico de artes gráficas."},
    ]


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
