import json
from xml.etree.ElementTree import XML, indent, tostring

from starlette.types import Scope, Receive, Send
from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException

from fastapi_xmlrpc.parser import XMLHandler


class XmlRpcMiddleware:

    def __init__(self, app, access_url: str):
        self.app = app
        self.headers = None
        self.message = None
        self.access_url = access_url

    async def __call__(self, scope: Scope, receive: Receive, send: Send):

        if not scope['path'] == self.access_url:
            return await self.app(scope, receive, send)

        self.receive = receive
        self.send = send
        self.scope = scope.copy()
        scope = await self.scope_with_xml_rpc(scope=scope)
        await self.app(scope, self.receive_with_xml_rpc, self.send_with_xml_rpc)

    async def receive_with_xml_rpc(self):
        print('receive')
        assert self.message["type"] == "http.request"
        handle = await XMLHandler(xml_body=self.message['body']).handle(return_name_endpoint=False)
        body = json.dumps(*handle).encode()
        self.message['body'] = body
        return self.message

    async def scope_with_xml_rpc(self, scope: Scope):
        print('scope')
        self.message = await self.receive()
        name = await XMLHandler(xml_body=self.message['body']).handle()
        scope['path'] = await self._parse_url(name_call_function=name)
        return scope

    async def send_with_xml_rpc(self, message: dict):
        print('send')
        match message.get('type'):
            case 'http.response.start':
                return await self.send(message)
            case 'http.response.body':
                res = XMLHandler().build_xml(await XMLHandler().format_success(json.loads(message.get('body'))))
                element = XML(res)
                indent(element)
                print(tostring(element, encoding='unicode'))

        await self.send(message)

    @staticmethod
    async def _parse_url(name_call_function: str) -> str:
        return '/' + '/'.join(name_call_function.split('.'))
