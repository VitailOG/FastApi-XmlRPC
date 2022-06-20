import typing

from starlette.responses import Response

from fastapi_xmlrpc.parser.parser import XMLRPCHandler


class XMLRPCResponse(Response):
    media_type = "application/xml"

    def render(self, content: typing.Any) -> bytes:
        if isinstance(content, Exception):
            return XMLRPCHandler.format_error(content)

        return XMLRPCHandler.format_success(content)
