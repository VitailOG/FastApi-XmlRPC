import orjson

from inspect import (
    signature,
    getfullargspec,
    Parameter
)
from functools import wraps
from typing import NamedTuple

from fastapi.params import Body
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Scope, Receive, Send, Message

from fastapi_xmlrpc.parser.exceptions import ParseError, InvalidArguments
from fastapi_xmlrpc.parser.parser import XMLRPCHandler
from fastapi_xmlrpc.responses import XMLRPCResponse
from fastapi_xmlrpc.routing import XmlRpcAPIRouter
from open_api.schema_generator import SchemaGenerator


class Error(BaseModel):
    faultCode: int
    faultMessage: str


class EndpointParam(NamedTuple):
    args: list[str]
    embed: bool


class XMLRPCResponder:

    __slots__ = (
        "app", "endpoints", "router", "scope", "message", "method_name", "method_args", "initial_message", "send"
    )

    def __init__(self, app: ASGIApp, *, endpoints: dict[str, EndpointParam], router: XmlRpcAPIRouter) -> None:
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

        if len(self.endpoints[self.scope['path']].args) < len(self.method_args):
            return await XMLRPCResponse(InvalidArguments('error'))(self.scope, receive, send)

        headers["Content-Type"] = "application/json"

        self.scope["path"] = self._gen_endpoint_path(self.method_name)

        self.send = send

        await self.app(self.scope, self.receive_with_xmlrpc, self.send_with_xmlrpc)

    async def receive_with_xmlrpc(self) -> Message:
        assert self.message["type"] == "http.request"

        body = ""

        # If endpoint has one or more arguments, send them as structure
        # where key is argument name and value is any supported type
        if len(self.method_args) > 1 or self.endpoints[self.scope["path"]].embed:
            args = dict(
                zip(
                    self.endpoints[self.scope["path"]].args,
                    self.method_args
                )
            )
            body = orjson.dumps(args)
        # If endpoint has only one argument, send json data as flat structure without argument key
        elif len(self.method_args) == 1:
            body = orjson.dumps(self.method_args[0])

        self.message["body"] = body

        return self.message

    async def send_with_xmlrpc(self, message: Message):
        match message.get('type'):
            case "http.response.start":
                self.initial_message = message

            case 'http.response.body':
                headers = MutableHeaders(raw=self.initial_message["headers"])

                if 'xml' in headers['content-type']:
                    await self._send(message)
                    return

                try:
                    message_body_loads = orjson.loads(message['body'])
                    body = XMLRPCHandler.format_success(message_body_loads)
                except orjson.JSONDecodeError:
                    body = message['body']

                headers["Content-Type"] = "application/xml"
                headers["Content-Encoding"] = "utf-8"
                headers["Content-Length"] = str(len(body))
                message["body"] = body

                await self._send(message)

    async def _send(self, message: Message):
        await self.send(self.initial_message)
        await self.send(message)

    def _gen_endpoint_path(self, method_name: str, namespace_separator=".") -> str:
        return self.router.prefix + "/" + method_name.replace(namespace_separator, "/", 1)


class XMLRPCMiddleware:
    __slots__ = ("app", "router", "endpoints")

    # On every add_middleware, add_exception_handler call, build_middleware_stack invoked
    # So every middleware is reinitialized
    def __init__(self, app: ASGIApp, *, router: XmlRpcAPIRouter):
        print('---')
        self.app = app
        self.router = router

        self.endpoints = {}

        for route in self.router.routes:
            sig = signature(route.endpoint)
            args = sig.parameters
            embed = False

            response = getattr(route, 'response_model') or str

            request_body = [
                arg.annotation for arg in args.values()
                if arg.default is Parameter.empty or type(arg.default) == Body
            ]

            method_name = route.path.replace('/', '.').lstrip('.')

            openapi_extra = {
                "requestBody": {
                    "content": {
                        "application/xml": {
                            "schema": SchemaGenerator()(
                                request_body, method_name=method_name
                            ).schema(ref_template="#/components/schemas/{model}")
                        }
                    },
                    "required": True,
                }
            }

            responses = {
                200: {
                    "content": {
                        "application/xml": {
                            "schema": SchemaGenerator()(
                                [response], res=True
                            ).schema(ref_template="#/components/schemas/{model}"),
                        }
                    },
                },
                500: {
                    "content": {
                        "application/xml": {
                            "schema": SchemaGenerator()(
                                [Error], res=True, is_fault=True
                            ).schema(ref_template="#/components/schemas/{model}"),
                        }
                    },
                },
            }

            route.openapi_extra = openapi_extra
            route.responses = responses

            if route.path in self.endpoints:
                raise ValueError(f"Duplicated {route.path} registered")

            if len(args) == 1 and getattr(args[list(args)[0]], 'default', False):
                if getattr(sig.parameters[list(args)[0]].default, "embed", False):
                    embed = True

            self.endpoints[route.path] = EndpointParam(args=getfullargspec(route.endpoint).args, embed=embed)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        headers = MutableHeaders(raw=scope["headers"])

        # Check Content-Type header
        content_type_header = headers.get("Content-Type", '')

        if "xml" in content_type_header:
            responder = XMLRPCResponder(self.app, endpoints=self.endpoints, router=self.router)
            await responder(scope, receive, send)
            return

        await self.app(scope, receive, send)
