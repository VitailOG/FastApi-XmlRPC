import asyncio

from aiohttp_xmlrpc.common import schema, py2xml, xml2py
from lxml import etree


class XMLHandler:

    def __init__(self, xml_body=None):
        self.xml_body = xml_body
        self.THREAD_POOL_EXECUTOR = None

    async def handle(self, return_name_endpoint: bool = True):
        xml_request = await self.parse_body()

        full_method_name = xml_request.xpath("//methodName[1]")[0].text

        if return_name_endpoint:
            return full_method_name

        args = list(
                map(
                    xml2py,
                    xml_request.xpath("//params/param/value")
                )
            )

        return args

    async def parse_body(self):
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                self.THREAD_POOL_EXECUTOR,
                self.parse_xml,
                self.xml_body
            )
        except etree.DocumentInvalid:
            pass

    @staticmethod
    def parse_xml(xml_string: str):
        parse = etree.XMLParser(resolve_entities=False)
        root = etree.fromstring(xml_string, parse)
        schema.assertValid(root)
        return root

    @staticmethod
    async def format_error(exception: Exception):
        xml_response = etree.Element("methodResponse")
        xml_fault = etree.Element("fault")
        xml_value = etree.Element("value")
        xml_value.append(py2xml(exception))
        xml_fault.append(xml_value)
        xml_response.append(xml_fault)
        return xml_response

    @staticmethod
    async def format_success(body):
        xml_response = etree.Element("methodResponse")
        xml_params = etree.Element("params")
        xml_param = etree.Element("param")
        xml_value = etree.Element("value")

        xml_value.append(py2xml(body))
        xml_param.append(xml_value)
        xml_params.append(xml_param)
        xml_response.append(xml_params)
        return xml_response

    @staticmethod
    def build_xml(tree):
        return etree.tostring(
            tree,
            xml_declaration=True,
            encoding="utf-8",
        )
