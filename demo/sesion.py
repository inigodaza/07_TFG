"""
La cadena de custodia de una decisión, con dos escalones.

Qué es esto y qué NO es
------------------------
Esto **no simula el módulo de Mencía**. Reproduce la *regla* que su módulo aplica
—quien está en el área propone, quien manda sobre ella valida— para poder
enseñarla funcionando y, sobre todo, para poder comprobarla contra la matriz de
Pablo. Es un banco de pruebas de la regla, no una imitación de su software.

La diferencia importa y va escrita en la pantalla: nada de lo que pase aquí
puntúa contra Mencía. Cuando llegue su exportación del pedido, el mismo cruce se
ejecuta sobre datos suyos y entonces sí emite veredicto. Un evaluador que
puntuara a alguien contra una maqueta hecha por él mismo estaría cometiendo el
error que le reprocha a los demás.

Por qué dos escalones y no uno
-------------------------------
Es lo que se ve en el vídeo del módulo: el administrativo comercial resuelve la
contradicción y su decisión **no se llega a guardar del todo**; queda como
propuesta. Cuando entra el director comercial le salta un aviso —«ya corregido
por administrativo comercial»— y es él quien la cierra.

Esa es exactamente la pregunta que ningún módulo puede contestar solo. Mencía
sabe quién tocó qué. Pablo declara quién puede tocar qué. Sólo aquí están los
dos.
"""

from nucleo import autoridad as AUT

ABIERTA = "abierta"
PROPUESTA = "propuesta"
VALIDADA = "validada"

INICIAL = {"fase": ABIERTA, "propuesta_por": None, "validada_por": None,
           "historial": []}


def nueva():
    """Un estado limpio. Se devuelve copiado para no compartir el historial."""
    return {"fase": ABIERTA, "propuesta_por": None, "validada_por": None,
            "historial": []}


def _anota(estado, quien, que, por_que):
    estado["historial"] = estado["historial"] + [
        {"quien": quien, "que": que, "por_que": por_que}]


def entrar(estado, rol, categoria, onto=None):
    """
    Alguien inicia sesión con un puesto e intenta resolver la contradicción.

    Devuelve `(nuevo_estado, resultado)`. El resultado dice qué ha pasado y por
    qué, con el motivo que da la matriz de autoridad — nunca uno escrito aquí,
    para que cambiar el organigrama cambie el comportamiento sin tocar código.
    """
    estado = dict(estado or nueva())
    puede_validar, motivo_v = AUT.puede(rol, categoria, "validar", onto)
    puede_proponer, motivo_p = AUT.puede(rol, categoria, "proponer", onto)

    aviso = None
    if estado["fase"] == PROPUESTA and estado["propuesta_por"] != rol:
        # El aviso que salta al director en el módulo real.
        aviso = (f"Ya corregido por {estado['propuesta_por']}, pendiente de "
                 f"validación.")

    # 1 · No se reconoce el puesto o la categoría: no se puede decidir nada.
    if puede_validar is None and puede_proponer is None:
        return estado, {"accion": "indeterminada", "aviso": aviso,
                        "motivo": motivo_v or motivo_p,
                        "mensaje": "No se puede saber si este puesto podía "
                                   "intervenir, así que no se le atribuye nada."}

    # 2 · Ya está cerrada.
    if estado["fase"] == VALIDADA:
        return estado, {"accion": "cerrada", "aviso": aviso, "motivo": "",
                        "mensaje": (f"La contradicción ya la validó "
                                    f"{estado['validada_por']}. A partir de aquí "
                                    f"cualquier consulta sobre este pedido "
                                    f"recibe el valor decidido y no vuelve a "
                                    f"mostrar el conflicto.")}

    # 3 · Ni siquiera es de su área.
    if not puede_proponer:
        return estado, {"accion": "rechazada", "aviso": aviso, "motivo": motivo_p,
                        "mensaje": ("Este puesto no puede intervenir en esta "
                                    "contradicción.")}

    # 4 · Manda sobre el área: valida y cierra.
    if puede_validar:
        estado["fase"] = VALIDADA
        estado["validada_por"] = rol
        _anota(estado, rol, "valida", motivo_v)
        cerrada_sobre = (f" Se cierra sobre la propuesta de "
                         f"{estado['propuesta_por']}."
                         if estado["propuesta_por"] else
                         " La cierra directamente, sin propuesta previa.")
        return estado, {"accion": "validacion", "aviso": aviso, "motivo": motivo_v,
                        "mensaje": ("Decisión validada y guardada." + cerrada_sobre)}

    # 5 · Está en el área pero no manda: propone, y ahí se queda.
    if estado["fase"] == PROPUESTA and estado["propuesta_por"] == rol:
        return estado, {"accion": "repetida", "aviso": aviso, "motivo": motivo_v,
                        "mensaje": ("La propuesta ya estaba registrada a su "
                                    "nombre. Volver a entrar no la asciende: "
                                    "hace falta alguien con autoridad sobre el "
                                    "área.")}
    estado["fase"] = PROPUESTA
    estado["propuesta_por"] = rol
    _anota(estado, rol, "propone", motivo_v)
    return estado, {"accion": "propuesta", "aviso": aviso, "motivo": motivo_v,
                    "mensaje": ("Queda registrada como **propuesta pendiente de "
                                "validación**: no se llega a guardar del todo. "
                                "Hasta que alguien con autoridad sobre el área "
                                "la valide, el conflicto sigue vivo.")}


def resumen(estado, categoria=None, onto=None):
    """Cómo está la cadena ahora mismo, para pintarla y para comprobarla."""
    estado = estado or nueva()
    manda = [r["rol"] for r in AUT.quien_manda_sobre(categoria, onto)] \
        if categoria else []
    return {
        "fase": estado["fase"],
        "propuesta_por": estado["propuesta_por"],
        "validada_por": estado["validada_por"],
        "cerrada": estado["fase"] == VALIDADA,
        "quien_puede_cerrarla": manda,
        "pasos": len(estado["historial"]),
    }
