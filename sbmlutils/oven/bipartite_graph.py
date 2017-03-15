"""
Create SBML bipartite graph with tellurium/antimony.
Read the antimony tutorial for details.

reversibility:
    reversible reaction: '->'
    irreversible reaction: '=>'

One class is R (reaction) the other class S (species).

"""

import tellurium as te

ant = """
model graph()
    // bipartite reaction-species graph (R-S graph)
    // all ingoing edges on the left, outgoing on the right
    R1: A + B => C;
    R2: C => D;
    R3: D => E;
end
"""

sbml = te.antimonyToSBML(ant)
with open("bipartite-graph.xml", "w") as f:
    f.write(sbml)
