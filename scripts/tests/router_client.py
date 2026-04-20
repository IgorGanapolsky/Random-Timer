class RouterClient:
    """
    Minimal request router for unit tests: map (method, path) -> response.

    - If the mapped value is an Exception, it is raised.
    - If the mapped value is callable, it is called and its return value is used.
    """

    def __init__(self, routes):
        self._routes = routes
        self.calls = []

    def request(self, method, path, *, params=None, payload=None):
        self.calls.append({"method": method, "path": path, "params": params, "payload": payload})
        key = (method, path)
        if key not in self._routes:
            raise RuntimeError(f"unhandled route {method} {path}")
        value = self._routes[key]
        if isinstance(value, Exception):
            raise value
        if callable(value):
            return value()
        return value

    def get_all(self, path: str, *, params=None):
        """Match ASCClient.get_all: one GET returning data[] (optionally paginated)."""
        data = self.request("GET", path, params=params or {})
        if not isinstance(data, dict):
            return []
        chunk = data.get("data") or []
        return chunk if isinstance(chunk, list) else []

