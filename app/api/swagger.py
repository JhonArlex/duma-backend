"""
Swagger/OpenAPI documentation configuration using Flask-RESTX.
"""
from flask_restx import Api, fields

# API instance for Swagger documentation
api = Api(
    title='Duma Express API',
    version='1.0.0',
    description='API para la aplicación Duma Express - Servicio de compras y entregas desde USA a Venezuela',
    doc='/docs',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Token. Format: "Bearer {token}"'
        }
    },
    security='Bearer'
)

# =============================================================================
# Namespaces
# =============================================================================
auth_ns = api.namespace('api/auth', description='Autenticación y gestión de sesiones')
users_ns = api.namespace('api/users', description='Gestión de perfil y direcciones de usuario')
orders_ns = api.namespace('api/orders', description='Gestión de órdenes de compra')
carts_ns = api.namespace('api/carts', description='Carrito de compras')
stores_ns = api.namespace('api/stores', description='Tiendas soportadas')
payments_ns = api.namespace('api/payments', description='Procesamiento de pagos')
roles_ns = api.namespace('api/roles', description='Gestión de roles y permisos (Solo Superadmin)')

# =============================================================================
# Common Models
# =============================================================================
error_model = api.model('Error', {
    'error': fields.String(description='Código de error'),
    'message': fields.String(description='Mensaje descriptivo del error'),
    'messages': fields.Raw(description='Detalles de validación (opcional)')
})

pagination_model = api.model('Pagination', {
    'total': fields.Integer(description='Total de registros'),
    'pages': fields.Integer(description='Total de páginas'),
    'current_page': fields.Integer(description='Página actual')
})

# =============================================================================
# Auth Models
# =============================================================================
user_model = api.model('User', {
    'id': fields.String(description='UUID del usuario'),
    'email': fields.String(description='Correo electrónico'),
    'display_name': fields.String(description='Nombre para mostrar'),
    'phone_number': fields.String(description='Número de teléfono'),
    'photo_url': fields.String(description='URL de la foto de perfil'),
    'country': fields.String(description='País'),
    'auth_provider': fields.String(description='Proveedor de autenticación', enum=['email', 'google', 'apple']),
    'email_verified': fields.Boolean(description='Email verificado'),
    'created_at': fields.DateTime(description='Fecha de creación'),
    'last_login': fields.DateTime(description='Último inicio de sesión')
})

register_model = api.model('Register', {
    'email': fields.String(required=True, description='Correo electrónico'),
    'password': fields.String(required=True, description='Contraseña (mínimo 8 caracteres)'),
    'display_name': fields.String(required=True, description='Nombre para mostrar'),
    'phone_number': fields.String(description='Número de teléfono'),
    'country': fields.String(description='País', default='Venezuela')
})

login_model = api.model('Login', {
    'email': fields.String(required=True, description='Correo electrónico'),
    'password': fields.String(required=True, description='Contraseña')
})

oauth_login_model = api.model('OAuthLogin', {
    'provider': fields.String(required=True, description='Proveedor OAuth', enum=['google', 'apple']),
    'token': fields.String(required=True, description='Token del proveedor'),
    'email': fields.String(description='Correo electrónico'),
    'display_name': fields.String(description='Nombre para mostrar'),
    'photo_url': fields.String(description='URL de la foto')
})

auth_response_model = api.model('AuthResponse', {
    'user': fields.Nested(user_model),
    'access_token': fields.String(description='Token de acceso JWT'),
    'refresh_token': fields.String(description='Token de refresco JWT')
})

token_refresh_model = api.model('TokenRefresh', {
    'access_token': fields.String(description='Nuevo token de acceso')
})

# =============================================================================
# Address Models
# =============================================================================
address_model = api.model('Address', {
    'id': fields.String(description='UUID de la dirección'),
    'type': fields.String(description='Tipo de dirección', enum=['shipping', 'billing']),
    'label': fields.String(description='Etiqueta (Casa, Trabajo, etc.)'),
    'recipient_name': fields.String(description='Nombre del destinatario'),
    'phone': fields.String(description='Teléfono de contacto'),
    'address_line_1': fields.String(description='Dirección línea 1'),
    'address_line_2': fields.String(description='Dirección línea 2'),
    'city': fields.String(description='Ciudad'),
    'state': fields.String(description='Estado/Provincia'),
    'postal_code': fields.String(description='Código postal'),
    'country': fields.String(description='País'),
    'is_default': fields.Boolean(description='Es dirección predeterminada'),
    'created_at': fields.DateTime(description='Fecha de creación')
})

