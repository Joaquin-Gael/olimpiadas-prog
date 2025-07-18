from django.contrib import admin
#from django.http.response import StreamingHttpResponse
from django.urls import path, re_path
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.shortcuts import render
#from django.conf.urls.static import static
from django.http import FileResponse
from pathlib import Path

import json
import os
from enum import Enum
from typing_extensions import Annotated, Doc

from ninja import NinjaAPI, Router

from api.users.urls import user_router
from api.products.views_products import products_router
from api.products.views_package import package_router, category_router
from api.products.views_supliers import suppliers_router
from api.products.views_audit import audit_router
from api.employees.views_employees import router as employees_router
from api.store.views_cart import router as store_router
from api.store.views_orders import orders_router
from api.store.views_sales import router as sales_router
from api.clients.views import router as clients_router

from api.core.notification.services import test_email_templates

id_prefix = settings.ID_PREFIX

api = NinjaAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url=None,
    openapi_url=f"{id_prefix}/openapi.json",
)

# Agregar las rutas de usuarios
api.add_router("/users/", user_router)
# Agregar las rutas de products
api.add_router("/products/", products_router)
# Agregar las rutas de package
api.add_router("/packages/", package_router)
# Agregar las rutas de categorías
api.add_router("/categories/", category_router)
# Agregar las rutas de suppliers
api.add_router("/suppliers/", suppliers_router)
# Agregar las rutas de employees
api.add_router("/employees/", employees_router)
# Agregar las rutas de store
api.add_router("/store/", store_router)
# Agregar las rutas de orders
api.add_router("/orders/", orders_router)
# Agregar las rutas de sales
api.add_router("/sales/", sales_router)
# Agregar las rutas de auditoría
api.add_router("/audit/", audit_router)
# Agregar las rutas de clients
api.add_router("/clients/", clients_router)

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

@api.get("/scalar", include_in_schema=False)
async def scalar_html(request):
    return get_scalar_api_reference(
        openapi_url=api.openapi_url,
        title=api.title,
        hide_download_button=True,
        layout=Layout.MODERN,
        dark_mode=True,
        scalar_favicon_url="/assets/img/logo-rest-doc.png"
    )



@api.get("/test/stripe", include_in_schema=False)
async def stripe_html(request):
    return render(request, "stripe_test.html", {"secret_public":settings.STRIPE_PUBLISHABLE_KEY})

@api.get("/test/email", include_in_schema=False)
def email_html(request):
    test_email_templates()


def get_secret(request):
    return JsonResponse({"id_prefix_api_secret": str(id_prefix)})

def index_view(request):
    return render(request, "index.csr.html")

async def media_controller(request, path_to_file: str):
    try:
        file_path = Path(os.path.join(settings.MEDIA_ROOT, path_to_file))

        if not file_path.exists():
            return HttpResponse(f"Archivo no encontrado: {file_path}", status=404)

        content_type = f"image/{file_path.suffix.lstrip('.')}"

        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            as_attachment=False
        )

        response['Content-Disposition'] = f'inline; filename="{file_path.name}"'
        
        return response
        
    except Exception as e:
        return HttpResponse(f"Error al acceder al archivo: {str(e)}", status=500)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('id_prefix_api_secret/', get_secret),
    path(f'{str(id_prefix)}/', api.urls),
    path('', index_view, name="index"),
    path("home/", index_view, name="home"),
    path("packets/", index_view, name="packets"),
    path("contact/", index_view, name="contact"),
    path("register/", index_view, name="register"),
    path("login/", index_view, name="login"),
    path("user_panel/", index_view, name="user_panel"),
    path("cart/", index_view, name="cart"),
    path("checkout/success", index_view, name="checkout_success"),
    path("checkout/cancel", index_view, name="checkout_cancel"),
    path('media/<str:path_to_file>', media_controller),
]

#urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)