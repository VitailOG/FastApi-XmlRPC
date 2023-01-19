from aiohttp_xmlrpc.common import schema, py2xml, xml2py

from lxml import etree

from fastapi_xmlrpc.parser.exceptions import ParseError


class XMLRPCHandler:

    def __init__(self, xml_body=None):
        self.xml_body = xml_body
        self.THREAD_POOL_EXECUTOR = None

    @classmethod
    def handle(cls, body):
        try:
            xml_request = cls._parse_body(body)
        except etree.XMLSyntaxError:
            raise ParseError('Syntax error while parsing an XML document')

        full_method_name = xml_request.xpath("//methodName[1]")[0].text

        args = list(
                map(
                    xml2py,
                    xml_request.xpath("//params/param/value")
                )
            )

        return full_method_name, args

    @staticmethod
    def _parse_body(xml_string: str):
        parse = etree.XMLParser(resolve_entities=False)
        root = etree.fromstring(xml_string, parse)
        return root

    @classmethod
    def format_error(cls, exception: Exception):
        xml_response = etree.Element("methodResponse")
        xml_fault = etree.Element("fault")
        xml_value = etree.Element("value")
        xml_value.append(py2xml(exception))
        xml_fault.append(xml_value)
        xml_response.append(xml_fault)
        return cls.build_xml(xml_response)

    @classmethod
    def format_success(cls, body):
        xml_response = etree.Element("methodResponse")
        xml_params = etree.Element("params")
        xml_param = etree.Element("param")
        xml_value = etree.Element("value")

        xml_value.append(py2xml(body))
        xml_param.append(xml_value)
        xml_params.append(xml_param)
        xml_response.append(xml_params)
        return cls.build_xml(xml_response)

    @staticmethod
    def build_xml(tree):
        return etree.tostring(
            tree,
            xml_declaration=True,
            encoding="utf-8",
        )
