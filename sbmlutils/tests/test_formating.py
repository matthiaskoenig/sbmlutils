import unittest

try:
    import libsbml
except ImportError:
    import tesbml as libsbml

import sbmlutils.formating as formating


class FormatingTestCase(unittest.TestCase):
    @staticmethod
    def _create_unit_definition(sid, units):
        """ Creates the defined unit definitions.
        (kind, exponent, scale, multiplier)
        """
        unit_def = libsbml.UnitDefinition(3, 1)
        unit_def.setId(sid)
        for data in units:
            kind = data[0]
            exponent = data[1]
            scale = 0
            multiplier = 1.0
            if len(data) > 2:
                scale = data[2]
            if len(data) > 3:
                multiplier = data[3]

            FormatingTestCase._create_unit(unit_def, kind, exponent, scale, multiplier)
        return unit_def

    @staticmethod
    def _create_unit(unit_def, kind, exponent, scale=0, multiplier=1.0):
        unit = unit_def.createUnit()
        unit.setKind(kind)
        unit.setExponent(exponent)
        unit.setScale(scale)
        unit.setMultiplier(multiplier)
        return unit

    def test_unitDefinitionToString1(self):
        unit_def = FormatingTestCase._create_unit_definition('mM',
                                                             [(libsbml.UNIT_KIND_MOLE, 1.0), (libsbml.UNIT_KIND_METRE, -3.0)])
        print(unit_def)
        self.assertEqual(formating.unitDefinitionToString(unit_def),
                         '(mole)/(m^3)')

    def test_unitDefinitionToString2(self):
        unit_def = FormatingTestCase._create_unit_definition('test',
                                                             [(libsbml.UNIT_KIND_DIMENSIONLESS, 1.0)])
        print(unit_def)
        self.assertEqual(formating.unitDefinitionToString(unit_def),
                         '')

    def test_unitDefinitionToString3(self):
        unit_def = FormatingTestCase._create_unit_definition('pmol',
                                                             [(libsbml.UNIT_KIND_MOLE, 1.0, -12, 1.0)], )
        print(unit_def)
        self.assertEqual(formating.unitDefinitionToString(unit_def),
                         '(10^-12)*mole')


if __name__ == '__main__':
    unittest.main()
