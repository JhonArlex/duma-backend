"""
Swagger documentation for Auth endpoints.
"""
from flask_restx import Resource
from app.api.swagger import (
    auth_ns,
    register_model,
    login_model,
    oauth_login_model,
    auth_response_model,
    token_refresh_model,
    user_model,
    error_model
)


@auth_ns.route('/register')
class RegisterDoc(Resource):
    @auth_ns.doc('register_user')
    @auth_ns.expect(register_model)
    @auth_ns.response(201, 'Usuario registrado exitosamente', auth_response_model)
    @auth_ns.response(400, 'Error de validación', error_model)
    @auth_ns.response(409, 'Email ya registrado', error_model)
    @auth_ns.response(429, 'Límite de peticiones excedido', error_model)
    def post(self):
        """
        Registrar un nuevo usuario

        Crea una nueva cuenta de usuario con email y contraseña.
        Automáticamente crea un carrito de compras para el usuario.

        **Rate limit:** 5 peticiones por minuto
        """
        pass


@auth_ns.route('/login')
class LoginDoc(Resource):
    @auth_ns.doc('login_user')
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Login exitoso', auth_response_model)
    @auth_ns.response(400, 'Error de validación', error_model)
    @auth_ns.response(401, 'Credenciales inválidas', error_model)
    @auth_ns.response(429, 'Límite de peticiones excedido', error_model)
    def post(self):
        """
        Iniciar sesión con email y contraseña

        Autentica al usuario y retorna tokens JWT.

        **Rate limit:** 10 peticiones por minuto
        """
        pass


@auth_ns.route('/oauth')
class OAuthDoc(Resource):
    @auth_ns.doc('oauth_login')
    @auth_ns.expect(oauth_login_model)
    @auth_ns.response(200, 'Login OAuth exitoso', auth_response_model)
    @auth_ns.response(400, 'Error de validación o email faltante', error_model)
    @auth_ns.response(409, 'Email ya registrado con otro proveedor', error_model)
    @auth_ns.response(429, 'Límite de peticiones excedido', error_model)
    def post(self):
        """
        Iniciar sesión o registrarse con OAuth (Google/Apple)

        Si el usuario no existe, se crea automáticamente.
        Si ya existe con el mismo proveedor, se actualiza el token.
        Si el email existe con otro proveedor, retorna error 409.

        **Rate limit:** 10 peticiones por minuto
        """
        pass


@auth_ns.route('/refresh')
class RefreshDoc(Resource):
    @auth_ns.doc('refresh_token', security='Bearer')
    @auth_ns.response(200, 'Token refrescado', token_refresh_model)
    @auth_ns.response(401, 'Token de refresco inválido o expirado', error_model)
    def post(self):
        """
        Refrescar token de acceso

        Usa el refresh token para obtener un nuevo access token.
        El header Authorization debe contener el refresh token.
        """
        pass


@auth_ns.route('/me')
class MeDoc(Resource):
    @auth_ns.doc('get_current_user', security='Bearer')
    @auth_ns.response(200, 'Usuario actual', user_model)
    @auth_ns.response(401, 'No autenticado', error_model)
    @auth_ns.response(404, 'Usuario no encontrado', error_model)
    def get(self):
        """
        Obtener usuario autenticado

        Retorna los datos del usuario actualmente autenticado.
        """
        pass


@auth_ns.route('/logout')
class LogoutDoc(Resource):
    @auth_ns.doc('logout_user', security='Bearer')
    @auth_ns.response(200, 'Logout exitoso')
    @auth_ns.response(401, 'No autenticado', error_model)
    def post(self):
        """
        Cerrar sesión

        Invalida la sesión actual. El cliente debe descartar los tokens.
        """
        pass
