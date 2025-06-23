from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
import re


class UserValidator:
    """Clase para validar datos de usuarios"""
    
    @staticmethod
    def validate_email(email):
        """Valida el formato del email"""
        validator = EmailValidator()
        try:
            validator(email)
            return True
        except ValidationError:
            return False
    
    @staticmethod
    def validate_telephone(telephone):
        """Valida el formato del teléfono (formato básico)"""
        # Patrón básico para teléfonos (puedes ajustarlo según tus necesidades)
        pattern = r'^\+?1?\d{9,15}$'
        return re.match(pattern, telephone) is not None
    
    @staticmethod
    def validate_password(password):
        """Valida la contraseña (mínimo 8 caracteres, al menos una letra y un número)"""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        
        if not re.search(r'[A-Za-z]', password):
            return False, "La contraseña debe contener al menos una letra"
        
        if not re.search(r'\d', password):
            return False, "La contraseña debe contener al menos un número"
        
        return True, "Contraseña válida"
    
    @staticmethod
    def validate_names(name):
        """Valida nombres y apellidos"""
        if not name or len(name.strip()) < 2:
            return False, "El nombre debe tener al menos 2 caracteres"
        
        if not re.match(r'^[A-Za-zÁáÉéÍíÓóÚúÑñ\s]+$', name):
            return False, "El nombre solo puede contener letras y espacios"
        
        return True, "Nombre válido"


class UserSerializer:
    """Clase para serializar/deserializar datos de usuarios"""
    
    @staticmethod
    def validate_registration_data(data):
        """Valida los datos de registro"""
        errors = {}
        
        # Validar email
        if not UserValidator.validate_email(data.get('email', '')):
            errors['email'] = "Formato de email inválido"
        
        # Validar teléfono
        if not UserValidator.validate_telephone(data.get('telephone', '')):
            errors['telephone'] = "Formato de teléfono inválido"
        
        # Validar contraseña
        is_valid_password, password_message = UserValidator.validate_password(data.get('password', ''))
        if not is_valid_password:
            errors['password'] = password_message
        
        # Validar nombres
        is_valid_first_name, first_name_message = UserValidator.validate_names(data.get('first_name', ''))
        if not is_valid_first_name:
            errors['first_name'] = first_name_message
        
        is_valid_last_name, last_name_message = UserValidator.validate_names(data.get('last_name', ''))
        if not is_valid_last_name:
            errors['last_name'] = last_name_message
        
        return len(errors) == 0, errors
    
    @staticmethod
    def to_dict(user):
        """Convierte un objeto User a diccionario"""
        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "telephone": user.telephone,
            "born_date": user.born_date,
            "state": user.state,
            "created_at": user.created_at,
            "is_staff": user.is_staff
        } 