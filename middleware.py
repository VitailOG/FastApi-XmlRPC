import json

from starlette.types import Scope, Receive, Send
from starlette.datastructures import Headers


class XmlRpcMiddleware:
    def __init__(self, app) -> None:
        self.app = app
        self.headers = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        self.receive = receive
        scope = await self._scope(scope=scope)
        await self.app(scope, self._receive, send)

    async def _receive(self):
        receive = await self.receive()
        assert receive['type'] == "http.request"

        data = json.loads(receive.get('body'))
        return data

    # async def make_send(self):
    #     pass

    async def _scope(self, scope: Scope):
        self.headers = Headers(scope=scope)
        return scope
