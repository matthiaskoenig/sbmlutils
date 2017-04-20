from __future__ import print_function, absolute_import
import cobra


if __name__ == "__main__":
    print("reading model")
    model = cobra.io.read_sbml_model("diauxic_fba.xml")
    print(model)
