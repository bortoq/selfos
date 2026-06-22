"""
WebInterface — заготовка веб-интерфейса для Self OS (Phase 3, Этап 5).

В будущем здесь будет FastAPI / Flask приложение.
"""



class WebInterface:
    """
    Заготовка веб-интерфейса Self OS.
    """

    def __init__(self) -> None:
        self.routes: dict[str, str] = {
            "/": "Self OS Dashboard (coming soon)",
            "/status": "System status",
            "/context": "Context Engine",
            "/delegate": "Delegation management"
        }

    def get_route(self, path: str) -> str:
        return self.routes.get(path, "404 - Not Found")

    def list_routes(self) -> dict[str, str]:
        return self.routes


# Глобальный экземпляр
web_interface = WebInterface()