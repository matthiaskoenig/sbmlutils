"""
Compare the simulator results.
"""
from __future__ import print_function, division
import tellurium as te


def modelHeaders(top_model):
    """

    :param top_model:
    :type top_model:
    :return:
    :rtype:
    """
    r = te.loads(top_model)
    print(r.selections)
    r.selections = ['time'] + sorted(["[{}]".format(sid) for sid in r.getFloatingSpeciesIds()] +
                                     ["[{}]".format(sid) for sid in r.getBoundarySpeciesIds()]) + \
        sorted(r.getReactionIds()) + sorted(r.getGlobalParameterIds())
    print(r.selections)


if __name__ == "__main__":
    # Run simulation of the hybrid model
    from simsettings import top_level_file, out_dir
    import os

    os.chdir(out_dir)

    modelHeaders(top_level_file)
