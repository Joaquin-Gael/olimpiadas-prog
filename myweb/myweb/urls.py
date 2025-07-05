from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.views.static import serve
from django.conf import settings

import json
from enum import Enum
from typing_extensions import Annotated, Doc

from ninja import NinjaAPI, Router

from api.users.urls import user_router
from api.products.views_products import products_router
from api.products.views_package import package_router, category_router
from api.products.views_supliers import suppliers_router
from api.employees.views_employees import router as employees_router
from api.store.views_cart import router as store_router
from api.store.views_orders import router as orders_router
from api.store.views_sales import router as sales_router
from api.clients.views import router as clients_router

id_prefix = settings.ID_PREFIX

main_router = Router()

# Agregar las rutas de usuarios
main_router.add_router("/users/", user_router)
# Agregar las rutas de products
main_router.add_router("/products/", products_router)
# Agregar las rutas de package
main_router.add_router("/packages/", package_router)
# Agregar las rutas de categorías
main_router.add_router("/categories/", category_router)
# Agregar las rutas de suppliers
main_router.add_router("/suppliers/", suppliers_router)
# Agregar las rutas de employees
main_router.add_router("/employees/", employees_router)
# Agregar las rutas de store
main_router.add_router("/store/", store_router)
# Agregar las rutas de orders
main_router.add_router("/orders/", orders_router)
# Agregar las rutas de sales
main_router.add_router("/sales/", sales_router)
# Agregar las rutas de clients
main_router.add_router("/clients/", clients_router)

class Layout(Enum):
    MODERN = "modern"
    CLASSIC = "classic"


class SearchHotKey(Enum):
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"
    F = "f"
    G = "g"
    H = "h"
    I = "i"
    J = "j"
    K = "k"
    L = "l"
    M = "m"
    N = "n"
    O = "o"
    P = "p"
    Q = "q"
    R = "r"
    S = "s"
    T = "t"
    U = "u"
    V = "v"
    W = "w"
    X = "x"
    Y = "y"
    Z = "z"


