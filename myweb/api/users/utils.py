from ninja.security import HttpBearer
import jwt
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model() 
class HeaderJWTAuth(HttpBearer):
    def authenticate(self, request, token):
        if not token:
            return None
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            return user
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            return None