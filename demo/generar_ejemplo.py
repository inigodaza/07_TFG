"""
Genera la bandeja de documentos sintéticos con la que arranca la demo.

Por qué existe
--------------
Los documentos reales del pedido 42805 son documentación de cliente y no se
versionan, así que en un despliegue limpio la demo no tenía con qué arrancar:
pedía documentos y ahí se quedaba. Una demo que sólo funciona en el portátil de
quien la escribió no es una demo.

Esto fabrica **dos pedidos completos y un contrato marco**, inventados de
principio a fin —editorial, títulos e ISBN no existen— con la misma estructura
que los reales:

    Pedido 90001 · limpio            presupuesto + pedido de cliente + orden
    Pedido 90002 · dos diferencias   presupuesto + pedido de cliente + orden
    expediente   · contrato marco del cliente, vigente hasta 2027

Tres cosas distintas dependen de esta bandeja, y por eso es así:

**Que haya un pedido limpio** es lo que demuestra que el sistema distingue. Una
alarma que salta en el primer documento que se mira no demuestra nada.

**Que haya dos pedidos con el MISMO error** es lo que permite enseñar la
memoria. Al resolver el primero el sistema registra la decisión; cuando aparece
el segundo, la reconoce y ofrece el precedente. Con un solo caso no habría nada
que recordar.

**Que haya un contrato** es lo que le da algo real que decir a la herramienta de
diligencia: es el único documento de la bandeja que se puede situar en el
tiempo, y ése es precisamente el criterio del módulo de vigencia.

Van marcados en la primera línea de cada página. Un documento sintético que se
pudiera confundir con uno de cliente sería un problema, no una comodidad.

    python demo/generar_ejemplo.py
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

DESTINO = Path(__file__).resolve().parent / "datos" / "ejemplo"

AVISO = "DOCUMENTO SINTETICO DE PRUEBA - editorial, titulo e ISBN inventados"


def orden(of, isbn, titulo, cantidad, paginas, gr_cubierta):
    return f"""{AVISO}

ORDEN DE FABRICACION                          O.F. Nº {of}

Cliente: Editorial Ficticia del Norte S.L.
Formato: 170 x 240

{isbn} 170 x 240

Cantidad:                                     Paginas:
  {titulo:<44}{cantidad} {paginas}

Interiores 4 4 offset blanco {paginas}  {cantidad}  {cantidad}
  Papel offset ahuesado    170x240   90   Interiores  1/1
  Carton estucado brillo   170x240   {gr_cubierta}  Cubiertas  4/0

Encuadernacion: rustica fresada
Impresion: offset

LOGISTICA
Cantidad: {cantidad}
Destino: almacen central
"""


def cliente(isbn, titulo, cantidad, paginas, gr_cubierta):
    return f"""{AVISO}

PURCHASE ORDER

We hereby order the following title:

RE: {isbn}

Title: {titulo}
Quantity: {cantidad} copies
Extent: {paginas} pp
Trimmed Size: 170 x 240mm
Text Paper: 90 gsm
Cover Material: {gr_cubierta} gsm
Binding: limp

Delivery date: 30/11/2026
Delivery address: Editorial Ficticia del Norte S.L.
"""


def presupuesto(isbn, titulo, cantidad, paginas, gr_cubierta):
    return f"""{AVISO}

QUOTATION

Ref: {isbn}
Title: {titulo}

Please find herewith our prices for the above title.

{cantidad} cps. = unit price on application
Extent {paginas} pp
TPS 170 x 240mm
Inside: 90 gsm offset
Cover: {gr_cubierta} gsm board

Valid for 60 days. Our prices exclude carriage.
"""


CONTRATO = f"""{AVISO}

CONTRATO MARCO DE SERVICIOS DE IMPRESION

ENTRE: Artes Graficas Ficticias S.A., como PRESTADOR
Y: Editorial Ficticia del Norte S.L., como CLIENTE

En Zaragoza, a uno de marzo de 2.024.

EXPONEN

Que ambas partes acuerdan regular las condiciones de los encargos de impresion
que el CLIENTE curse al PRESTADOR durante la vigencia del presente contrato.

CLAUSULAS

PRIMERA. Objeto. El PRESTADOR se obliga a la impresion y encuadernacion de las
obras que el CLIENTE le encargue mediante orden de fabricacion.

SEGUNDA. Duracion. El plazo de duracion del presente contrato sera de tres anos,
comenzando el uno de marzo de 2.024 y finalizando el uno de marzo de 2.027.