scalar_theme = """
/* basic theme */
.light-mode {
  --scalar-color-1: #2a2f45;
  --scalar-color-2: #757575;
  --scalar-color-3: #8e8e8e;
  --scalar-color-accent: #009485;

  --scalar-background-1: #fff;
  --scalar-background-2: #fcfcfc;
  --scalar-background-3: #f8f8f8;
  --scalar-background-accent: #ecf8f6;

  --scalar-border-color: rgba(0, 0, 0, 0.1);
}
.dark-mode {
  --scalar-color-1: rgba(255, 255, 255, 0.9);
  --scalar-color-2: rgba(255, 255, 255, 0.62);
  --scalar-color-3: rgba(255, 255, 255, 0.44);
  --scalar-color-accent: #00ccb8;

  --scalar-background-1: #1f2129;
  --scalar-background-2: #282a35;
  --scalar-background-3: #30323d;
  --scalar-background-accent: #223136;

  --scalar-border-color: rgba(255, 255, 255, 0.1);
}
/* Document Sidebar */
.light-mode .t-doc__sidebar {
  --sidebar-background-1: var(--scalar-background-1);
  --sidebar-item-hover-color: currentColor;
  --sidebar-item-hover-background: var(--scalar-background-2);
  --sidebar-item-active-background: var(--scalar-background-accent);
  --sidebar-border-color: var(--scalar-border-color);
  --sidebar-color-1: var(--scalar-color-1);
  --sidebar-color-2: var(--scalar-color-2);
  --sidebar-color-active: var(--scalar-color-accent);
  --sidebar-search-background: transparent;
  --sidebar-search-border-color: var(--scalar-border-color);
  --sidebar-search--color: var(--scalar-color-3);
}

.dark-mode .sidebar {
  --sidebar-background-1: var(--scalar-background-1);
  --sidebar-item-hover-color: currentColor;
  --sidebar-item-hover-background: var(--scalar-background-2);
  --sidebar-item-active-background: var(--scalar-background-accent);
  --sidebar-border-color: var(--scalar-border-color);
  --sidebar-color-1: var(--scalar-color-1);
  --sidebar-color-2: var(--scalar-color-2);
  --sidebar-color-active: var(--scalar-color-accent);
  --sidebar-search-background: transparent;
  --sidebar-search-border-color: var(--scalar-border-color);
  --sidebar-search--color: var(--scalar-color-3);
}

/* advanced */
.light-mode {
  --scalar-button-1: rgb(49 53 56);
  --scalar-button-1-color: #fff;
  --scalar-button-1-hover: rgb(28 31 33);

  --scalar-color-green: #009485;
  --scalar-color-red: #d52b2a;
  --scalar-color-yellow: #ffaa01;
  --scalar-color-blue: #0a52af;
  --scalar-color-orange: #953800;
  --scalar-color-purple: #8251df;

  --scalar-scrollbar-color: rgba(0, 0, 0, 0.18);
  --scalar-scrollbar-color-active: rgba(0, 0, 0, 0.36);
}
.dark-mode {
  --scalar-button-1: #f6f6f6;
  --scalar-button-1-color: #000;
  --scalar-button-1-hover: #e7e7e7;

  --scalar-color-green: #00ccb8;
  --scalar-color-red: #e5695b;
  --scalar-color-yellow: #ffaa01;
  --scalar-color-blue: #78bffd;
  --scalar-color-orange: #ffa656;
  --scalar-color-purple: #d2a8ff;

  --scalar-scrollbar-color: rgba(255, 255, 255, 0.24);
  --scalar-scrollbar-color-active: rgba(255, 255, 255, 0.48);
}
:root {
  --scalar-radius: 3px;
  --scalar-radius-lg: 6px;
  --scalar-radius-xl: 8px;
}
.scalar-card:nth-of-type(3) {
  display: none;
}"""

