"""
Swagger documentation for Users endpoints.
"""
from flask_restx import Resource
from app.api.swagger import (
    users_ns,
    user_model,
    user_update_model,
    password_change_model,
    address_model,
    address_create_model,
    address_update_model,
    error_model
)


@users_ns.route('/profile')
class ProfileDoc(Resource):
    @users_ns.doc('get_profile', security='Bearer')
    @users_ns.response(200, 'Perfil del usuario', user_model)
    @users_ns.response(401, 'No autenticado', error_model)
    @users_ns.response(404, 'Usuario no encontrado', error_model)
    def get(self):
        """
        Obtener perfil del usuario

        Retorna el perfil completo del usuario autenticado.
        """
        pass

    @users_ns.doc('update_profile', security='Bearer')
    @users_ns.expect(user_update_model)
    @users_ns.response(200, 'Perfil actualizado', user_model)
    @users_ns.response(400, 'Error de validación', error_model)
    @users_ns.response(401, 'No autenticado', error_model)
    @users_ns.response(404, 'Usuario no encontrado', error_model)
    def put(self):
        """
        Actualizar perfil del usuario

        Actualiza los campos del perfil del usuario autenticado.
        Solo se actualizan los campos enviados en la petición.
        """
        pass


@users_ns.route('/password')
class PasswordDoc(Resource):
    @users_ns.doc('change_password', security='Bearer')
    @users_ns.expect(password_change_model)
    @users_ns.response(200, 'Contraseña actualizada')
    @users_ns.response(400, 'Contraseña actual incorrecta o usuario OAuth', error_model)
    @users_ns.response(401, 'No autenticado', error_model)
    @users_ns.response(404, 'Usuario no encontrado', error_model)
    def put(self):
        """
        Cambiar contraseña

        Cambia la contraseña del usuario autenticado.
        Solo disponible para usuarios con autenticación por email.
        """
        pass


@users_ns.route('/addresses')
class AddressesDoc(Resource):
    @users_ns.doc('get_addresses', security='Bearer')
    @users_ns.response(200, 'Lista de direcciones', [address_model])
    @users_ns.response(401, 'No autenticado', error_model)
    def get(self):
        """
        Listar direcciones del usuario

        Retorna todas las direcciones guardadas del usuario autenticado.
        """
        pass

    @users_ns.doc('create_address', security='Bearer')
    @users_ns.expect(address_create_model)
    @users_ns.response(201, 'Dirección creada', address_model)
    @users_ns.response(400, 'Error de validación', error_model)
    @users_ns.response(401, 'No autenticado', error_model)
    def post(self):
        """
        Crear nueva dirección

        Crea una nueva dirección para el usuario autenticado.
        Si se marca como predeterminada, las otras direcciones perderán ese estado.
        """
        pass


@users_ns.route('/addresses/<string:address_id>')
@users_ns.param('address_id', 'UUID de la dirección')
class AddressDoc(Resource):
    @users_ns.doc('get_address', security='Bearer')
    @users_ns.response(200, 'Dirección', address_model)
    @users_ns.response(401, 'No autenticado', error_model)
    @users_ns.response(404, 'Dirección no encontrada', error_model)
    def get(self):
        """
        Obtener dirección por ID

        Retorna los detalles de una dirección específica del usuario.
        """
        pass

    @users_ns.doc('update_address', security='Bearer')
    @users_ns.expect(address_update_model)
    @users_ns.response(200, 'Dirección actualizada', address_model)
    @users_ns.response(400, 'Error de validación', error_model)
    @users_ns.response(401, 'No autenticado', error_model)
    @users_ns.response(404, 'Dirección no encontrada', error_model)
    def put(self):
        """
        Actualizar dirección

        Actualiza los campos de una dirección existente.
        Solo se actualizan los campos enviados en la petición.
        """
        pass

    @users_ns.doc('delete_address', security='Bearer')
    @users_ns.response(200, 'Dirección eliminada')
    @users_ns.response(401, 'No autenticado', error_model)
    @users_ns.response(404, 'Dirección no encontrada', error_model)
    def delete(self):
        """
        Eliminar dirección

        Elimina permanentemente una dirección del usuario.
        """
        pass


@users_ns.route('/addresses/<string:address_id>/default')
@users_ns.param('address_id', 'UUID de la dirección')
class AddressDefaultDoc(Resource):
    @users_ns.doc('set_default_address', security='Bearer')
    @users_ns.response(200, 'Dirección marcada como predeterminada', address_model)
    @users_ns.response(401, 'No autenticado', error_model)
    @users_ns.response(404, 'Dirección no encontrada', error_model)
    def put(self):
        """
        Marcar dirección como predeterminada

        Establece la dirección especificada como la predeterminada.
        Las otras direcciones perderán el estado de predeterminada.
        """
        pass