address_create_model = api.model('AddressCreate', {
    'type': fields.String(required=True, description='Tipo', enum=['shipping', 'billing']),
    'label': fields.String(description='Etiqueta'),
    'recipient_name': fields.String(required=True, description='Nombre del destinatario'),
    'phone': fields.String(description='Teléfono'),
    'address_line_1': fields.String(required=True, description='Dirección línea 1'),
    'address_line_2': fields.String(description='Dirección línea 2'),
    'city': fields.String(required=True, description='Ciudad'),
    'state': fields.String(required=True, description='Estado'),
    'postal_code': fields.String(description='Código postal'),
    'country': fields.String(required=True, description='País'),
    'is_default': fields.Boolean(description='Es predeterminada', default=False)
})

address_update_model = api.model('AddressUpdate', {
    'label': fields.String(description='Etiqueta'),
    'recipient_name': fields.String(description='Nombre del destinatario'),
    'phone': fields.String(description='Teléfono'),
    'address_line_1': fields.String(description='Dirección línea 1'),
    'address_line_2': fields.String(description='Dirección línea 2'),
    'city': fields.String(description='Ciudad'),
    'state': fields.String(description='Estado'),
    'postal_code': fields.String(description='Código postal'),
    'is_default': fields.Boolean(description='Es predeterminada')
})

# =============================================================================
# User Models
# =============================================================================
user_update_model = api.model('UserUpdate', {
    'display_name': fields.String(description='Nombre para mostrar'),
    'phone_number': fields.String(description='Número de teléfono'),
    'photo_url': fields.String(description='URL de foto'),
    'country': fields.String(description='País')
})

password_change_model = api.model('PasswordChange', {
    'current_password': fields.String(required=True, description='Contraseña actual'),
    'new_password': fields.String(required=True, description='Nueva contraseña (mínimo 8 caracteres)')
})

# =============================================================================
# Store Models
# =============================================================================
store_model = api.model('Store', {
    'id': fields.String(description='UUID de la tienda'),
    'name': fields.String(description='Nombre de la tienda'),
    'slug': fields.String(description='Identificador único'),
    'base_url': fields.String(description='URL base de la tienda'),
    'logo_url': fields.String(description='URL del logo'),
    'is_active': fields.Boolean(description='Tienda activa'),
    'display_order': fields.Integer(description='Orden de visualización'),
    'config': fields.Raw(description='Configuración adicional')
})

store_config_model = api.model('StoreConfig', {
    'id': fields.String(description='UUID'),
    'name': fields.String(description='Nombre'),
    'slug': fields.String(description='Slug'),
    'base_url': fields.String(description='URL base'),
    'config': fields.Raw(description='Configuración para WebView')
})

# =============================================================================
# Cart Models
# =============================================================================
cart_item_model = api.model('CartItem', {
    'id': fields.String(description='UUID del item'),
    'store_id': fields.String(description='UUID de la tienda'),
    'product_url': fields.String(description='URL del producto'),
    'title': fields.String(description='Título del producto'),
    'image_url': fields.String(description='URL de imagen'),
    'variant_size': fields.String(description='Talla/Tamaño'),
    'variant_color': fields.String(description='Color'),
    'quantity': fields.Integer(description='Cantidad'),
    'unit_price': fields.Float(description='Precio unitario USD'),
    'notes': fields.String(description='Notas'),
    'created_at': fields.DateTime(description='Fecha de creación')
})

cart_model = api.model('Cart', {
    'id': fields.String(description='UUID del carrito'),
    'user_id': fields.String(description='UUID del usuario'),
    'items': fields.List(fields.Nested(cart_item_model)),
    'item_count': fields.Integer(description='Cantidad de items'),
    'subtotal': fields.Float(description='Subtotal USD'),
    'updated_at': fields.DateTime(description='Última actualización')
})

cart_item_create_model = api.model('CartItemCreate', {
    'store_id': fields.String(description='UUID de la tienda'),
    'product_url': fields.String(required=True, description='URL del producto'),
    'title': fields.String(description='Título'),
    'image_url': fields.String(description='URL de imagen'),
    'variant_size': fields.String(description='Talla'),
    'variant_color': fields.String(description='Color'),
    'quantity': fields.Integer(description='Cantidad', default=1),
    'unit_price': fields.Float(required=True, description='Precio unitario USD'),
    'notes': fields.String(description='Notas')
})

cart_item_update_model = api.model('CartItemUpdate', {
    'quantity': fields.Integer(description='Nueva cantidad'),
    'notes': fields.String(description='Notas')
})

checkout_model = api.model('Checkout', {
    'shipping_address_id': fields.String(required=True, description='UUID de la dirección de envío')
})

checkout_response_model = api.model('CheckoutResponse', {
    'message': fields.String(description='Mensaje'),
    'order_data': fields.Raw(description='Datos para crear la orden')
})

