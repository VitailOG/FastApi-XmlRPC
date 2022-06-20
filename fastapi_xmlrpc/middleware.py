import inspect

import orjson
from fastapi.responses import PlainTextResponse
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Scope, Receive, Send, Message

from fastapi_xmlrpc.parser.exceptions import ParseError
from fastapi_xmlrpc.parser.parser import XMLRPCHandler
from fastapi_xmlrpc.responses import XMLRPCResponse
from fastapi_xmlrpc.routing import XmlRpcAPIRouter


class XMLRPCResponder:
    __slots__ = (
        "app", "endpoints", "router", "scope", "message", "method_name", "method_args", "initial_message", "send"
    )

    def __init__(self, app: ASGIApp, *, endpoints: dict[str, list[str]], router: XmlRpcAPIRouter) -> None:
        self.app = app
        self.endpoints = endpoints
        self.router = router

        self.scope: Scope = {}
        self.message: Message = {}

        self.method_name = None
        self.method_args = None

        self.initial_message = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.scope = scope.copy()

        headers = MutableHeaders(scope=self.scope)

        # Check Content-Type header
        content_type_header = headers.get("Content-Type")
        if content_type_header is None:
            response = PlainTextResponse(
                "Content-Type header not found",
                status_code=400
            )
            return await response(self.scope, receive, send)
        elif "xml" not in content_type_header:
            response = PlainTextResponse(
                f"Bad Content-Type header, {content_type_header} is not supported",
                status_code=400
            )
            return await response(self.scope, receive, send)

        self.message = await receive()

        # Read body
        body = self.message["body"]
        while self.message.get("more_body", False):
            self.message = await receive()
            body += self.message["body"]

        # Check Content-Length header
        body_length = len(body)
        content_length_header = headers.get("Content-Length")
        if content_length_header is None:
            response = PlainTextResponse(
                "Content-Length header not found",
                status_code=400
            )
            return await response(self.scope, receive, send)
        elif int(content_length_header) != body_length:
            response = PlainTextResponse(
                f"Content-Length header value and body length mismatch, {content_length_header} != {body_length}",
                status_code=400
            )
            return await response(self.scope, receive, send)

        try:
            self.method_name, self.method_args = XMLRPCHandler.handle(body)
        except ParseError as exc:
            return await XMLRPCResponse(exc)(self.scope, receive, send)

        headers["Content-Type"] = "application/json"

        self.scope["path"] = self._gen_endpoint_path(self.method_name)

        self.send = send

        #  todo
        await self.app(self.scope, self.receive_with_xmlrpc, self.send_with_xmlrpc)

    async def receive_with_xmlrpc(self) -> Message:
        assert self.message["type"] == "http.request"

        body = ""

        # If endpoint has one or more arguments, send them as structure
        # where key is argument name and value is any supported type
        if len(self.method_args) > 1:
            args = dict(
                zip(
                    self.endpoints[self.scope["path"]],
                    self.method_args
                )
            )
            body = orjson.dumps(args)
        # If endpoint has only one argument, send json data as flat structure without argument key
        elif len(self.method_args) == 1:
            body = orjson.dumps(self.method_args[0])

        self.message["body"] = body

        return self.message

    #  todo
    async def send_with_xmlrpc(self, message: Message):
        match message.get('type'):
            case "http.response.start":
                self.initial_message = message

            case 'http.response.body':

                try:
                    message_body_loads = orjson.loads(message['body'])
                    body = XMLRPCHandler.format_success(message_body_loads)
                except orjson.JSONDecodeError:
                    body = message['body']

                headers = MutableHeaders(raw=self.initial_message["headers"])
                headers["Content-Type"] = "application/xml"
                headers["Content-Encoding"] = "utf-8"
                headers["Content-Length"] = str(len(body))
                message["body"] = body

                await self.send(self.initial_message)
                await self.send(message)

    def _gen_endpoint_path(self, method_name: str, namespace_separator=".") -> str:
        return self.router.prefix + "/" + method_name.replace(namespace_separator, "/", 1)


class XMLRPCMiddleware:
    __slots__ = ("app", "router", "endpoints")

    # On every add_middleware, add_exception_handler call, build_middleware_stack invoked
    # So every middleware is reinitialized
    def __init__(self, app: ASGIApp, *, router: XmlRpcAPIRouter):
        self.app = app
        self.router = router

        self.endpoints = {}

        for route in self.router.routes:
            if route.path in self.endpoints:
                raise ValueError(f"Duplicated {route.path} registered")

            self.endpoints[route.path] = inspect.getfullargspec(route.endpoint).args

    async def __call__(self, scope: Scope, receive: Receive, send: Send):

        headers = MutableHeaders(raw=scope['headers'])
        content_type_header = headers.get("Content-Type")

        #  todo
        if 'xml' in content_type_header:
            headers['test'] = 'xml'
            responder = XMLRPCResponder(self.app, endpoints=self.endpoints, router=self.router)
            await responder(scope, receive, send)
            return

        await self.app(scope, receive, send)


"""
class XmlRpcMiddleware:

    def __init__(self, app, access_url: str):
        self.app = app
        self.message = {}
        self.initial_message: Message = {}
        self.access_url = access_url
        self.args = None
        self.name = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        print('middle')
        self.headers = MutableHeaders(raw=scope['headers'])

        if not scope['path'] == self.access_url:
            return await self.app(scope, receive, send)
        if 'xml' not in self.headers['Content-Type']:
            return await self.app(scope, receive, send)
            # raise exceptions.HTTPException(status_code=402)

        self.receive = receive
        self.send = send
        scope = await self.scope_with_xml_rpc(scope=scope.copy())

        await self.app(scope, self.receive_with_xml_rpc, self.send_with_xml_rpc)

    async def receive_with_xml_rpc(self):
        assert self.message["type"] == "http.request"
        body = orjson.dumps(*self.args)
        self.message['body'] = body
        return self.message

    async def scope_with_xml_rpc(self, scope: Scope):
        self.message = await self.receive()
        self.name, self.args = await XMLHandler(xml_body=self.message['body']).handle()
        print(self.name, self.args)
        scope['path'] = await self._parse_url(name_call_function=self.name)
        self.headers['content-type'] = 'application/json'
        return scope

    async def send_with_xml_rpc(self, message: Message):
        match message.get('type'):
            case "http.response.start":
                self.initial_message = message

            case 'http.response.body':
                if self.initial_message['status'] == status.HTTP_200_OK:
                    body = XMLHandler().build_xml(await XMLHandler().format_success(orjson.loads(message['body'])))
                else:
                    decode_data = message['body'].decode()
                    body = orjson.loads(decode_data)['errors'].encode()

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
"""
