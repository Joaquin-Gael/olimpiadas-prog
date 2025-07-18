import os

from django.core.asgi import get_asgi_application
from django.conf import settings

from rich.console import Console
from rich.panel import Panel

console = Console()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb.settings')


class LifespanWrapper:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                msg = await receive()
                if msg["type"] == "lifespan.startup":
                    console.rule("[bold green]🔍 Documentación Scalar activa[/bold green]")
                    mensaje = (
                        "[bold cyan]✅ La documentación de tu API está disponible en:[/bold cyan]\n"
                        f"  [bold magenta]http://localhost:8080/{settings.ID_PREFIX}/scalar[/bold magenta]\n\n"
                        "[dim]Permanecerá accesible mientras debug esté activado.[/dim]"
                    )
                    console.print(
                        Panel.fit(
                            mensaje,
                            title="[bold yellow]📚 Scalar Docs[/bold yellow]",
                            border_style="bright_blue",
                            padding=(1, 2),
                        )
                    )
                    await send({"type": "lifespan.startup.complete"})
                elif msg["type"] == "lifespan.shutdown":
                    console.rule("[red]🛑 Server Closed[/red]")
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        await self.app(scope, receive, send)

django_asgi_app = get_asgi_application()

application = LifespanWrapper(django_asgi_app)