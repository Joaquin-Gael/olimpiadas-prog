from ninja import NinjaAPI

api = NinjaAPI(
    title="Olimpiadas-API",
    version="0.0.1"
)

@api.get("/ping")
def ping(request):
    return {"ping": "pong!"}
