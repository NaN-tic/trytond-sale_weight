====================
Venta. Peso en venta
====================

Añade dos campos a la venta:

* Peso de las líneas: El peso de todas las líneas del pedido (en el caso que el producto
  disponga de peso.
* Peso: Campo que el usuario podrá personalizar según el peso que desee.

Costes del envío
----------------

Si el coste de envío del transportista se calcula en base del peso, por defecto se usa
el peso de las líneas. Si el usuario añade un valor en el peso del pedido de venta,
el valor del peso para el cálculo del coste de envío será el del pedido de venta.

Peso pedido a albarán de salida
-------------------------------

En el momento de generar albaranes de salida, si en el pedido dispone de un peso se copiará
al campo peso del albarán de salida.
