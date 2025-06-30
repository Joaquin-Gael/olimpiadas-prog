import os
import sys
import django
from django.conf import settings

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

# Configuración de pytest para Django
pytest_plugins = ['pytest_django'] 