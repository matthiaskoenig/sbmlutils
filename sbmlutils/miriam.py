"""
Helper class to work with the MIRIAM resources.
"""
_collections = [
    ["sbo", "Systems Biology Ontology", "^SBO:\d{7}$"],
    ["bto", "Brenda Tissue Ontology", "^BTO:\d{7}$"],
    ["chebi", "ChEBI", "^CHEBI:\d+$"],
    ["ec-code", "Enzyme Nomenclature", "^\d+\.-\.-\.-|\d+\.\d+\.-\.-|\d+\.\d+\.\d+\.-|\d+\.\d+\.\d+\.(n)?\d+$"],
    ["fma", "Foundational Model of Anatomy Ontology", "^FMA:\d+$"],
    ["go", "Gene Ontology", "^GO:\d{7}$"],
    ["kegg.compound", "KEGG Compound", "^C\d+$"],
    ["kegg.pathway", "KEGG Pathway", "^\w{2,4}\d{5}$"],
    ["kegg.reaction", "KEGG Reaction", "^R\d+$"],
    ["omim", "OMIM", "^[*#+%^]?\d{6}$"],
    ["pubmed", "PubMed", "^\d+$"],
    ["pw", "Pathway Ontology", "^PW:\d{7}$"],
    ["reactome", "Reactome", "(^(REACTOME:)?R-[A-Z]{3}-[0-9]+(-[0-9]+)?$)|(^REACT_\d+$)"],
    ["rhea", "Rhea", "^\d{5}$"],
    ["sabiork.kineticrecord", "SABIO-RK Kinetic Record", "^\d+$"],
    ["smpdb", "Small Molecule Pathway Database", "^SMP\d{5}$"],
    ["taxonomy", "Taxonomy", "^\d+$"],
    ["tcdb", "Transport Classification Database", "^\d+\.[A-Z]\.\d+\.\d+\.\d+$"],
    ["uberon", "UBERON", "^UBERON\:\d+$"],
    ["uniprot", "UniProt Knowledgebase",
     "^([A-N,R-Z][0-9]([A-Z][A-Z, 0-9][A-Z, 0-9][0-9]){1,2})|([O,P,Q][0-9]"
     "[A-Z, 0-9][A-Z, 0-9][A-Z, 0-9][0-9])(\.\d+)?$"],
    ["uo", "Ontology of standardized units", "^UO:\d{7}?"],
]
