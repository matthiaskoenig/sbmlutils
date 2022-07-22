"""Annotations for ICG model."""

from sbmlutils.metadata import *


compartments = {
    # liver
    "li": [
        (BQB.IS, "fma/FMA:7197"),
        (BQB.IS, "bto/BTO:0000759"),
        (BQB.IS, "ncit/C12392"),
    ],
    "lyso": [
        (BQB.IS, "fma/FMA:63836"),
        (BQB.IS, "ncit/C13253"),
    ],
    # basolateral membrane
    "basolateral": [
        (BQB.IS, "fma/FMA:84669"),  # Basolateral plasma membrane
        (BQB.IS, "go/GO:0016323"),  # basolateral plasma membrane
    ],
    # apical membrane
    "apical": [
        (BQB.IS, "fma/FMA:84666"),  # Apical plasma membrane
        (BQB.IS, "go/GO:0016324"),  # apical plasma membrane
    ],
    "bi": [
        (BQB.IS, "fma/FMA:62971"),
        (BQB.IS, "ncit/C13192"),
    ],
    # rest
    # FIXME: rest compartment is not the organism
    "re": [
        (BQB.IS_VERSION_OF, "fma/FMA:62955"),  # anatomical entity
        (BQB.IS_PART_OF, "ncit/C14250"),  # Organism
    ],
    # gastrointestinal tract
    "gi": [
        (BQB.IS, "fma/FMA:71132"),
        (BQB.IS, "bto/BTO:0000511"),
        (BQB.IS, "ncit/C34082"),
    ],
    # gut/intestine
    "gu": [
        (BQB.IS, "fma/FMA:45615"),  # gut
        (BQB.IS, "bto/BTO:0000545"),  # gut
        (BQB.IS, "ncit/C12736"),  # intestine
        (BQB.IS, "fma/FMA:7199"),  # intestine
        (BQB.IS, "bto/BTO:0000648"),  # intestine
    ],
    "gu_lumen": [
        (BQB.IS, "fma/FMA:14586"),  # Lumen of intestine
        (BQB.IS, "uberon/UBERON:0018543"),  # lumen of intestine
    ],
    # heart
    "he": [
        (BQB.IS, "ncit/C12727"),  # heart
        (BQB.IS, "fma/FMA:7088"),  # heart
        (BQB.IS, "bto/BTO:0000562"),  # heart
    ],
    # kidneys
    "ki": [
        (BQB.IS, "fma/FMA:7203"),
        (BQB.IS, "bto/BTO:0000671"),
        (BQB.IS, "ncit/C12415"),
    ],
    # lung
    "lu": [
        (BQB.IS, "fma/FMA:7195"),
        (BQB.IS, "bto/BTO:0000763"),
        (BQB.IS, "ncit/C12468"),
    ],
    "ve": [
        (BQB.IS, "bto/BTO:0000131"),  # plasma
        (BQB.IS, "ncit/C13356"),  # plasma
        (BQB.IS_PART_OF, "fma/FMA:50723"),  # vein
    ],
    "ar": [
        (BQB.IS, "bto/BTO:0000131"),  # plasma
        (BQB.IS, "ncit/C13356"),  # plasma
        (BQB.IS_PART_OF, "fma/FMA:50720"),  # artery
    ],
    "po": [
        (BQB.IS, "bto/BTO:0000131"),  # plasma
        (BQB.IS, "ncit/C13356"),  # plasma
        (BQB.IS_PART_OF, "fma/FMA:66645"),  # portal vein
    ],
    # hepatic vein
    "hv": [
        (BQB.IS, "bto/BTO:0000131"),  # plasma
        (BQB.IS, "ncit/C13356"),  # plasma
        (BQB.IS_PART_OF, "fma/FMA:14337"),  # hepatic vein
    ],
    # rest vein
    "rev": [
        (BQB.IS, "bto/BTO:0000131"),  # plasma
        (BQB.IS, "ncit/C13356"),  # plasma
        # fixme: be more specific
    ],
    # hepatic vein
    "kiv": [
        (BQB.IS, "bto/BTO:0000131"),  # plasma
        (BQB.IS, "ncit/C13356"),  # plasma
        # fixme: be more specific
    ],
    "stomach": [
        (BQB.IS, "fma/FMA:7148"),
        (BQB.IS, "ncit/C12391"),
        (BQB.IS, "uberon/UBERON:0000945"),
        (BQB.IS, "bto/BTO:0001307"),
    ],
    # spleen
    "sp": [
        (BQB.IS, "fma/FMA:7196"),
        (BQB.IS, "ncit/C12432"),
        (BQB.IS, "uberon/UBERON:0002106"),
        (BQB.IS, "bto/BTO:0001281"),
    ],
    # muscle
    "mu": [
        (BQB.IS, "fma/FMA:30316"),
        (BQB.IS, "bto/BTO:0000511"),
        (BQB.IS, "ncit/C13056"),
    ],
    "fo": [
        (BQB.IS, "ncit/C32628"),  # forearm
        (BQB.IS, "fma/FMA:9663"),  # forearm
    ],
    # hepatic vein
    "fov": [
        (BQB.IS, "bto/BTO:0000131"),  # plasma
        (BQB.IS, "ncit/C13356"),  # plasma
        # fixme: be more specific
    ],
    # pancreas
    "pa": [
        (BQB.IS, "fma/FMA:7198"),
        (BQB.IS, "ncit/C12393"),
        (BQB.IS, "uberon/UBERON:0001264"),
        (BQB.IS, "bto/BTO:0000988"),
    ],
    "feces": [
        (BQB.IS, "fma/FMA:64183"),
        (BQB.IS, "ncit/C13234"),
        (BQB.IS, "bto/BTO:0000440"),
    ],
    "plasma": [
        (BQB.IS, "ncit/C13356"),
        (BQB.IS, "bto/BTO:0000131"),
    ],
    "blood": [
        (BQB.IS, "fma/FMA:62970"),
        (BQB.IS, "ncit/C12434"),
        (BQB.IS, "bto/BTO:0000089"),
    ],
    "urine": [
        (BQB.IS, "fma/FMA:12274"),
        (BQB.IS, "ncit/C13283"),
        (BQB.IS, "bto/BTO:0001419"),
    ],
    "parenchyma": [
        (BQB.IS, "fma/FMA:45732"),
        (BQB.IS, "ncit/C74601"),
        (BQB.IS, "bto/BTO:0001539"),
    ],
    "parietal cell": [
        (BQB.IS, "ncit/C12594"),
        (BQB.IS, "http://snomed.info/id/57041003"),
    ],
    "gastric acid": [
        (BQB.IS, "fma/FMA:62972"),  # gastric juice
        (BQB.IS, "ncit/C94192"),
        (BQB.IS, "omit/0006944"),  # gastric acid
    ],
    "plasma membrane": [
        (BQB.IS, "ncit/C13735"),  # Plasma membrane
        (BQB.IS, "fma/FMA:63841"),  # Plasma membrane
        (BQB.IS, "GO:0005886"),  # plasma membrane
    ],
}

species = {
    "bil": [
        (BQB.IS, "inchikey/BPYKTIZUTYGOLE-IFADSCNNSA-N"),
        (BQB.IS, "chebi/CHEBI:16990"),
        (BQB.IS, "ncit/C305"),
    ],
    "icg": [
        (BQB.IS, "inchikey/MOFVSTNWEDAEEK-UHFFFAOYSA-M"),
        (BQB.IS, "chebi/CHEBI:31696"),
        (BQB.IS, "ncit/C65913"),
    ],
}
