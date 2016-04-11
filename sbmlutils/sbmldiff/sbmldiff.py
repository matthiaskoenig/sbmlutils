from __future__ import print_function, division
import tellurium as te
import lxml.etree as ET
import StringIO
import tempfile
import libsbml

r = te.loada('''
    J0: S1 -> S2; k1*S1;
    S1=10.0; S2=0.0; k1=1.0;
''')

# create SBML file
f = tempfile.NamedTemporaryFile('w', suffix=".xml")
r.exportToSBML(f.name)

# create C14N canonical XML
et = ET.parse(f.name)
output = StringIO.StringIO()
et.write_c14n(output)
c14n_xml = output.getvalue()
# TODO: in addition sort all elements of the listOfs

# libsbml has no problem reading
doc = libsbml.readSBMLFromString(c14n_xml)

# file has no problems
# from multiscale.sbmlutils.validation import check_sbml
# check_sbml(libsbml.writeSBMLToString(doc))

# roadrunner has problems
te.loadSBMLModel(c14n_xml)