def get_scalar_api_reference(
        *,
        openapi_url: Annotated[
            str,
            Doc(
                """
                The OpenAPI URL that Scalar should load and use.
                This is normally done automatically by FastAPI using the default URL
                `/openapi.json`.
                """
            ),
        ],
        title: Annotated[
            str,
            Doc(
                """
                The HTML `<title>` content, normally shown in the browser tab.
                """
            ),
        ],
        scalar_js_url: Annotated[
            str,
            Doc(
                """
                The URL to use to load the Scalar JavaScript.
                It is normally set to a CDN URL.
                """
            ),
        ] = "https://cdn.jsdelivr.net/npm/@scalar/api-reference",
        scalar_proxy_url: Annotated[
            str,
            Doc(
                """
                The URL to use to set the Scalar Proxy.
                It is normally set to a Scalar API URL (https://proxy.scalar.com), but default is empty
                """
            ),
        ] = "",
        scalar_favicon_url: Annotated[
            str,
            Doc(
                """
                The URL of the favicon to use. It is normally shown in the browser tab.
                """
            ),
        ] = "https://fastapi.tiangolo.com/img/favicon.png",
        scalar_theme: Annotated[
            str,
            Doc(
                """
                Custom CSS theme for Scalar.
                """
            ),
        ] = scalar_theme,
        layout: Annotated[
            Layout,
            Doc(
                """
                The layout to use for Scalar.
                Default is "modern".
                """
            ),
        ] = Layout.MODERN,
        show_sidebar: Annotated[
            bool,
            Doc(
                """
                A boolean to show the sidebar.
                Default is True which means the sidebar is shown.
                """
            ),
        ] = True,
        hide_download_button: Annotated[
            bool,
            Doc(
                """
                A boolean to hide the download button.
                Default is False which means the download button is shown.
                """
            ),
        ] = False,
        hide_models: Annotated[
            bool,
            Doc(
                """
                A boolean to hide all models.
                Default is False which means all models are shown.
                """
            ),
        ] = False,
        dark_mode: Annotated[
            bool,
            Doc(
                """
                Whether dark mode is on or off initially (light mode).
                Default is True which means dark mode is used.
                """
            ),
        ] = True,
        search_hot_key: Annotated[
            SearchHotKey,
            Doc(
                """
                The hotkey to use for search.
                Default is "k" (e.g. CMD+k).
                """
            ),
        ] = SearchHotKey.K,
        hidden_clients: Annotated[
            bool | dict[str, bool | list[str]] | list[str],
            Doc(
                """
                A dictionary with the keys being the target names and the values being a boolean to hide all clients of the target or a list clients.
                If a boolean is provided, it will hide all the clients with that name.
                Backwards compatibility: If a list of strings is provided, it will hide the clients with the name and the list of strings.
                Default is [] which means no clients are hidden.
                """
            ),
        ] = [],
        servers: Annotated[
            list[dict[str, str]],
            Doc(
                """
                A list of dictionaries with the keys being the server name and the value being the server URL.
                Default is [] which means no servers are provided.
                """
            ),
        ] = [],
        default_open_all_tags: Annotated[
            bool,
            Doc(
                """
                A boolean to open all tags by default.
                Default is False which means all tags are closed by default.
                """
            ),
        ] = False,
) -> HttpResponse:
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>{title}</title>
    <!-- needed for adaptive design -->
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="shortcut icon" href="{scalar_favicon_url}">
    <style>
      body {{
        margin: 0;
        padding: 0;
      }}
    </style>
    <style>
    {scalar_theme}
    </style>
    </head>
    <body>
    <noscript>
        Scalar requires Javascript to function. Please enable it to browse the documentation.
    </noscript>
    <script
      id="api-reference"
      data-url="{openapi_url}"
      data-proxy-url="{scalar_proxy_url}"></script>
    <script>
      var configuration = {{
        layout: "{layout.value}",
        showSidebar: {json.dumps(show_sidebar)},
        hideDownloadButton: {json.dumps(hide_download_button)},
        hideModels: {json.dumps(hide_models)},
        darkMode: {json.dumps(dark_mode)},
        searchHotKey: "{search_hot_key.value}",
        hiddenClients: {json.dumps(hidden_clients)},
        servers: {json.dumps(servers)},
        defaultOpenAllTags: {json.dumps(default_open_all_tags)},
      }}

      document.getElementById('api-reference').dataset.configuration =
        JSON.stringify(configuration)
    </script>
    <script src="{scalar_js_url}"></script>
    </body>
    </html>
    """
    return HttpResponse(html)

@main_router.get("/scalar", include_in_schema=False)
async def scalar_html(request):
    return get_scalar_api_reference(
        openapi_url=api.openapi_url,
        title=api.title,
        hide_download_button=True,
        layout=Layout.MODERN,
        dark_mode=True,
        scalar_favicon_url="/assets/img/logo-rest-doc.png"
    )

api = NinjaAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url=None
)

@api.get("/test/stripe", include_in_schema=False)
async def stripe_html(request):
    return HttpResponse(
        """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finalizar Compra</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <!-- Importar la librería de Stripe -->
    <script src="https://js.stripe.com/v3/"></script>
