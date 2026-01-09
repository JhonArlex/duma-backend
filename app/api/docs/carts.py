"""
Swagger documentation for Carts endpoints.
"""
from flask_restx import Resource
from app.api.swagger import (
    carts_ns,
    cart_model,
    cart_item_model,
    cart_item_create_model,
    cart_item_update_model,
    checkout_model,
    checkout_response_model,
    error_model
)


@carts_ns.route('')
class CartDoc(Resource):
    @carts_ns.doc('get_cart', security='Bearer')
    @carts_ns.response(200, 'Carrito del usuario', cart_model)
    @carts_ns.response(401, 'No autenticado', error_model)
    def get(self):
        """
        Obtener carrito del usuario

        Retorna el carrito del usuario autenticado con todos sus items.
        Si el usuario no tiene carrito, se crea uno automáticamente.

        Incluye:
        - Lista de items con detalles
        - Cantidad total de items
        - Subtotal en USD
        """
        pass


@carts_ns.route('/items')
class CartItemsDoc(Resource):
    @carts_ns.doc('add_cart_item', security='Bearer')
    @carts_ns.expect(cart_item_create_model)
    @carts_ns.response(201, 'Item agregado al carrito', cart_item_model)
    @carts_ns.response(400, 'Error de validación', error_model)
    @carts_ns.response(401, 'No autenticado', error_model)
    def post(self):
        """
        Agregar item al carrito

        Agrega un nuevo producto al carrito.

        - Si el producto (mismo URL) ya existe, se actualiza la cantidad
        - El precio unitario es obligatorio y debe estar en USD
        - Opcionalmente se puede asociar a una tienda
        """
        pass


@carts_ns.route('/items/<string:item_id>')
@carts_ns.param('item_id', 'UUID del item')
class CartItemDoc(Resource):
    @carts_ns.doc('update_cart_item', security='Bearer')
    @carts_ns.expect(cart_item_update_model)
    @carts_ns.response(200, 'Item actualizado', cart_item_model)
    @carts_ns.response(400, 'Error de validación', error_model)
    @carts_ns.response(401, 'No autenticado', error_model)
    @carts_ns.response(404, 'Item no encontrado', error_model)
    def put(self):
        """
        Actualizar item del carrito

        Actualiza la cantidad o notas de un item existente en el carrito.
        """
        pass

    @carts_ns.doc('remove_cart_item', security='Bearer')
    @carts_ns.response(200, 'Item eliminado')
    @carts_ns.response(401, 'No autenticado', error_model)
    @carts_ns.response(404, 'Item no encontrado', error_model)
    def delete(self):
        """
        Eliminar item del carrito

        Elimina un item específico del carrito.
        """
        pass


@carts_ns.route('/clear')
class CartClearDoc(Resource):
    @carts_ns.doc('clear_cart', security='Bearer')
    @carts_ns.response(200, 'Carrito vaciado')
    @carts_ns.response(401, 'No autenticado', error_model)
    def delete(self):
        """
        Vaciar carrito

        Elimina todos los items del carrito del usuario.
        """
        pass


@carts_ns.route('/checkout')
class CartCheckoutDoc(Resource):
    @carts_ns.doc('checkout', security='Bearer')
    @carts_ns.expect(checkout_model)
    @carts_ns.response(200, 'Datos para crear orden', checkout_response_model)
    @carts_ns.response(400, 'Carrito vacío o dirección faltante', error_model)
    @carts_ns.response(401, 'No autenticado', error_model)
    def post(self):
        """
        Preparar checkout

        Prepara los datos del carrito para crear una orden.

        Retorna los datos formateados para enviar al endpoint de creación de órdenes.
        Este endpoint NO crea la orden, solo prepara los datos.

        **Flujo:**
        1. Llamar a este endpoint con la dirección de envío
        2. Usar los datos retornados para llamar a POST /api/orders
        3. Procesar el pago con el endpoint de pagos
        """
        pass
