from starlette.types import Scope, Receive, Send
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException

from fastapi_xmlrpc.parser import XMLHandler


class XmlRpcMiddleware:

    def __init__(self, app):
        self.app = app
        self.headers = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        self.receive = receive
        scope = await self._scope(scope=scope)
        receive = await self._receive()
        await self.app(scope, receive, send)

    async def _receive(self):
        pass
    #     receive = await self.receive()
    #     handle = Handle(receive['body'])
    #     print(await handle.handle())
        # data = json.loads(receive.get('body'))
        # return data

    # async def _send(self):
    #     assert receive['type'] == "http.request"
    #     pass

    async def _scope(self, scope: Scope):
        self.headers = Headers(scope=scope)
        receive = await self.receive()
        handle = XMLHandler(receive['body'])
        name = await handle.handle()
        scope['path'] = await self._parse_url(name_call_function=name)
        return scope

    @staticmethod
    async def _parse_url(name_call_function: str) -> str:
        return '/' + '/'.join(name_call_function.split('.'))
