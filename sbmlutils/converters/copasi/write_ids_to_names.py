try:
    import libsbml
except ImportError:
    import tesbml as libsbml


def write_ids_to_names(input_path, output_path):
    """
    :return:
    """
    doc = libsbml.readSBMLFromFile(input_path)  # type: libsbml.SBMLDocument
    elements = doc.getListOfAllElements()
    for element in elements:
        if element.isSetId():
            element.setName(element.id)
            print(element)

    libsbml.writeSBMLToFile(doc, output_path)


if __name__ == "__main__":


    """
    if len(sys.argv) < 3:
        print ("Usage: write_ids_to_name <input_copasi_file> <output_copasi_file>")
        sys.exit(0)

    input_path = sys.argv[1]
    output_pth = sys.argv[2]
    """
    input_path = "limax_pkpd_37.xml"
    output_path = "limax_pkpd_37_copasi.xml"
    write_ids_to_names(input_path, output_path)
