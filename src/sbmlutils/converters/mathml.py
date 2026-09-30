"""Helper functions for the conversion of MathML to formula strings."""

import libsbml


def evaluableMathML(astnode: libsbml.ASTNode, variables: dict | None = None) -> str:
    """Create evaluable python formula string from ASTNode.

    The node of the caller is not modified, the variables are replaced in a copy.
    """
    if variables is None:
        variables = {}
    astnode = astnode.deepCopy()
    # replace variables with provided values
    for key, value in variables.items():
        astnode.replaceArgument(key, libsbml.parseFormula(str(value)))

    # parse formula
    settings: libsbml.L3ParserSettings = libsbml.L3ParserSettings()
    settings.setParseUnits(False)
    settings.setParseCollapseMinus(True)
    formula: str = libsbml.formulaToL3StringWithSettings(astnode, settings)

    # <replacements>
    formula = formula.replace("&&", "and")
    formula = formula.replace("||", "or")
    return formula.replace("^", "**")
