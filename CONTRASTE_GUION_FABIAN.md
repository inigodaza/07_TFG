# El customer journey, implementado

Íñigo Daza · 10 de septiembre de 2026
Contraste del guion pantalla a pantalla (v3, 9/09) con lo que hay construido.

> «Espero que te facilite el trabajo y nos dé una base común para contrastarla
> mañana con tu propuesta.»

Lo he implementado. Las nueve pantallas están en la aplicación y se recorren de
principio a fin. Este documento dice qué encaja, qué he cambiado y en qué tres
puntos creo que conviene discutir.

---

## 1 · Las nueve pantallas, una por una

| # | Pantalla del guion | Estado | Qué hace de verdad |
|---|---|---|---|
| 0 | El sistema trabaja en segundo plano | ✔ | Procesa cada tanda en cuanto entra y deja la cola de alarmas hecha. Nadie ha pedido que se revise nada |
| 1 | Entrada y contexto del usuario | ✔ | Pantalla de entrada con rol, nivel, área, tipo de autoridad y sobre qué manda — leído de la ontología |
| 2 | Entrada y procesamiento | ✔ | **Pantalla de recepción**: la documentación entra por tandas y se procesa a la vista, documento a documento |
| 3 | Alerta | ✔ | «Posible incongruencia · Pedido 3.000 · Orden 30.000» salta al terminar de leer la tanda, con la fila del documento que la disparó marcada |
| 4 | Dashboard de la incidencia | ✔ | Un centro de control: alarma, contexto, tres herramientas y actuación |
| 5 | Evidencia y diagnóstico | ✔ | **Fragmento literal de cada documento**, con el valor resaltado y su línea, y el estado del diagnóstico |
| 6 | Autoridad y permisos | ✔ | «Puedes proponer · cerrarla le corresponde a Dir. Producción, CEO» |
| 7 | Decisión y captura del criterio | ✔ | Aceptar · corregir · escalar, **con justificación obligatoria** |
| 8 | Cierre, memoria y aprendizaje | ✔ | Registro de criterio con las dos columnas, y el precedente en el caso siguiente |

**Recorrido probado de extremo a extremo**: identificarse → recibir dos tandas y ver saltar la alarma → atender la
alarma del 90002 → proponer con justificación → cambiar a director (que ve la
justificación previa) → cerrar → ver el registro de criterio → volver a la cola →
tolerar el gramaje del 90002 y **ver el criterio guardarse**. Para verlo VOLVER hace falta un segundo pedido con la misma diferencia, que hoy no está en la bandeja.

602 comprobaciones automáticas en verde, de las cuales 40 cubren lo que se añadió
por este guion.

---

## 2 · La etiqueta «Naturaleza», y el dato que sale de ella

He implementado las etiquetas IA / determinista / humana en cada pantalla, y
distinguen tres estados en vez de dos, porque hacía falta:

- **actúa** — interviene hoy, en esta demo, con estos datos
- **disponible** — implementado y activable con una clave; aquí no corre
- **prevista** — es donde iría, y todavía no está

Y el recuento sale así:

| | Pantallas que resuelve **hoy** |
|---|---|
| Determinista | **9 de 9** |
| Humana | 2 (decisión y cierre) |
| IA | **0** |

IA **prevista** en 4 pantallas · **disponible** en 2.

Ese cero no es una carencia que haya que disimular: es la respuesta con datos a
la pregunta que tú planteas. «No se trata de poner IA en todo» deja de ser una
frase y pasa a ser un recuento. Y las cuatro pantallas donde sí aportaría están
nombradas, que es lo accionable.

**Dónde creo que la IA aporta de verdad**, por orden:

1. **Pantalla 5, el diagnóstico.** Distinguir un error de transcripción de un
   cambio acordado es interpretación, y hoy lo resuelvo con una regla pobre
   (comparar los documentos de cliente entre sí). Aquí hay hueco real.
2. **Pantalla 2, extracción.** Documentos con formato desconocido. Ya está
   implementado y **vetado** sobre los documentos de Juan, por lo de abajo.
3. **Pantalla 8, recuperación.** Casos equivalentes que no comparten la forma
   exacta pero sí el problema.
4. **Pantalla 7, asistencia.** Redactar la justificación para que una persona la
   acepte o la cambie.

**Dónde creo que NO debe entrar**: pantalla 6. Autoridad, permisos y escalado
tienen que ser deterministas. Meter IA ahí no es una mejora, es un problema de
seguridad.

---

## 3 · Los tres puntos a discutir mañana

### a) El veto de IA sobre los documentos de Juan sigue en pie

