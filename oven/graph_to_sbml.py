"""
Create SBML graph with tellurium.
Read the antimony tutorial for details.

reversibility:
    reversible reaction: '->'
    irreversible reaction: '=>'

modifiers:
    activations '-o'
    inhibitions '-|'
    unknown interactions '-('
"""

import tellurium as te

ant = """
model graph()
    // bipartite reaction-species graph
    R1: A + B -> 2 C;
    R2: C => D;
    R3: D -> E;

    // modifiers
    I1: Inh -| R1;
    A1: Act -o R3;
end
"""

sbml = te.antimonyToSBML(ant)
with open("graph.xml", "w") as f:
    f.write(sbml)
