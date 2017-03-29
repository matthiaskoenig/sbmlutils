"""
Test naming.
"""
from __future__ import print_function, absolute_import
from .sinnaming import *


def test_pp_id():
    assert 'PP' == getPPId()
    assert 'PP__test' == getPPSpeciesId('test')
    assert isPPSpeciesId('PP__test')
    assert not isPPSpeciesId('PP_test')


def test_pv_id():
    assert 'PV' == getPVId()
    assert 'PV__test' == getPVSpeciesId('test')
    assert isPVSpeciesId('PV__test')
    assert not isPVSpeciesId('PV_test')


def test_sinusoid_id():
    assert getSinusoidId(21) == 'S21'
    assert getSinusoidId(2) == 'S02'
    assert isSinusoidSpeciesId('S31__test')
    assert not isSinusoidSpeciesId('S1__test')


def test_disse_id():
    assert getDisseId(21) == 'D21'
    assert getDisseId(2) == 'D02'
    assert isDisseSpeciesId('D31__test')
    assert not isDisseSpeciesId('D1__test')


def test_hepatocyte_id():
    assert getHepatocyteId(21) == 'H21'
    assert getHepatocyteId(2) == 'H02'
    assert isHepatocyteSpeciesId('H31__test')
    assert not isHepatocyteSpeciesId('H1__test')


def test_cytosol_id():
    assert getCytosolId(21) == 'C21'
    assert getCytosolId(2) == 'C02'
    assert isCytosolSpeciesId('C31__test')
    assert not isCytosolSpeciesId('C1__test')


def test_localized_species_id():
    assert getPPSpeciesId('s1') == 'PP__s1'
    assert getPVSpeciesId('s1') == 'PV__s1'
    assert getSinusoidSpeciesId('s1', 3) == 'S03__s1'
    assert getDisseSpeciesId('s1', 3) == 'D03__s1'
    assert getHepatocyteSpeciesId('s1', 3) == 'H03__s1'