El modo asistido está construido y funciona, pero está **cerrado** para el
material de Juan: son datos reales de cliente de GraphyCems y el nivel gratuito
del proveedor entrena con lo que se le manda. Levantarlo requiere un plan de pago
y el visto bueno de Juan, y no es una decisión que me corresponda a mí.

Consecuencia práctica para la demo: las pantallas donde la IA aportaría se
enseñan con la etiqueta *prevista*, no funcionando.

### b) La cadena de validación reproduce la regla de Mencía, no su salida

La pantalla 7 aplica lo que se ve en el vídeo de su módulo —quien está en el área
propone, quien manda sobre ella valida— pero **no es su exportación**. Sigo
esperando la del pedido 42805, antes y después de resolver. En cuanto llegue, el
mismo cruce se ejecuta sobre datos suyos y emite veredicto.

### c) Falta el mapa campo → ámbito de Pablo

Su matriz va de **rol a área**; el módulo de Mencía va de **contradicción a
categoría**; la pieza del medio —de qué área es cada campo de un pedido— no está
en ninguno de los dos. Y no es un detalle: con `cantidad` leída como Producción
la validación del Director de Producción es válida, y leída como Comercial no lo
es. La misma decisión, dos veredictos.

---

## 4 · Lo que he añadido al guion, y por qué

**La documentación entra por tandas, y se puede meter más en cualquier momento.**
Tu pantalla 0 dice que el sistema vigila en segundo plano, y eso es cierto — pero
si al abrir la aplicación la alarma ya está ahí, no se ve de dónde sale. Ahora se
recibe una tanda, se ve procesarse y la alarma salta al final. Y se puede dejar
una sin recibir, entrar en la consola, y meterla después para verla saltar en
vivo. Es lo que distingue un sistema en marcha de un guion.

**Justificación obligatoria, también al proponer.** Tu pantalla 7 dice «el
encargado propone y justifica». Lo he hecho bloqueante y **antes** de comprobar
los permisos: sin motivo no se registra nada. Una propuesta sin justificar le
deja al que valida el mismo trabajo que si no la hubiera, y un criterio sin
motivo no se puede reutilizar — dentro de seis meses queda el número y nadie sabe
por qué.

**Condiciones de aplicación en el precedente.** Tu columna «contexto de
reutilización» la he hecho ejecutable: el criterio guarda cliente, producto y
tipo de documento, y cuando llega un caso nuevo **se comprueba que aplican**. Si
el caso es de otro cliente, el precedente se descarta y se dice por qué. Un
precedente sin condiciones es una regla disfrazada: acabaría aplicándose donde no
toca, que es peor que no tenerlo.

**Versionado del criterio.** Si mañana se decide otra cosa para el mismo patrón,
el anterior no se borra: se versiona. Se puede ver que cambió y cuándo.

**El sistema no se sienta precedente a sí mismo.** Detalle pequeño y molesto: al
cerrar una alarma, su propio registro volvía como «esto ya pasó».

**«Requiere decisión humana» acompaña siempre a los otros tres diagnósticos.** No
como excusa: el sistema puede decir qué no cuadra y **no** cuál de los dos valores
vale. Es la frase que más va a servir si alguien pregunta si esto sustituye a
alguien.

---

## 5 · Una diferencia de fondo, dicha claramente

Tu guion presenta las nueve pantallas como el producto. Lo que yo tengo son **dos
cosas separadas a propósito**, y creo que conviene mantenerlo así:

- **Consola** — el producto: lo que el equipo construiría con las cinco piezas
  juntas. Es tu customer journey.
- **Evaluar un módulo** — mi bloque haciendo su trabajo: baterías, métricas,
  severidad, veredicto e informe.

Mezclarlas produciría una demostración más redonda y una demostración peor: la
que no distingue lo que funciona de lo que se ha ensayado. Y esa distinción es
precisamente lo que aporta mi parte al proyecto.

En la propia consola quedan escritas, en una línea cada una, las tres cosas que
**no** se demuestran: la salida de Juan se entrega y no se va a buscar, la cadena
de Mencía es la regla y no su salida, y la herramienta de similitud **declara que
no puede contestar** porque su histórico es de otro dominio. Esa tercera es la
que más nos defiende: disfrazarla habría quedado mejor en la demo y es
exactamente el tipo de cosa que este bloque existe para detectar.

---

## 6 · Lo que necesito para cerrar el recorrido

| De quién | Qué | Para qué |
|---|---|---|
| **Mencía** | Exportación del 42805, antes y después de resolver | Que la pantalla 7 deje de reproducir la regla y evalúe su salida |
| **Pablo** | Mapa campo → ámbito | Que el cruce de autoridad pueda cerrarse en vez de declararse abierto |
| **Juan** | Su criterio sobre el veto de IA | Que las pantallas 2 y 5 puedan enseñarse funcionando |