TERCERA. Prorroga. Llegado el vencimiento, el contrato se prorrogara tacitamente
por periodos anuales salvo denuncia de cualquiera de las partes con un preaviso
de 60 dias de antelacion.

CUARTA. Precio. Los precios se fijaran en cada presupuesto y tendran la vigencia
que en el mismo se indique.
"""


# Los dos pedidos de la bandeja.
#
# Dos pedidos, y el segundo con DOS diferencias que no se deciden igual. Es la
# pareja del caso real 42805: una cantidad diez veces mayor —que hay que
# corregir— y una cubierta diez gramos más gruesa, que el módulo de auditoría
# saca «a revisar» porque podría ser el redondeo estándar de la casa.
#
# Hubo un tercer pedido, el 90003, que repetía el error de cantidad (8.000 de
# 800) para poder enseñar el precedente volviendo. Se ha quitado: era inventado
# de principio a fin y no se parecía a nada que Juan haya visto. El precio de
# quitarlo es que en la bandeja de ejemplo ya no hay un segundo caso de la misma
# clase, así que el criterio se puede ver GUARDARSE pero no VOLVER. Para verlo
# volver hace falta un segundo pedido con la misma diferencia de gramaje.
PEDIDOS = [
    {
        "of": "90001", "isbn": "9780000000017", "carpeta": "90001",
        "titulo": "Manual de Encuadernacion Imaginaria",
        "cliente": {"cantidad": "1,500", "paginas": "192", "gr_cubierta": "240"},
        "orden": {"cantidad": "1.500", "paginas": "192", "gr_cubierta": "240"},
        "contrato": True,
    },
    {
        "of": "90002", "isbn": "9780000000024", "carpeta": "90002",
        "titulo": "Atlas de Tipografias Inventadas",
        "cliente": {"cantidad": "3,000", "paginas": "288", "gr_cubierta": "240"},
        # 30.000 contra 3.000 pedidos, y 250 g contra 240: la misma pareja de
        # discrepancias que el caso real, una grave y una menor.
        "orden": {"cantidad": "30.000", "paginas": "288", "gr_cubierta": "250"},
    },
]


def escribir(ruta, texto):
    """Un PDF con capa de texto: nada de imágenes, para no depender del OCR."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(ruta), pagesize=A4)
    c.setFont("Courier", 9)
    y = A4[1] - 50
    for linea in texto.splitlines():
        c.drawString(45, y, linea)
        y -= 12
        if y < 50:
            c.showPage()
            c.setFont("Courier", 9)
            y = A4[1] - 50
    c.save()


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for p in PEDIDOS:
        base = DESTINO / p["carpeta"]
        escribir(base / f'{p["carpeta"]}_1_presupuesto.pdf',
                 presupuesto(p["isbn"], p["titulo"], **p["cliente"]))
        escribir(base / f'{p["carpeta"]}_2_pedido_de_cliente.pdf',
                 cliente(p["isbn"], p["titulo"], **p["cliente"]))
        escribir(base / f'{p["carpeta"]}_3_orden_de_fabricacion.pdf',
                 orden(p["of"], p["isbn"], p["titulo"], **p["orden"]))
        if p.get("contrato"):
            # El contrato marco no pertenece a ningún pedido: cuelga del
            # expediente del cliente y por eso va en su propia carpeta. La
            # herramienta de diligencia lo encuentra porque es el único
            # documento de la bandeja que se puede situar en el tiempo.
            escribir(DESTINO / "expediente" / "contrato_marco_del_cliente.pdf",
                     CONTRATO)
    (DESTINO / "LEEME.md").write_text(
        "# Bandeja de ejemplo\n\n"
        "Todo inventado de principio a fin: la editorial, los títulos y los ISBN "
        "no existen. Lo genera `demo/generar_ejemplo.py`.\n\n"
        "- **90001** — presupuesto, pedido y orden que dicen lo mismo. Se "
        "despacha sin incidencias.\n"
        "- **90002** — dos diferencias que no se deciden igual: la orden manda "
        "fabricar 30.000 ejemplares de los 3.000 que pidió el cliente, y sube "
        "el gramaje de cubierta de 240 a 250 g.\n"
        "- **expediente/** — el contrato marco del cliente, vigente hasta marzo "
        "de 2027, con preaviso de 60 días.\n\n"
        "Existen para que la demo se pueda recorrer entera en cualquier "
        "despliegue, sin depender de documentación de cliente. Para la "
        "demostración de verdad se suben los documentos reales: dan el mismo "
        "resultado por el mismo camino.\n",
        encoding="utf-8")
    print(f"Escritos en {DESTINO}")


if __name__ == "__main__":
    main()
