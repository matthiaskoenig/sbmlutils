import unittest

# TODO: implement tests

class MyTestCase(unittest.TestCase):
    '''
    def test_something(self):

        # TODO: test for model creator test that all the information is written in the test model

        h = model.getModelHistory()
        self.assertIsNotNone(h)
        self.assertEqual(1, h.getNumCreators())
        c = h.getCreator(0)
        self.assertEqual('Koenig', c.getFamilyName())
        self.assertEqual('Matthias', c.getGivenName())
        self.assertEqual('konigmatt@googlemail.com', c.getEmail())
        self.assertEqual('Test organisation', c.getOrganization())

        self.assertEqual(True, False)


    def test_clearance(self):
        """Test BasicClearance model."""
        # TODO: fix/simplify the path issues

        cell_model = CellModel.create_model('multiscale.modelcreator.models.clearance.BasicClearanceCell')
        tissue_dict = TissueModel.createTissueDict(['multiscale.modelcreator.models.SinusoidalUnit',
                                                   'multiscale.modelcreator.models.clearance.BasicClearanceSinusoid'])
        Nc, Nf = 1, 1

        version = 1
        tm = TissueModel(Nc=Nc, Nf=Nf, version=version, tissue_dict=tissue_dict,
                         cell_model=cell_model, sim_id='core', events=None)
        tm.createModel()
        self.assertEqual(tm.Nc, Nc)
        self.assertEqual(tm.version, version)
        self.assertEqual(tm.simId, 'core')

    def test_galactose_core(self):
        Nc = 1
        Nf = 1
        version = 'test'
        cell_model = CellModel.create_model('multiscale.modelcreator.models.galactose.GalactoseCell')
        tissue_dict = TissueModel.createTissueDict(['multiscale.modelcreator.models.SinusoidalUnit',
                                          'multiscale.modelcreator.models.galactose.GalactoseSinusoid'])

        tissue_model = TissueModel(Nc=Nc, Nf=Nf, version=version, tissue_dict=tissue_dict,
                                   cell_model=cell_model, sim_id='test', events=None)
        tissue_model.createModel()

        self.assertEqual(tissue_model.version, version)
        self.assertEqual(tissue_model.simId, 'test')
    '''

if __name__ == '__main__':
    unittest.main()
