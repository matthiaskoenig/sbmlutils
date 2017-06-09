"""
Test annotation functions and annotating of SBML models.
"""
from __future__ import print_function, division

import pytest
import libsbml
from sbmlutils import factory
from sbmlutils import history


def test_date_now():
    now = history.date_now()
    assert now is not None


def test_set_model_history():
    creators = [factory.Creator(familyName='Koenig', givenName="Matthias",
                                email="konigmatt@googlemail.com", organization="Test organisation")]
    sbmlns = libsbml.SBMLNamespaces(3, 1)
    doc = libsbml.SBMLDocument(sbmlns)
    model = doc.createModel()
    history.set_model_history(model, creators)

    # check if history was written correctly
    h = model.getModelHistory()
    assert h is not None
    assert h.getNumCreators() == 1
    c = h.getCreator(0)
    assert 'Koenig' == c.getFamilyName()
    assert 'Matthias' == c.getGivenName()
    assert 'konigmatt@googlemail.com' == c.getEmail()
    assert 'Test organisation' == c.getOrganization()