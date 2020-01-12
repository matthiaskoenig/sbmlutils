import os
import logging

from sbmlutils.modelcreator import creator

import coloredlogs
coloredlogs.install(
    level='INFO',
    fmt="%(pathname)s:%(lineno)s %(funcName)s %(levelname) -10s %(message)s"
    # fmt="%(levelname) -10s %(asctime)s %(module)s:%(lineno)s %(funcName)s %(message)s"
)
logger = logging.getLogger(__name__)


base_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.join(base_dir, 'model')


if __name__ == "__main__":
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    print('-'*80)
    print(models_dir)
    print('-' * 80)

    # brain
    creator.create_model(modules=['pylimax.models.glucose.glucose_liver_model'], target_dir=target_dir,
                         annotations=os.path.join(base_dir, 'glucose_annotations.xlsx'), create_report=True)
