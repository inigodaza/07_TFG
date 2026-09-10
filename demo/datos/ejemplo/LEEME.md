# Bandeja de ejemplo

Todo inventado de principio a fin: la editorial, los títulos y los ISBN no existen. Lo genera `demo/generar_ejemplo.py`.

- **90001** — presupuesto, pedido y orden que dicen lo mismo. Se despacha sin incidencias.
- **90002** — la orden manda fabricar 30.000 ejemplares de los 3.000 que pidió el cliente, y sube el gramaje de cubierta de 240 a 250 g.
- **90003** — el mismo error otra vez: 8.000 de los 800 pedidos. Sirve para enseñar que el sistema recuerda cómo se resolvió el anterior.
- **expediente/** — el contrato marco del cliente, vigente hasta marzo de 2027, con preaviso de 60 días.

Existen para que la demo se pueda recorrer entera en cualquier despliegue, sin depender de documentación de cliente. Para la demostración de verdad se suben los documentos reales: dan el mismo resultado por el mismo camino.
