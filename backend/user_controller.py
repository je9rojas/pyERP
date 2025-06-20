from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .models.user import Usuario

user_bp = Blueprint('users', __name__)

@user_bp.route('/crear', methods=['POST'])
@login_required
def crear_usuario():
    if not current_user.is_admin():
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.get_json()
    rol = data.get('rol', 'cliente')
    
    # Validar jerarquía de roles
    if rol == 'superadmin' and not current_user.is_superadmin():
        return jsonify({'error': 'Solo superadmin puede crear superadmin'}), 403
    
    if rol == 'admin' and not current_user.is_superadmin():
        return jsonify({'error': 'Solo superadmin puede crear admin'}), 403
    
    nuevo_usuario = Usuario(
        email=data['email'],
        nombre=data['nombre'],
        rol=rol,
        creado_por=str(current_user.id)
    nuevo_usuario.set_password(data['password'])
    
    try:
        nuevo_usuario.save()
        return jsonify({'mensaje': 'Usuario creado', 'id': str(nuevo_usuario.id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@user_bp.route('/<id>', methods=['PUT'])
@login_required
def actualizar_usuario(id):
    usuario = Usuario.objects(id=id).first()
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    # Validar permisos
    if usuario.rol == 'superadmin' and not current_user.is_superadmin():
        return jsonify({'error': 'No puedes modificar superadmin'}), 403
    
    if not current_user.is_admin():
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.get_json()
    if 'password' in data:
        usuario.set_password(data['password'])
    if 'nombre' in data:
        usuario.nombre = data['nombre']
    if 'activo' in data:
        usuario.activo = data['activo']
    
    usuario.save()
    return jsonify({'mensaje': 'Usuario actualizado'}), 200

@user_bp.route('/<id>', methods=['DELETE'])
@login_required
def eliminar_usuario(id):
    usuario = Usuario.objects(id=id).first()
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    # Validar permisos
    if usuario.rol == 'superadmin':
        return jsonify({'error': 'No se puede eliminar superadmin'}), 403
    
    if not current_user.is_admin():
        return jsonify({'error': 'No autorizado'}), 403
    
    usuario.delete()
    return jsonify({'mensaje': 'Usuario eliminado'}), 200