# =============================================================================
# Order Models
# =============================================================================
order_item_model = api.model('OrderItem', {
    'id': fields.String(description='UUID del item'),
    'store_id': fields.String(description='UUID de la tienda'),
    'product_url': fields.String(description='URL del producto'),
    'title': fields.String(description='Título'),
    'image_url': fields.String(description='URL de imagen'),
    'variant_size': fields.String(description='Talla'),
    'variant_color': fields.String(description='Color'),
    'quantity': fields.Integer(description='Cantidad'),
    'unit_price': fields.Float(description='Precio unitario USD'),
    'total_price': fields.Float(description='Precio total USD'),
    'notes': fields.String(description='Notas'),
    'status': fields.String(description='Estado del item')
})

order_model = api.model('Order', {
    'id': fields.String(description='UUID de la orden'),
    'order_number': fields.String(description='Número de orden (DUM-YYYY-NNNNNN)'),
    'user_id': fields.String(description='UUID del usuario'),
    'shipping_address_id': fields.String(description='UUID dirección de envío'),
    'status': fields.String(description='Estado', enum=['pending', 'processing', 'shipped', 'delivered', 'cancelled']),
    'payment_status': fields.String(description='Estado de pago', enum=['pending', 'paid', 'failed', 'refunded']),
    'subtotal': fields.Float(description='Subtotal USD'),
    'platform_fee': fields.Float(description='Tarifa de plataforma USD'),
    'shipping_cost': fields.Float(description='Costo de envío USD'),
    'total_usd': fields.Float(description='Total USD'),
    'exchange_rate': fields.Float(description='Tasa de cambio USD/VES'),
    'total_bs': fields.Float(description='Total en Bolívares'),
    'notes': fields.String(description='Notas'),
    'tracking_number': fields.String(description='Número de rastreo'),
    'estimated_delivery': fields.Date(description='Fecha estimada de entrega'),
    'created_at': fields.DateTime(description='Fecha de creación'),
    'paid_at': fields.DateTime(description='Fecha de pago'),
    'items': fields.List(fields.Nested(order_item_model))
})

order_create_item_model = api.model('OrderCreateItem', {
    'store_id': fields.String(description='UUID de la tienda'),
    'product_url': fields.String(required=True, description='URL del producto'),
    'title': fields.String(description='Título'),
    'image_url': fields.String(description='URL de imagen'),
    'variant_size': fields.String(description='Talla'),
    'variant_color': fields.String(description='Color'),
    'quantity': fields.Integer(required=True, description='Cantidad'),
    'unit_price': fields.Float(required=True, description='Precio unitario USD'),
    'notes': fields.String(description='Notas')
})

order_create_model = api.model('OrderCreate', {
    'shipping_address_id': fields.String(required=True, description='UUID de la dirección'),
    'items': fields.List(fields.Nested(order_create_item_model), required=True, description='Items de la orden'),
    'notes': fields.String(description='Notas de la orden')
})

order_status_update_model = api.model('OrderStatusUpdate', {
    'status': fields.String(required=True, description='Nuevo estado', enum=['processing', 'shipped', 'delivered', 'cancelled']),
    'notes': fields.String(description='Notas del cambio')
})

orders_list_model = api.model('OrdersList', {
    'orders': fields.List(fields.Nested(order_model)),
    'total': fields.Integer(description='Total de órdenes'),
    'pages': fields.Integer(description='Total de páginas'),
    'current_page': fields.Integer(description='Página actual')
})

order_history_model = api.model('OrderHistory', {
    'id': fields.String(description='UUID del registro'),
    'from_status': fields.String(description='Estado anterior'),
    'to_status': fields.String(description='Nuevo estado'),
    'changed_by': fields.String(description='UUID del usuario que cambió'),
    'notes': fields.String(description='Notas'),
    'created_at': fields.DateTime(description='Fecha del cambio')
})

# =============================================================================
# Payment Models
# =============================================================================
payment_model = api.model('Payment', {
    'id': fields.String(description='UUID del pago'),
    'order_id': fields.String(description='UUID de la orden'),
    'user_id': fields.String(description='UUID del usuario'),
    'payment_provider': fields.String(description='Proveedor', enum=['stripe', 'paypal', 'pago_movil', 'manual']),
    'payment_method': fields.String(description='Método de pago'),
    'amount': fields.Float(description='Monto'),
    'currency': fields.String(description='Moneda'),
    'status': fields.String(description='Estado', enum=['pending', 'completed', 'failed', 'refunded']),
    'provider_txn_id': fields.String(description='ID de transacción del proveedor'),
    'created_at': fields.DateTime(description='Fecha de creación'),
    'completed_at': fields.DateTime(description='Fecha de completado')
})

payment_intent_request_model = api.model('PaymentIntentRequest', {
    'order_id': fields.String(required=True, description='UUID de la orden')
})

