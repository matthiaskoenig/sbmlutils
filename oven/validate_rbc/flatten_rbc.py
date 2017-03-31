
from __future__ import absolute_import, print_function

import libsbml
import time

model_paths = ["rbc_top.xml"]

for p in model_paths:

    t_start = time.time()
    print("\n*** {} ***".format(p))
    doc = libsbml.readSBMLFromFile(p)
    t_read = time.time()
    print('reading: {:5.3} [s]'.format(t_read - t_start))

    # converter options
    props = libsbml.ConversionProperties()
    props.addOption("flatten comp", True)  # Invokes CompFlatteningConverter
    props.addOption("leave_ports", True)  # Indicates whether to leave ports

    # convert
    result = doc.convert(props)
    if result != libsbml.LIBSBML_OPERATION_SUCCESS:
        doc.printErrors()
        print("model could not be flattended due to errors.")
    t_flat = time.time()
    print('flattening: {:5.3} [s]'.format(t_flat - t_start))
