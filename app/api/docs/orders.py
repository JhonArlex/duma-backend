"""
Swagger documentation for Orders endpoints.
"""
from flask_restx import Resource
from app.api.swagger import (
    orders_ns,
    order_model,
    order_create_model,
    order_status_update_model,
    orders_list_model,
    order_history_model,
    error_model,
    api
)


@orders_ns.route('')
class OrdersDoc(Resource):
    @orders_ns.doc('get_orders', security='Bearer')
    @orders_ns.param('page', 'Número de página', type=int, default=1)
    @orders_ns.param('per_page', 'Resultados por página (máx 50)', type=int, default=10)
    @orders_ns.param('status', 'Filtrar por estado', type=str,
                     enum=['pending', 'processing', 'shipped', 'delivered', 'cancelled'])
    @orders_ns.response(200, 'Lista de órdenes', orders_list_model)
    @orders_ns.response(401, 'No autenticado', error_model)
    def get(self):
        """
        Listar órdenes del usuario

        Retorna las órdenes del usuario autenticado con paginación.
        Se puede filtrar por estado de la orden.
        """
        pass

    @orders_ns.doc('create_order', security='Bearer')
    @orders_ns.expect(order_create_model)
    @orders_ns.response(201, 'Orden creada', order_model)
    @orders_ns.response(400, 'Error de validación o dirección inválida', error_model)
    @orders_ns.response(401, 'No autenticado', error_model)
    def post(self):
        """
        Crear nueva orden

        Crea una nueva orden de compra con los items especificados.

        - El número de orden se genera automáticamente (DUM-YYYY-NNNNNN)
        - Se calcula automáticamente: subtotal, platform_fee (10%), total_usd
        - Si hay tasa de cambio activa, se calcula total_bs
        - La orden inicia en estado 'pending'
        """
        pass


@orders_ns.route('/<string:order_id>')
@orders_ns.param('order_id', 'UUID de la orden')
class OrderDoc(Resource):
    @orders_ns.doc('get_order', security='Bearer')
    @orders_ns.response(200, 'Detalles de la orden', order_model)
    @orders_ns.response(401, 'No autenticado', error_model)
    @orders_ns.response(404, 'Orden no encontrada', error_model)
    def get(self):
        """
        Obtener orden por ID

        Retorna los detalles completos de una orden específica,
        incluyendo todos los items.
        """
        pass


@orders_ns.route('/<string:order_id>/status')
@orders_ns.param('order_id', 'UUID de la orden')
class OrderStatusDoc(Resource):
    @orders_ns.doc('update_order_status', security='Bearer')
    @orders_ns.expect(order_status_update_model)
    @orders_ns.response(200, 'Estado actualizado', order_model)
    @orders_ns.response(400, 'Transición de estado inválida', error_model)
    @orders_ns.response(401, 'No autenticado', error_model)
    @orders_ns.response(404, 'Orden no encontrada', error_model)
    def put(self):
        """
        Actualizar estado de la orden

        Actualiza el estado de una orden siguiendo las transiciones válidas:

        - **pending** → processing, cancelled
        - **processing** → shipped, cancelled
        - **shipped** → delivered
        - **delivered** → (estado final)
        - **cancelled** → (estado final)
        """
        pass


@orders_ns.route('/<string:order_id>/cancel')
@orders_ns.param('order_id', 'UUID de la orden')
class OrderCancelDoc(Resource):
    @orders_ns.doc('cancel_order', security='Bearer')
    @orders_ns.response(200, 'Orden cancelada', order_model)
    @orders_ns.response(400, 'No se puede cancelar en el estado actual', error_model)
    @orders_ns.response(401, 'No autenticado', error_model)
    @orders_ns.response(404, 'Orden no encontrada', error_model)
    def post(self):
        """
        Cancelar orden

        Cancela una orden que esté en estado 'pending' o 'processing'.
        Las órdenes en otros estados no pueden ser canceladas.
        """
        pass


@orders_ns.route('/<string:order_id>/history')
@orders_ns.param('order_id', 'UUID de la orden')
class OrderHistoryDoc(Resource):
    @orders_ns.doc('get_order_history', security='Bearer')
    @orders_ns.response(200, 'Historial de estados', [order_history_model])
    @orders_ns.response(401, 'No autenticado', error_model)
    @orders_ns.response(404, 'Orden no encontrada', error_model)
    def get(self):
        """
        Obtener historial de estados

        Retorna el historial completo de cambios de estado de la orden,
        incluyendo fecha, usuario que realizó el cambio y notas.
        """
        pass
