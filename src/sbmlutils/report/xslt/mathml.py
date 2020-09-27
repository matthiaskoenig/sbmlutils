"""
Transformation of Content MathML to Presentation MathML using stylesheets.

"""
import lxml.etree as ET

xml_filename = 'test.xml'
xsl_filename = 'ctop.xsl'

dom = ET.parse(xml_filename)
xslt = ET.parse(xsl_filename)
transform = ET.XSLT(xslt)
newdom = transform(dom)


print(ET.tostring(newdom, pretty_print=True))
