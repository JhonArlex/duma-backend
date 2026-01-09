"""
Swagger documentation for Roles and Permissions endpoints.

All endpoints require superadmin access.
"""
from flask_restx import Resource
from app.api.swagger import (
    roles_ns,
    role_model,
    role_create_model,
    role_update_model,
    permissions_update_model,
    single_permission_update_model,
    user_role_assign_model,
    users_with_roles_list_model,
    role_permissions_response_model,
    entities_actions_model,
    error_model
)


# =============================================================================
# Role Management
# =============================================================================

@roles_ns.route('')
class RolesDoc(Resource):
    @roles_ns.doc('get_roles', security='Bearer')
    @roles_ns.param('include_permissions', 'Incluir permisos en la respuesta', type=bool, default=False)
    @roles_ns.response(200, 'Lista de roles', [role_model])
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    def get(self):
        """
        Listar todos los roles

        Retorna todos los roles del sistema.
        Opcionalmente incluye los permisos de cada rol.

        **Requiere rol: superadmin**
        """
        pass

    @roles_ns.doc('create_role', security='Bearer')
    @roles_ns.expect(role_create_model)
    @roles_ns.response(201, 'Rol creado', role_model)
    @roles_ns.response(400, 'Error de validación', error_model)
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    @roles_ns.response(409, 'Nombre de rol ya existe', error_model)
    def post(self):
        """
        Crear nuevo rol

        Crea un nuevo rol con todos los permisos deshabilitados por defecto.

        **Tipos de rol permitidos:**
        - admin: Rol administrativo
        - authenticated: Rol de usuario autenticado

        No se pueden crear roles superadmin o public.

        **Requiere rol: superadmin**
        """
        pass


@roles_ns.route('/<string:role_id>')
@roles_ns.param('role_id', 'UUID del rol')
class RoleDoc(Resource):
    @roles_ns.doc('get_role', security='Bearer')
    @roles_ns.response(200, 'Detalles del rol', role_model)
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    @roles_ns.response(404, 'Rol no encontrado', error_model)
    def get(self):
        """
        Obtener rol por ID

        Retorna los detalles completos de un rol, incluyendo sus permisos.

        **Requiere rol: superadmin**
        """
        pass

    @roles_ns.doc('update_role', security='Bearer')
    @roles_ns.expect(role_update_model)
    @roles_ns.response(200, 'Rol actualizado', role_model)
    @roles_ns.response(400, 'Error de validación', error_model)
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    @roles_ns.response(404, 'Rol no encontrado', error_model)
    @roles_ns.response(409, 'Nombre de rol ya existe', error_model)
    def put(self):
        """
        Actualizar rol

        Actualiza el nombre y/o descripción de un rol.

        **Requiere rol: superadmin**
        """
        pass

    @roles_ns.doc('delete_role', security='Bearer')
    @roles_ns.response(200, 'Rol eliminado')
    @roles_ns.response(400, 'No se puede eliminar rol del sistema o con usuarios', error_model)
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    @roles_ns.response(404, 'Rol no encontrado', error_model)
    def delete(self):
        """
        Eliminar rol

        Elimina un rol del sistema.

        **Restricciones:**
        - No se pueden eliminar roles del sistema (superadmin, admin, authenticated, public)
        - No se pueden eliminar roles que tienen usuarios asignados

        **Requiere rol: superadmin**
        """
        pass


# =============================================================================
# Permission Management
# =============================================================================

@roles_ns.route('/<string:role_id>/permissions')
@roles_ns.param('role_id', 'UUID del rol')
class RolePermissionsDoc(Resource):
    @roles_ns.doc('get_role_permissions', security='Bearer')
    @roles_ns.response(200, 'Permisos del rol', role_permissions_response_model)
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    @roles_ns.response(404, 'Rol no encontrado', error_model)
    def get(self):
        """
        Obtener permisos de un rol

        Retorna todos los permisos del rol organizados por entidad.

        **Formato de respuesta:**
        ```json
        {
            "role_id": "uuid",
            "role_name": "Admin",
            "permissions": {
                "user": {
                    "create": true,
                    "read": true,
                    "read_all": true,
                    "update": true,
                    "delete": false
                },
                ...
            }
        }
        ```

        **Requiere rol: superadmin**
        """
        pass

    @roles_ns.doc('update_role_permissions', security='Bearer')
    @roles_ns.expect(permissions_update_model)
    @roles_ns.response(200, 'Permisos actualizados', role_permissions_response_model)
    @roles_ns.response(400, 'Error de validación o rol superadmin', error_model)
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    @roles_ns.response(404, 'Rol no encontrado', error_model)
    def put(self):
        """
        Actualizar permisos de un rol

        Actualiza múltiples permisos de un rol.

        **Formato del body:**
        ```json
        {
            "permissions": {
                "user": {
                    "create": true,
                    "read": true,
                    "read_all": false,
                    "update": true,
                    "delete": false
                },
                "order": {
                    "create": true,
                    "read": true,
                    ...
                }
            }
        }
        ```

        **Restricción:** No se pueden modificar permisos del rol superadmin.

        **Requiere rol: superadmin**
        """
        pass


