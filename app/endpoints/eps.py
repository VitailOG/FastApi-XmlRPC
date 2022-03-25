from routing import XmlRpcAPIRouter


router = XmlRpcAPIRouter()


@router.xml_rpc(namespace='eps', function_name='test')
def test():
    return {}
