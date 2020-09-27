"""
PKPD model creator for LiMAx and methacetin.
"""
from pathlib import Path

from sbmlutils.modelcreator import creator


if __name__ == "__main__":
    creator.create_model(
        modules=['pylimax.models.galactose_pkpd.galactose_pkpd_model'],
        output_dir=Path(__file__).parent / 'results',
        annotations=None
    )
