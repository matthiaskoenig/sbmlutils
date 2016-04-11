from __future__ import print_function, division

import unittest
from libsbml import *
from multiscale.sbmlutils.factory import *

class FactoryTestCase(unittest.TestCase):

    def test_create_parameters(self):
        parameters = {
            # id: ('value', 'unit', 'constant')
            'scale_f':      (1E-6, '-', True),
            'Vmax_bA':      (5.0, 'mole_per_s', True),
            'Km_A':         (1.0, 'mM', True)}
        dzip = {}
        for k, v in parameters.iteritems():
            dzip[k] = dict(zip(['value', 'unit', 'constant'], v))
            dzip[k]['id'] = k

        doc = SBMLDocument(3, 1)
        model = doc.createModel()
        sbml_parameters = create_parameters(model, dzip)
        self.assertEqual(3, len(sbml_parameters))
        self.assertTrue('scale_f' in sbml_parameters)
        self.assertTrue('Vmax_bA' in sbml_parameters)
        self.assertTrue('Km_A' in sbml_parameters)
        self.assertEqual(3, len(model.getListOfParameters()))


if __name__ == '__main__':
    unittest.main()