@roles_ns.route('/<string:role_id>/permissions/<string:entity>/<string:action>')
@roles_ns.param('role_id', 'UUID del rol')
@roles_ns.param('entity', 'Entidad (user, order, cart, etc.)')
@roles_ns.param('action', 'Acción (create, read, read_all, update, delete)')
class SinglePermissionDoc(Resource):
    @roles_ns.doc('update_single_permission', security='Bearer')
    @roles_ns.expect(single_permission_update_model)
    @roles_ns.response(200, 'Permiso actualizado')
    @roles_ns.response(400, 'Entidad/acción inválida o rol superadmin', error_model)
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    @roles_ns.response(404, 'Rol no encontrado', error_model)
    def put(self):
        """
        Actualizar un permiso específico

        Actualiza un único permiso de un rol.

        **Entidades disponibles:**
        user, address, store, order, order_item, cart, cart_item,
        payment, exchange_rate, notification, role, permission

        **Acciones disponibles:**
        - create: Crear nuevos registros
        - read: Leer un registro individual
        - read_all: Listar múltiples registros
        - update: Modificar registros existentes
        - delete: Eliminar registros

        **Condiciones opcionales:**
        ```json
        {
            "is_enabled": true,
            "conditions": {
                "own_only": true  // Solo acceso a sus propios registros
            }
        }
        ```

        **Requiere rol: superadmin**
        """
        pass


# =============================================================================
# User Role Assignment
# =============================================================================

@roles_ns.route('/users')
class UsersWithRolesDoc(Resource):
    @roles_ns.doc('get_users_with_roles', security='Bearer')
    @roles_ns.param('page', 'Número de página', type=int, default=1)
    @roles_ns.param('per_page', 'Resultados por página (máx 100)', type=int, default=20)
    @roles_ns.param('role_id', 'Filtrar por UUID de rol', type=str)
    @roles_ns.response(200, 'Lista de usuarios con roles', users_with_roles_list_model)
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    def get(self):
        """
        Listar usuarios con sus roles

        Retorna todos los usuarios con información de sus roles asignados.
        Se puede filtrar por rol específico.

        **Requiere rol: superadmin**
        """
        pass


@roles_ns.route('/users/<string:user_id>/role')
@roles_ns.param('user_id', 'UUID del usuario')
class UserRoleDoc(Resource):
    @roles_ns.doc('assign_user_role', security='Bearer')
    @roles_ns.expect(user_role_assign_model)
    @roles_ns.response(200, 'Rol asignado')
    @roles_ns.response(400, 'No puede cambiar su propio rol', error_model)
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    @roles_ns.response(404, 'Usuario o rol no encontrado', error_model)
    def put(self):
        """
        Asignar rol a usuario

        Asigna un rol a un usuario específico.

        **Restricción:** No puede cambiar su propio rol.

        **Requiere rol: superadmin**
        """
        pass


# =============================================================================
# Utility Endpoints
# =============================================================================

@roles_ns.route('/entities')
class EntitiesDoc(Resource):
    @roles_ns.doc('get_entities', security='Bearer')
    @roles_ns.response(200, 'Entidades y acciones disponibles', entities_actions_model)
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    def get(self):
        """
        Obtener entidades y acciones disponibles

        Retorna la lista de todas las entidades y acciones que pueden
        configurarse en los permisos.

        **Requiere rol: superadmin**
        """
        pass


@roles_ns.route('/default')
class DefaultRoleDoc(Resource):
    @roles_ns.doc('get_default_role', security='Bearer')
    @roles_ns.response(200, 'Rol por defecto', role_model)
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    @roles_ns.response(404, 'No hay rol por defecto configurado', error_model)
    def get(self):
        """
        Obtener rol por defecto

        Retorna el rol que se asigna automáticamente a los nuevos usuarios.

        **Requiere rol: superadmin**
        """
        pass


@roles_ns.route('/<string:role_id>/set-default')
@roles_ns.param('role_id', 'UUID del rol')
class SetDefaultRoleDoc(Resource):
    @roles_ns.doc('set_default_role', security='Bearer')
    @roles_ns.response(200, 'Rol establecido como defecto')
    @roles_ns.response(400, 'No se puede establecer superadmin como defecto', error_model)
    @roles_ns.response(401, 'No autenticado', error_model)
    @roles_ns.response(403, 'Acceso denegado - Solo superadmin', error_model)
    @roles_ns.response(404, 'Rol no encontrado', error_model)
    def post(self):
        """
        Establecer rol por defecto

        Establece un rol como el rol por defecto para nuevos usuarios.

        **Restricción:** No se puede establecer superadmin como rol por defecto.

        **Requiere rol: superadmin**
        """
        pass
