# 🛒 Olimpiadas de Programación - Backend

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![DjangoNinja](https://img.shields.io/badge/Django_Ninja-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

## ⚡ Acerca del proyecto

Backend potente y eficiente desarrollado con **Django** y **Django-Ninja** para ofrecer una API rápida y moderna.

## 🛠️ Tecnologías

- **Django**: Framework web robusto y escalable
- **Django-Ninja**: API REST rápida inspirada en FastAPI
- **MySQL**: Base de datos relacional
- **JWT**: Autenticación segura

## 🚀 Características principales

- Catálogo de productos con categorías y filtros
- Gestión de inventario en tiempo real
- Sistema de carrito persistente para usuarios
- ~~Proceso de checkout optimizado~~ (Por Ver)
- Historial de pedidos y seguimiento
- Pasarela de pagos integrada
- ~~Sistema de cupones y descuentos~~ (Por Ver)
- Reseñas y valoraciones de productos

## 📋 Requisitos

```bash
# Instalar dependencias
uv sync

# Localizate en el entorno de Django / WOS
Set-Location myweb
# UNIX OS
cd myweb

# Ejecutar migraciones
python manage.py migrate

# Iniciar servidor / Windows OS
.\setup-dev.ps1
```

## 📁 Estructura
#TODO: ajustar al proyecto una vez avanzado
```
myweb/
├── 📂 myweb/                    # Configuración principal del proyecto
│   ├── ⚙️ settings.py           # Configuraciones de Django
│   ├── 🌐 urls.py               # URLs principales
│   └── 🚀 asgi.py               # Configuración ASGI
│
├── 📂 api/                      # Aplicaciones Django
│   ├── 👤 users/                # Gestión de usuarios
│   │   ├── 📄 models.py         # Modelos de usuario
│   │   ├── 🔗 api.py            # Endpoints con Django-Ninja
│   │   └── 🔐 auth.py           # Autenticación JWT
│   │
│   ├── 🛍️ products/            # Catálogo de productos
│   │   ├── 📄 models.py         # Modelos de productos
│   │   ├── 🔗 api.py            # API de productos
│   │   └── 🏷️ serializers.py   # Serializadores
│   │
│   ├── 🛒 cart/                 # Carrito de compras
│   │   ├── 📄 models.py         # Modelo del carrito
│   │   ├── 🔗 api.py            # API del carrito
│   │   └── ⚡ services.py       # Lógica de negocio
│   │
│   ├── 📦 orders/               # Gestión de pedidos
│   │   ├── 📄 models.py         # Modelos de pedidos
│   │   ├── 🔗 api.py            # API de pedidos
│   │   └── 📊 utils.py          # Utilidades
│   │
│   └── 💳 payments/             # Procesamiento de pagos
│       ├── 📄 models.py         # Modelos de pago
│       ├── 🔗 api.py            # API de pagos
│       └── 🏦 gateways.py       # Pasarelas de pago
│
├── 📂 static/                   # Archivos estáticos
├── 📂 media/                    # Archivos multimedia
│
├── 🐳 Dockerfile               # Configuración Docker
├── 🔧 docker-compose.yml       # Orquestación de contenedores
├── ⚙️ manage.py                # Comando de gestión Django
└── 📖 README.md                # Este archivo
```