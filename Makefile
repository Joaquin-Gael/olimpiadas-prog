# Makefile para el proyecto myweb
# Comandos para testing y cobertura de código

.PHONY: help test test-olympiad coverage clean-coverage install-cov

# Comando por defecto
help:
	@echo "Comandos disponibles:"
	@echo "  test          - Ejecutar todos los tests con cobertura"
	@echo "  test-olympiad - Ejecutar tests específicos de olimpiadas"
	@echo "  test-unit     - Ejecutar solo tests unitarios"
	@echo "  test-integration - Ejecutar solo tests de integración"
	@echo "  test-products - Ejecutar tests específicos de productos"
	@echo "  test-store    - Ejecutar tests específicos de store"
	@echo "  coverage      - Generar reporte de cobertura HTML"
	@echo "  clean-coverage- Limpiar archivos de cobertura"
	@echo "  install-cov   - Instalar pytest-cov"

# Instalar pytest-cov si no está instalado
install-cov:
	pip install pytest-cov

# Ejecutar todos los tests con cobertura
test: install-cov
	pytest

# Ejecutar tests específicos de olimpiadas (productos, store, etc.)
test-olympiad: install-cov
	pytest myweb/api/products/ myweb/api/store/ myweb/api/core/ -v --cov=myweb/api/products --cov=myweb/api/store --cov=myweb/api/core --cov-report=term-missing

# Ejecutar solo tests unitarios
test-unit: install-cov
	pytest -m unit -v --cov=myweb/api/products --cov=myweb/api/store --cov=myweb/api/core --cov-report=term-missing

# Ejecutar solo tests de integración
test-integration: install-cov
	pytest -m integration -v --cov=myweb/api/products --cov=myweb/api/store --cov=myweb/api/core --cov-report=term-missing

# Ejecutar tests específicos de productos
test-products: install-cov
	pytest myweb/api/products/tests/ -v --cov=myweb/api/products --cov-report=term-missing

# Ejecutar tests específicos de store
test-store: install-cov
	pytest myweb/api/store/tests/ -v --cov=myweb/api/store --cov-report=term-missing

# Generar reporte de cobertura HTML
coverage: install-cov
	pytest --cov=myweb/api/products \
	       --cov=myweb/api/store \
	       --cov=myweb/api/users \
	       --cov=myweb/api/employees \
	       --cov=myweb/api/clients \
	       --cov=myweb/api/core \
	       --cov-report=html:htmlcov \
	       --cov-report=term-missing \
	       --cov-fail-under=80
	@echo "Reporte de cobertura generado en htmlcov/index.html"

# Limpiar archivos de cobertura
clean-coverage:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	@echo "Archivos de cobertura limpiados"

# Comando para ejecutar tests rápidos sin cobertura
test-fast:
	pytest --reuse-db --nomigrations

# Comando para ejecutar tests con verbose
test-verbose: install-cov
	pytest -v --cov=myweb/api/products \
	          --cov=myweb/api/store \
	          --cov=myweb/api/users \
	          --cov=myweb/api/employees \
	          --cov=myweb/api/clients \
	          --cov=myweb/api/core \
	          --cov-report=term-missing 