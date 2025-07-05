#!/usr/bin/env python3
"""
Test de diagnóstico simple para el endpoint GET de productos
"""

import os
import sys
import django
import json
import time as time_module
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from api.products.models import ProductsMetadata, Activities, Location, Suppliers
from api.products.schemas import ProductsMetadataOut

def log(message):
    """Función para logging con timestamp"""
    timestamp = datetime.now().strftime("[%H:%M:%S]")
    print(f"{timestamp} INFO: {message}")

def log_error(message):
    """Función para logging de errores con timestamp"""
    timestamp = datetime.now().strftime("[%H:%M:%S]")
    print(f"{timestamp} ERROR: {message}")

def main():
    log("🔍 Iniciando diagnóstico simple del endpoint GET de productos...")
    
    # Crear cliente de prueba
    client = Client()
    
    # Obtener ID prefix
    try:
        from myweb.settings import ID_PREFIX
        id_prefix = ID_PREFIX
        log(f"ID Prefix: {id_prefix}")
    except Exception as e:
        log_error(f"Error obteniendo ID prefix: {str(e)}")
        return
    
    # Test 1: Verificar que el servidor responde
    log("🧪 Test 1: Verificar respuesta del servidor")
    try:
        response = client.get(f'/{id_prefix}/')
        log(f"Status Code raíz: {response.status_code}")
    except Exception as e:
        log_error(f"Error en test raíz: {str(e)}")
    
    # Test 2: Verificar endpoint de productos básico
    log("🧪 Test 2: Verificar endpoint de productos básico")
    try:
        response = client.get(f'/{id_prefix}/products/')
        log(f"Status Code productos: {response.status_code}")
        if response.status_code != 200:
            log(f"Contenido de error: {response.content[:500]}...")
    except Exception as e:
        log_error(f"Error en test productos: {str(e)}")
    
    # Test 3: Verificar endpoint de productos con filtros
    log("🧪 Test 3: Verificar endpoint de productos con filtros")
    try:
        response = client.get(f'/{id_prefix}/products/?limit=10')
        log(f"Status Code productos con parámetros: {response.status_code}")
        if response.status_code != 200:
            log(f"Contenido de error: {response.content[:500]}...")
    except Exception as e:
        log_error(f"Error en test productos con parámetros: {str(e)}")
    
    # Test 4: Verificar endpoint de diagnóstico
    log("🧪 Test 4: Verificar endpoint de diagnóstico")
    try:
        response = client.get(f'/{id_prefix}/products/test/')
        log(f"Status Code diagnóstico: {response.status_code}")
        if response.status_code == 200:
            try:
                data = json.loads(response.content)
                log(f"Diagnóstico exitoso: {data}")
            except json.JSONDecodeError:
                log("Diagnóstico exitoso pero no es JSON válido")
        else:
            log(f"Contenido de error: {response.content[:500]}...")
    except Exception as e:
        log_error(f"Error en test diagnóstico: {str(e)}")
    
    # Test 5: Verificar endpoint all
    log("🧪 Test 5: Verificar endpoint all")
    try:
        response = client.get(f'/{id_prefix}/products/all/')
        log(f"Status Code all: {response.status_code}")
        if response.status_code != 200:
            log(f"Contenido de error: {response.content[:500]}...")
    except Exception as e:
        log_error(f"Error en test all: {str(e)}")
    
    log("✅ Diagnóstico completado")

if __name__ == "__main__":
    main() 