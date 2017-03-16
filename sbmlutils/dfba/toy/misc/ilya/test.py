from __future__ import print_function, division


if __name__ == "__main__":
    # Run simulation of the hybrid model

    from multiscale.sbmlutils import comp
    comp.flattenSBMLFile("Top_level.xml", output_file="flatten.xml")
