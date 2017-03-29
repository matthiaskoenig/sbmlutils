#!/usr/bin/python
"""
Script replaces all SBML names with the ids
Only replaces SBML core, does not handle packages.

requires:
    libsbml python bindings
usage:
    ./copasi_names.py caffeine_pkpd.xml
"""
from __future__ import print_function
import libsbml


def set_names_as_ids(f_in, f_out=None):
    """ Sets the element as id on all elements in the model.

    :param f_in: SBML input file
    :param f_out:
    :return:
    """
    doc = libsbml.readSBMLFromFile(f_in)
    model = doc.getModel()
    model.populateAllElementIdList()
    sid_list = model.getAllElementIdList()

    for k in range(sid_list.size()):
        sid = sid_list.at(k)
        element = model.getElementBySId(sid)
        if (element is not None) and hasattr(element, 'setName'):
            print(element.getName(), '->', sid)
            element.setName(sid)

    if f_out is None:
        suffix = '_copasi'
        tokens = f_in.split('.')
        if len(tokens) > 1:
            f_out = ".".join(tokens[0:-1]) + suffix + "." + tokens[-1]
        else:
            f_out = tokens[0] + suffix

    # write to output file
    libsbml.writeSBMLToFile(doc, f_out)

    print('*'*60)
    print('Names replaced with ids')
    print('*'*60)
    print('f_in:\t', f_in)
    print('f_out:\t', f_out)
    print('*'*60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Python script which set SBML names to ids.')
    parser.add_argument('f_in', help="SBML input file")
    parser.add_argument('--f_out', help="SBML output file with names as ids")
    args = parser.parse_args()
    set_names_as_ids(args.f_in, args.f_out)
