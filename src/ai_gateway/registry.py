from __future__ import annotations

from .handlers import Handler


class HandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register(self, route: str, handler: Handler) -> None:
        if not route:
            raise ValueError("route must not be empty")
        self._handlers[route] = handler

    def get(self, route: str) -> Handler:
        try:
            return self._handlers[route]
        except KeyError as error:
            raise LookupError(f"no handler registered for route '{route}'") from error

    @property
    def routes(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))
