import libsedml

sid = "abd"
doc = libsedml.SedDocument()
element = doc.getElementBySId(sid)
