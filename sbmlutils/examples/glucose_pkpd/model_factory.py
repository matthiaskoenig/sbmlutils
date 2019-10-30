"""
PKPD model creator for whole-body glucose model.
"""
from __future__ import print_function, division
import os
import logging

from sbmlutils.modelcreator import creator
from sbmlutils.comp import flattenSBMLFile
from sbmlutils.report import sbmlreport

import coloredlogs
coloredlogs.install(
    level='INFO',
    fmt="%(pathname)s:%(lineno)s %(funcName)s %(levelname) -10s %(message)s"
    # fmt="%(levelname) -10s %(asctime)s %(module)s:%(lineno)s %(funcName)s %(message)s"
)
logger = logging.getLogger(__name__)


base_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.join(base_dir, 'model')

from pylimax.models.glucose_pkpd import prepare_rbc_model


#############################
if __name__ == "__main__":
    create_report = True
    build_submodels = True
    prepare_rbc = True

    # if prepare_rbc:
    #     prepare_rbc_model.prepare_rbc_model(name="rbc_parasite_model", target_dir=target_dir)

    if build_submodels:

        # brain
        creator.create_model(modules=['pylimax.models.glucose_pkpd.glucose_brain_model'], target_dir=target_dir,
                             annotations=None, create_report=create_report)


        # rbc
        creator.create_model(modules=['pylimax.models.glucose_pkpd.glucose_rbc_model'], target_dir=target_dir,
                             annotations=None, create_report=create_report)

        # liver
        creator.create_model(modules=['pylimax.models.glucose_pkpd.glucose_liver_model'], target_dir=target_dir,
                             annotations=None, create_report=create_report)

    # exit()
    # create comp model
    [_, _, body_path] = creator.create_model(modules=['pylimax.models.glucose_pkpd.glucose_pkpd_model'], target_dir=target_dir,
                                             annotations=None, create_report=create_report)

    from pylimax.models.glucose_pkpd.glucose_pkpd_model import mid, version
    flat_body_path = os.path.join(target_dir, "{}_{}_flat.xml".format(mid, version))
    flattenSBMLFile(body_path, output_path=flat_body_path)

    # create model report
    sbmlreport.create_sbml_report(flat_body_path, out_dir=target_dir)
