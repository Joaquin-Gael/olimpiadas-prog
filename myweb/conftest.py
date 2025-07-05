import os
import sys
import django
import pytest
from django.conf import settings
from decimal import Decimal

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

# Configuración de pytest para Django
pytest_plugins = ['pytest_django']

# Fixtures globales para todos los tests
@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Configuración de base de datos para toda la sesión de tests."""
    with django_db_blocker.unblock():
        # Aquí puedes añadir configuración inicial de BD si es necesario
        pass

@pytest.fixture
def sample_decimal():
    """Fixture para valores decimales comunes en tests."""
    return Decimal("100.00")

# Marcadores personalizados para organizar tests
def pytest_configure(config):
    """Configuración de marcadores personalizados."""
    config.addinivalue_line(
        "markers", "unit: marca tests unitarios"
    )
    config.addinivalue_line(
        "markers", "integration: marca tests de integración"
    )
    config.addinivalue_line(
        "markers", "e2e: marca tests end-to-end"
    )
    config.addinivalue_line(
        "markers", "slow: marca tests lentos"
    ) 