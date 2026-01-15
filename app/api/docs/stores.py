"""
Swagger documentation for Stores endpoints.
"""
from flask_restx import Resource
from app.api.swagger import (
    stores_ns,
    store_model,
    store_config_model,
    error_model
)


@stores_ns.route('')
class StoresDoc(Resource):
    @stores_ns.doc('get_stores')
    @stores_ns.response(200, 'Lista de tiendas activas', [store_model])
    def get(self):
        """
        Listar tiendas activas

        Retorna todas las tiendas activas ordenadas por display_order.

        **Tiendas disponibles:**
        - Amazon
        - eBay
        - Walmart
        - Target
        - Best Buy
        - Shein
        - AliExpress
        - Otra Tienda (para URLs personalizadas)

        Este endpoint es público y no requiere autenticación.
        """
        pass


@stores_ns.route('/<string:slug>')
@stores_ns.param('slug', 'Identificador único de la tienda (ej: amazon, ebay)')
class StoreDoc(Resource):
    @stores_ns.doc('get_store')
    @stores_ns.response(200, 'Tienda', store_model)
    @stores_ns.response(404, 'Tienda no encontrada', error_model)
    def get(self):
        """
        Obtener tienda por slug

        Retorna los detalles de una tienda específica usando su slug.

        **Slugs disponibles:**
        - amazon
        - ebay
        - walmart
        - target
        - bestbuy
        - shein
        - aliexpress
        - other

        Este endpoint es público y no requiere autenticación.
        """
        pass


@stores_ns.route('/<string:store_id>/config')
@stores_ns.param('store_id', 'UUID de la tienda')
class StoreConfigDoc(Resource):
    @stores_ns.doc('get_store_config', security='Bearer')
    @stores_ns.response(200, 'Configuración de la tienda', store_config_model)
    @stores_ns.response(401, 'No autenticado', error_model)
    @stores_ns.response(404, 'Tienda no encontrada', error_model)
    def get(self):
        """
        Obtener configuración de tienda para WebView

        Retorna la configuración específica de una tienda para ser usada
        en el WebView de la aplicación móvil.

        Incluye:
        - URL base de la tienda
        - Configuración de scraping
        - Países soportados
        """
        pass
