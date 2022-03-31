import json

from starlette.types import Scope, Receive, Send, Message
from starlette.datastructures import MutableHeaders
from fastapi.exceptions import HTTPException

from fastapi_xmlrpc.parser import XMLHandler


class XmlRpcMiddleware:

    def __init__(self, app, access_url: str):
        self.app = app
        self.message = {}
        self.initial_message: Message = {}
        self.access_url = access_url
        self.args = None
        self.name = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        self.headers = MutableHeaders(raw=scope['headers'])

        if not scope['path'] == self.access_url:
            return await self.app(scope, receive, send)
        if 'xml' not in self.headers['Content-Type']:
            raise HTTPException(status_code=402)

        self.scope = scope
        self.receive = receive
        self.send = send
        scope = await self.scope_with_xml_rpc(scope=scope.copy())

        await self.app(scope, self.receive_with_xml_rpc, self.send_with_xml_rpc)

    async def receive_with_xml_rpc(self):
        assert self.message["type"] == "http.request"
        body = json.dumps(*self.args).encode()
        self.message['body'] = body
        return self.message

    async def scope_with_xml_rpc(self, scope: Scope):
        self.message = await self.receive()
        self.name, self.args = await XMLHandler(xml_body=self.message['body']).handle()
        scope['path'] = await self._parse_url(name_call_function=self.name)
        self.headers['content-type'] = 'application/json'
        return scope

    async def send_with_xml_rpc(self, message: Message):
        match message.get('type'):
            case "http.response.start":
                self.initial_message = message

            case 'http.response.body':
                body = XMLHandler().build_xml(await XMLHandler().format_success(json.loads(message['body'])))

                headers = MutableHeaders(raw=self.initial_message["headers"])
                headers["Content-Type"] = "application/xml"
                headers["Content-Encoding"] = "utf-8"
                headers["Content-Length"] = str(len(body))
                message["body"] = body

                await self.send(self.initial_message)
                await self.send(message)

    @staticmethod
    async def _parse_url(name_call_function: str) -> str:
        return '/' + '/'.join(name_call_function.split('.'))
