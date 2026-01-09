"""
Swagger documentation for Payments endpoints.
"""
from flask_restx import Resource
from app.api.swagger import (
    payments_ns,
    payment_model,
    payment_intent_request_model,
    payment_intent_response_model,
    payment_confirm_model,
    error_model
)


@payments_ns.route('/create-intent')
class PaymentIntentDoc(Resource):
    @payments_ns.doc('create_payment_intent', security='Bearer')
    @payments_ns.expect(payment_intent_request_model)
    @payments_ns.response(200, 'Payment Intent creado', payment_intent_response_model)
    @payments_ns.response(400, 'Orden ya pagada', error_model)
    @payments_ns.response(401, 'No autenticado', error_model)
    @payments_ns.response(404, 'Orden no encontrada', error_model)
    @payments_ns.response(500, 'Error al crear Payment Intent', error_model)
    def post(self):
        """
        Crear Stripe Payment Intent

        Crea un Payment Intent de Stripe para procesar el pago de una orden.

        **Flujo de pago con Stripe:**
        1. Crear orden con POST /api/orders
        2. Llamar a este endpoint para obtener el client_secret
        3. En el cliente, usar Stripe SDK para confirmar el pago
        4. Llamar a POST /api/payments/confirm para registrar el pago
        5. Opcionalmente, configurar webhook para actualizaciones automáticas

        **Respuesta:**
        - client_secret: Para usar con Stripe SDK en el cliente
        - payment_intent_id: ID del Payment Intent
        - amount: Monto en USD
        """
        pass


@payments_ns.route('/confirm')
class PaymentConfirmDoc(Resource):
    @payments_ns.doc('confirm_payment', security='Bearer')
    @payments_ns.expect(payment_confirm_model)
    @payments_ns.response(200, 'Pago confirmado', payment_model)
    @payments_ns.response(400, 'Orden ya pagada o error de pago', error_model)
    @payments_ns.response(401, 'No autenticado', error_model)
    @payments_ns.response(404, 'Orden no encontrada', error_model)
    def post(self):
        """
        Confirmar pago

        Registra y confirma un pago después del procesamiento por Stripe.

        **Proveedores soportados:**
        - stripe: Tarjeta de crédito/débito
        - paypal: PayPal (próximamente)
        - pago_movil: Pago Móvil Venezuela (próximamente)
        - manual: Pago manual/transferencia

        Para Stripe, incluir el stripe_payment_method_id obtenido del SDK.
        """
        pass


@payments_ns.route('/<string:payment_id>')
@payments_ns.param('payment_id', 'UUID del pago')
class PaymentDoc(Resource):
    @payments_ns.doc('get_payment', security='Bearer')
    @payments_ns.response(200, 'Detalles del pago', payment_model)
    @payments_ns.response(401, 'No autenticado', error_model)
    @payments_ns.response(404, 'Pago no encontrado', error_model)
    def get(self):
        """
        Obtener pago por ID

        Retorna los detalles de un pago específico.
        """
        pass


@payments_ns.route('/order/<string:order_id>')
@payments_ns.param('order_id', 'UUID de la orden')
class OrderPaymentsDoc(Resource):
    @payments_ns.doc('get_order_payments', security='Bearer')
    @payments_ns.response(200, 'Pagos de la orden', [payment_model])
    @payments_ns.response(401, 'No autenticado', error_model)
    @payments_ns.response(404, 'Orden no encontrada', error_model)
    def get(self):
        """
        Listar pagos de una orden

        Retorna todos los intentos de pago asociados a una orden.
        Puede incluir pagos fallidos y exitosos.
        """
        pass


@payments_ns.route('/webhook/stripe')
class StripeWebhookDoc(Resource):
    @payments_ns.doc('stripe_webhook')
    @payments_ns.response(200, 'Webhook procesado')
    @payments_ns.response(400, 'Error al procesar webhook', error_model)
    @payments_ns.response(500, 'Webhook no configurado', error_model)
    def post(self):
        """
        Webhook de Stripe

        Endpoint para recibir notificaciones de eventos de Stripe.

        **Eventos manejados:**
        - payment_intent.succeeded: Marca la orden como pagada
        - payment_intent.payment_failed: Marca el pago como fallido

        **Configuración:**
        Este endpoint debe configurarse en el dashboard de Stripe.
        La firma del webhook se verifica usando STRIPE_WEBHOOK_SECRET.

        **Header requerido:**
        - Stripe-Signature: Firma del webhook

        Este endpoint es público (Stripe lo llama directamente).
        """
        pass
