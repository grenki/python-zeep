import re

from tests.utils import DummyTransport
from zeep.loader import parse_xml


def test_huge_text():
    # libxml2>=2.7.3 has XML_MAX_TEXT_LENGTH 10000000 without XML_PARSE_HUGE
    tree = parse_xml(u"""
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
         <s:Body>
          <HugeText xmlns="http://hugetext">%s</HugeText>
         </s:Body>
        </s:Envelope>
    """ % (u'\u00e5' * 10000001), DummyTransport(), xml_huge_tree=True)

    assert tree[0][0].text == u'\u00e5' * 10000001


def test_html_inside_xml():
    s = b'<env:Envelope xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><env:Header><ns0:sessionID xmlns:ns0="http://xmlns.org" xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">sid</ns0:sessionID></env:Header><env:Body><m:a xmlns:m="http://xmlns.org"><b xmlns="http://xmlns.org"><c><d>Text <a target="_blank" href="https://google.com">https://google.com</a> more text</d><e>Text<br/> more text</e></c></b></m:a></env:Body></env:Envelope>'

    tree = parse_xml(s, DummyTransport(), content_preprocessor=response_preprocessor)

    content = elem2dict(tree)['Body']['a']['b']['c']
    assert (content['d'] == "Text https://google.com more text")
    assert (content['e'] == "Text more text")


def response_preprocessor(response_str):
    response_str = response_str.decode('utf-8')
    replacer_datas = [[r"<a .*>(.*)</a>", r'\1'],
                      [r"(<br/>)", r'']]
    for replacer_data in replacer_datas:
        response_str = re.sub(replacer_data[0], replacer_data[1], response_str, 0)
    return response_str.encode('ascii')


def elem2dict(node):
    """
    Convert an lxml.etree node tree into a dict.
    """
    d = {}
    for e in node.iterchildren():
        key = e.tag.split('}')[1] if '}' in e.tag else e.tag
        value = e.text if e.text else elem2dict(e)
        if key in d:
            prev = d[key]
            if isinstance(prev, list):
                prev.append(value)
            else:
                d[key] = [prev, value]
        else:
            d[key] = value
    return d