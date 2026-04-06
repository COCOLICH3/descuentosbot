Ayudame a agregar un nuevo descuento a la planilla de Google Sheets "descuentosbot".

Antes de modificar nada, preguntame los siguientes datos:

1. **banco** — nombre del banco (ej: galicia, santander, bbva)
2. **supermercado** — nombre del super (ej: Carrefour, Coto, Dia)
3. **dia** — día(s) de la semana. Opciones válidas:
   - Un día: `Lunes`, `Martes`, `Miercoles`, `Jueves`, `Viernes`, `Sabado`, `Domingo`
   - Varios días separados con `/`: ej `Martes/Jueves`
   - Todos los días: `Todos los dias`
   - ⚠️ Sin tildes. "Miércoles" es incorrecto, debe ser "Miercoles"
4. **descuento** — porcentaje o valor (ej: `25%`, `30% de reintegro`)
5. **tope** — monto máximo de reintegro (ej: `$2000`). Si no hay tope, escribir `Sin tope`
6. **metodo_pago** — cómo se activa el descuento (ej: `Débito`, `Crédito`, `Débito y Crédito`, `App Galicia`)

Una vez que tenga todos los datos, mostrá un resumen en formato de fila de planilla y confirmá antes de dar instrucciones para agregarla manualmente a la planilla.

Recordá que la planilla tiene exactamente estas 6 columnas en este orden:
`banco | supermercado | dia | descuento | tope | metodo_pago`