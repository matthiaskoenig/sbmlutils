"""Load and modify an existing antimony model."""

from sbmlutils.cytoscape import visualize_antimony, visualize_sbml
from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.parser import antimony_to_model
from sbmlutils.resources import EXAMPLES_DIR


model_antimony: str = """
    model antimony_repressilator
        # compartment
        compartment cell = 1

        # species
        species PX in cell = 0
        species PY in cell = 0
        species PZ in cell = 0
        species X in cell = 0
        species Y in cell = 20
        species Z in cell = 0

        # parameters
        beta = 0.2
        alpha0 = 0.2164
        alpha = 216.404
        eff = 20
        n = 2
        KM = 40
        tau_mRNA = 2
        tau_prot = 10
        ps_a = 0.5
        ps_0 = 0.0005

        # assignment rules
        t_ave := tau_mRNA/ln(2);
        beta := tau_mRNA/tau_prot;
        k_tl := eff/t_ave;
        a_tr := (ps_a - ps_0)*60;
        a0_tr := ps_0*60;
        kd_prot := ln(2)/tau_prot;
        kd_mRNA := ln(2)/tau_mRNA;
        alpha := a_tr*eff*tau_prot/(ln(2)*KM);
        alpha0 := (a0_tr*eff*tau_prot)/(ln(2)*KM);

        # reactions
        X ->; kd_mRNA*X;
        Y ->; kd_mRNA*Y;
        Z ->; kd_mRNA*Z;
        -> PX; k_tl*X;
        -> PY; k_tl*Y;
        -> PZ; k_tl*Z;
        PX ->; kd_prot*PX;
        PY ->; kd_prot*PY;
        PZ ->; kd_prot*PZ;
        -> X; a0_tr +a_tr *KM^n/(KM^n +PZ ^n);
        -> Y; a0_tr +a_tr *KM^n/(KM^n +PX ^n);
        -> Z; a0_tr +a_tr *KM^n/(KM^n +PY ^n);
    end
"""


if __name__ == "__main__":
    # visualize the model
    visualize_antimony(source=model_antimony, delete_session=True)

    # load model and manipulate
    model: Model = antimony_to_model(source=model_antimony)
    model.species.append(Species(sid="PA", initialAmount=0, compartment="cell"))
    for s in model.species:
        if s.sid in ["X", "Y", "Z"]:
            s.annotations.append((BQB.IS, "chebi/CHEBI:33699"))  # messenger RNA

    result = create_model(
        model=model,
        filepath=EXAMPLES_DIR / f"{model.sid}.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )
    visualize_sbml(sbml_path=result.sbml_path)
