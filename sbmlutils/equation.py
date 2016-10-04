"""
Parse equation strings into a standard format.

Simplifies the creation of SBML models from given strings.
"""
from __future__ import print_function, division
import re
from collections import namedtuple

Part = namedtuple('Part', 'stoichiometry sid')

REV_PATTERN = '<[-=]>'
IRREV_PATTERN = '[-=]>'
MOD_PATTERN = '\[.*\]'
REV_SEP = '<=>'
IRREV_SEP = '=>'


class Equation(object):
    """ Representation of stoichiometric equations with modifiers. """

    class EquationException(Exception):
        pass

    def __init__(self, equation):
        self.raw = equation

        self.reactants = []
        self.products = []
        self.modifiers = []
        self.reversible = None

        self._parseEquation()

    def _parseEquation(self):
        eq_string = self.raw[:]

        # get modifiers and remove from equation string
        mod_list = re.findall(MOD_PATTERN, eq_string)
        if len(mod_list) == 1:
            self._parseModifiers(mod_list[0])
            tokens = eq_string.split('[')
            eq_string = tokens[0].strip()
        elif len(mod_list) > 1:
            raise self.EquationException('Invalid equation: {}'.format(self.raw))

        # now parse the equation without modifiers
        items = re.split(REV_PATTERN, eq_string)

        if len(items) == 2:
            self.reversible = True
        elif len(items) == 1:
            items = re.split(IRREV_PATTERN, eq_string)
            self.reversible = False
        else:
            raise self.EquationException('Invalid equation: {}'.format(self.raw))

        # remove whitespaces
        items = [o.strip() for o in items]
        left, right = items[0], items[1]
        if len(left) > 0:
            self.reactants = self._parseHalfEquation(left)
        if len(right) > 0:
            self.products = self._parseHalfEquation(right)

    def _parseModifiers(self, s):
        s = s.replace('[', '')
        s = s.replace(']', '')
        s = s.strip()
        tokens = re.split('[,;]', s)
        modifiers = [t.strip() for t in tokens]
        self.modifiers = [t for t in modifiers if len(t) > 0]

    def _parseHalfEquation(self, string):
        """ Only '+ supported in equation !, do not use negative
            stoichiometries.
        """
        items = re.split('[+-]', string)
        items = [item.strip() for item in items]
        return [self._parseReactant(item) for item in items]

    def _parseReactant(self, item):
        """ Returns tuple of stoichiometry, sid. """
        tokens = item.split()
        if len(tokens) == 1:
            stoichiometry = 1.0
            sid = tokens[0]
        else:
            stoichiometry = float(tokens[0])
            sid = ' '.join(tokens[1:])
        return Part(stoichiometry, sid)

    def toString(self, modifiers=False):
        left = self._toStringSide(self.reactants)
        right = self._toStringSide(self.products)
        if self.reversible:
            sep = REV_SEP
        elif not self.reversible:
            sep = IRREV_SEP

        if modifiers:
            mod = self.toStringModifiers()
            return ' '.join([left, sep, right, mod])
        else:
            return ' '.join([left, sep, right])

    def _toStringSide(self, items):
        tokens = []
        for item in items:
            stoichiometry, sid = item[0], item[1]
            if abs(1.0 - stoichiometry) < 1E-10:
                tokens.append(sid)
            else:
                tokens.append(' '.join([str(stoichiometry), sid]))
        return ' + '.join(tokens)

    def toStringModifiers(self):
        return '[{}]'.format(', '.join(self.modifiers))

    def info(self):
        lines = [
            '{:<10s} : {}'.format('raw', self.raw),
            '{:<10s} : {}'.format('parsed', self.toString()),
            '{:<10s} : {}'.format('reversible', self.reversible),
            '{:<10s} : {}'.format('reactants', self.reactants),
            '{:<10s} : {}'.format('products', self.products),
            '{:<10s} : {}'.format('modifiers', self.modifiers),
            '\n'
        ]
        print('\n'.join(lines))


##################################################################
if __name__ == '__main__':

    tests = ['c__gal1p => c__gal + c__phos',
             'e__h2oM <-> c__h2oM',
             '3 atp + 2.0 phos + ki <-> 16.98 tet',
             'c__gal1p => c__gal + c__phos [c__udp, c__utp]',
             'A_ext => A []',
             '=> cit',
             'acoa =>',
             ]

    for test in tests:
        print('-' * 40)
        print(test)
        print('-' * 40)
        eq = Equation(test)
        eq.info()