</head>
<body class="bg-gray-100 font-sans">
    <div class="container mx-auto p-6 max-w-4xl">
        <!-- Encabezado -->
        <h1 class="text-3xl font-bold text-gray-800 mb-6">Finalizar Compra</h1>

        <!-- Resumen del carrito -->
        <div class="bg-white shadow-md rounded-lg p-6 mb-6">
            <h2 class="text-xl font-semibold text-gray-700 mb-4">Resumen del Carrito</h2>
            <ul class="space-y-4">
                <li class="flex justify-between">
                    <span class="text-gray-600">Producto de prueba</span>
                    <span class="font-medium">$29.99</span>
                </li>
                <li class="flex justify-between border-t pt-4">
                    <span class="text-gray-800 font-semibold">Total</span>
                    <span class="text-gray-800 font-semibold">$29.99</span>
                </li>
            </ul>
        </div>

        <!-- Formulario de pago con Stripe Elements -->
        <div class="bg-white shadow-md rounded-lg p-6">
            <h2 class="text-xl font-semibold text-gray-700 mb-4">Información de Pago</h2>
            <div id="card-element" class="p-3 border rounded-lg"></div>
            <div id="card-errors" class="text-red-500 mt-2"></div>
            <button id="submit-button" class="mt-4 bg-blue-600 hover:bg-blue-800 text-white font-bold py-3 px-6 rounded-lg transition duration-300" disabled>
                Pagar
            </button>
        </div>
    </div>

    <!-- Modal de Login -->
    <div id="login-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center hidden">
        <div class="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 class="text-xl font-semibold text-gray-700 mb-4">Iniciar Sesión</h2>
            <div id="login-error" class="text-red-500 mb-4"></div>
            <input id="email" type="email" placeholder="Correo electrónico" class="w-full p-3 mb-4 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <input id="password" type="password" placeholder="Contraseña" class="w-full p-3 mb-4 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <button id="login-button" class="w-full bg-blue-600 hover:bg-blue-800 text-white font-bold py-3 px-6 rounded-lg transition duration-300">
                Iniciar Sesión
            </button>
            <button id="close-login" class="mt-2 w-full bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-3 px-6 rounded-lg transition duration-300">
                Cancelar
            </button>
        </div>
    </div>

    <script>
        // Inicializar Stripe con la clave pública
        const stripe = Stripe('tu_clave_publica'); // Reemplaza con tu clave pública de Stripe
        const elements = stripe.elements();
        const card = elements.create('card', {
            style: {
                base: {
                    fontSize: '16px',
                    color: '#32325d',
                },
            },
        });
        card.mount('#card-element');

        // Manejo de errores en el formulario de pago
        card.on('change', (event) => {
            const displayError = document.getElementById('card-errors');
            if (event.error) {
                displayError.textContent = event.error.message;
            } else {
                displayError.textContent = '';
            }
        });

        // Función para obtener el token CSRF
        function getCsrfToken() {
            const name = 'csrftoken';
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [key, value] = cookie.trim().split('=');
                if (key === name) return value;
            }
            return '';
        }
        
        function generateUUIDv4() {
            return crypto.randomUUID();
        }

        // Obtener el id_prefix de la API
        let idPrefix = '';
        let isLoggedIn = false;
        async function fetchIdPrefix() {
            try {
                console.log('Obteniendo id_prefix desde /id_prefix_api_secret/');
                const response = await fetch('/id_prefix_api_secret/', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });
                if (!response.ok) {
                    throw new Error(`Error al obtener id_prefix: ${response.status} - ${await response.text()}`);
                }
                const data = await response.json();
                if (!data.id_prefix_api_secret) {
                    throw new Error('No se recibió id_prefix_api_secret en la respuesta');
                }
                idPrefix = data.id_prefix_api_secret;
                console.log('id_prefix recibido:', idPrefix);
                // Mostrar el modal de login después de obtener el id_prefix
                document.getElementById('login-modal').classList.remove('hidden');
            } catch (error) {
                console.error('Error al obtener id_prefix:', error.message);
                document.getElementById('card-errors').textContent = `Error: ${error.message}`;
            }
        }

        // Manejo del login
        document.getElementById('login-button').addEventListener('click', async () => {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const loginError = document.getElementById('login-error');

            if (!email || !password) {
                loginError.textContent = 'Por favor, ingresa correo y contraseña';
                return;
            }

            try {
                console.log('Iniciando solicitud a /users/login');
                const loginResponse = await fetch(`/${idPrefix}/users/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify({ email, password }),
                });
                if (!loginResponse.ok) {
                    const errorText = await loginResponse.text();
                    throw new Error(`Error en /users/login: ${loginResponse.status} - ${errorText}`);
                }
                const loginData = await loginResponse.json();
                console.log('Login exitoso:', loginData);
                localStorage.setItem('access_token', loginData.data.access_token);
                isLoggedIn = true;
                document.getElementById('login-modal').classList.add('hidden');
                document.getElementById('submit-button').disabled = false; // Habilitar el botón de pago
            } catch (error) {
                console.error('Error durante el login:', error.message);
                loginError.textContent = `Error: ${error.message}`;
            }
        });

        // Cerrar el modal de login
        document.getElementById('close-login').addEventListener('click', () => {
            document.getElementById('login-modal').classList.add('hidden');
        });

        // Iniciar el flujo al cargar la página
        fetchIdPrefix();

        document.getElementById('submit-button').addEventListener('click', async () => {
            if (!isLoggedIn) {
                document.getElementById('card-errors').textContent = 'Debes iniciar sesión primero';
                document.getElementById('login-modal').classList.remove('hidden');
                return;
            }

            if (!idPrefix) {
                document.getElementById('card-errors').textContent = 'No se pudo obtener el prefijo de la API. Por favor, recarga la página.';
                return;
            }

            try {
                // Paso 1: Llamar a /{id_prefix}/cart/checkout/ para obtener el order_id
                console.log(`Iniciando solicitud a /${idPrefix}/cart/checkout/`);
                const checkoutResponse = await fetch(`/${idPrefix}/store/cart/checkout/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                        'Referer': `https://localhost:8080/${idPrefix}/store/cart/`,
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                        'Idempotency-Key': generateUUIDv4(),
                    },
                });
                if (!checkoutResponse.ok) {
                    const errorText = await checkoutResponse.text();
                    throw new Error(`Error en /${idPrefix}/cart/checkout/: ${checkoutResponse.status} - ${errorText}`);
                }
                const checkoutData = await checkoutResponse.json();
                if (!checkoutData.order_id) {
                    throw new Error('No se recibió order_id en la respuesta de /cart/checkout/');
                }
                const orderId = checkoutData.order_id;
                console.log('Order ID recibido:', orderId);

                // Paso 2: Llamar a /{id_prefix}/orders/{order_id}/pay para obtener el client_secret
                console.log(`Iniciando solicitud a /${idPrefix}/orders/${orderId}/pay`);
                const payResponse = await fetch(`/${idPrefix}/orders/${orderId}/pay`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                });
                if (!payResponse.ok) {
                    const errorText = await payResponse.text();
                    throw new Error(`Error en /${idPrefix}/orders/${orderId}/pay: ${payResponse.status} - ${errorText}`);
                }
                const payData = await payResponse.json();
                if (!payData.client_secret) {
                    throw new Error('No se recibió client_secret en la respuesta de /orders/{order_id}/pay');
                }
                const clientSecret = payData.client_secret;
                console.log('Client Secret recibido:', clientSecret);

                // Paso 3: Confirmar el pago con Stripe Elements
                const result = await stripe.confirmCardPayment(clientSecret, {
                    payment_method: {
                        card: card,
                        billing_details: {
                            name: 'Cliente de Prueba',
                        },
                    },
                });

                if (result.error) {
                    document.getElementById('card-errors').textContent = result.error.message;
                    console.error('Error al confirmar el pago:', result.error.message);
                } else {
                    console.log('Pago exitoso:', result.paymentIntent);
                    alert('Pago exitoso');
                    window.location.href = '/success';
                }
            } catch (error) {
                console.error('Error durante el proceso de pago:', error.message);
                document.getElementById('card-errors').textContent = `Error: ${error.message}`;
            }
        });
    </script>
</body>
</html>
        """
    )

@api.get("/id_prefix_api_secret/", include_in_schema=False)
async def get_secret(request):
    return {"id_prefix_api_secret": str(id_prefix)}

api.add_router(f"/{str(id_prefix)}/", main_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api.urls)
]