payment_intent_response_model = api.model('PaymentIntentResponse', {
    'client_secret': fields.String(description='Client secret de Stripe'),
    'payment_intent_id': fields.String(description='ID del PaymentIntent'),
    'amount': fields.Float(description='Monto'),
    'currency': fields.String(description='Moneda')
})

payment_confirm_model = api.model('PaymentConfirm', {
    'order_id': fields.String(required=True, description='UUID de la orden'),
    'payment_provider': fields.String(required=True, description='Proveedor', enum=['stripe', 'paypal', 'pago_movil', 'manual']),
    'payment_method': fields.String(description='Método de pago'),
    'stripe_payment_method_id': fields.String(description='ID del PaymentMethod de Stripe')
})

# =============================================================================
# Role Models
# =============================================================================
role_summary_model = api.model('RoleSummary', {
    'id': fields.String(description='UUID del rol'),
    'name': fields.String(description='Nombre del rol'),
    'type': fields.String(description='Tipo de rol', enum=['superadmin', 'admin', 'authenticated', 'public'])
})

role_model = api.model('Role', {
    'id': fields.String(description='UUID del rol'),
    'name': fields.String(description='Nombre del rol'),
    'description': fields.String(description='Descripción del rol'),
    'type': fields.String(description='Tipo de rol', enum=['superadmin', 'admin', 'authenticated', 'public']),
    'is_system': fields.Boolean(description='Es un rol del sistema (no se puede eliminar)'),
    'is_default': fields.Boolean(description='Es el rol por defecto para nuevos usuarios'),
    'user_count': fields.Integer(description='Cantidad de usuarios con este rol'),
    'created_at': fields.DateTime(description='Fecha de creación'),
    'updated_at': fields.DateTime(description='Última actualización'),
    'permissions': fields.Raw(description='Permisos del rol organizados por entidad')
})

role_create_model = api.model('RoleCreate', {
    'name': fields.String(required=True, description='Nombre del rol (2-100 caracteres)'),
    'description': fields.String(description='Descripción del rol'),
    'type': fields.String(description='Tipo de rol', enum=['admin', 'authenticated'], default='authenticated')
})

role_update_model = api.model('RoleUpdate', {
    'name': fields.String(description='Nombre del rol'),
    'description': fields.String(description='Descripción del rol')
})

permission_model = api.model('Permission', {
    'id': fields.String(description='UUID del permiso'),
    'role_id': fields.String(description='UUID del rol'),
    'entity': fields.String(description='Entidad', enum=[
        'user', 'address', 'store', 'order', 'order_item',
        'cart', 'cart_item', 'payment', 'exchange_rate',
        'notification', 'role', 'permission'
    ]),
    'action': fields.String(description='Acción', enum=['create', 'read', 'read_all', 'update', 'delete']),
    'is_enabled': fields.Boolean(description='Permiso habilitado'),
    'conditions': fields.Raw(description='Condiciones adicionales (ej: {own_only: true})'),
    'created_at': fields.DateTime(description='Fecha de creación')
})

permissions_update_model = api.model('PermissionsUpdate', {
    'permissions': fields.Raw(
        required=True,
        description='Permisos a actualizar. Formato: {"entity": {"action": true/false}}'
    )
})

single_permission_update_model = api.model('SinglePermissionUpdate', {
    'is_enabled': fields.Boolean(required=True, description='Habilitar o deshabilitar permiso'),
    'conditions': fields.Raw(description='Condiciones adicionales')
})

user_role_assign_model = api.model('UserRoleAssign', {
    'role_id': fields.String(required=True, description='UUID del rol a asignar')
})

user_with_role_model = api.model('UserWithRole', {
    'id': fields.String(description='UUID del usuario'),
    'email': fields.String(description='Email del usuario'),
    'display_name': fields.String(description='Nombre del usuario'),
    'is_active': fields.Boolean(description='Usuario activo'),
    'role': fields.Nested(role_summary_model, description='Rol asignado'),
    'created_at': fields.DateTime(description='Fecha de creación')
})

users_with_roles_list_model = api.model('UsersWithRolesList', {
    'users': fields.List(fields.Nested(user_with_role_model)),
    'total': fields.Integer(description='Total de usuarios'),
    'pages': fields.Integer(description='Total de páginas'),
    'current_page': fields.Integer(description='Página actual')
})

role_permissions_response_model = api.model('RolePermissionsResponse', {
    'role_id': fields.String(description='UUID del rol'),
    'role_name': fields.String(description='Nombre del rol'),
    'permissions': fields.Raw(description='Permisos organizados por entidad')
})

entities_actions_model = api.model('EntitiesActions', {
    'entities': fields.List(fields.String, description='Lista de entidades disponibles'),
    'actions': fields.List(fields.String, description='Lista de acciones disponibles')
})
