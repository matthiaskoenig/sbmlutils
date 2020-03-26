"""
Converts simple bipartite species-reaction graph to SBML
using python bindings in libsbml

requirements:
    pip install python-libsbml networkx
"""
import networkx as nx
import libsbml

'''
Create bipartite networkx graph consisting of species and reaction nodes.
Edges require stoichiometry (or set to 1 otherwise).
'''
G = nx.DiGraph()

# add species nodes
G.add_node("S1", ntype="specie")
G.add_node("S2", ntype="specie")
G.add_node("S3", ntype="specie")
G.add_node("S4", ntype="specie")
G.add_node("S5", ntype="specie")
G.add_node("S6", ntype="specie")

# add reaction nodes (and reaction edges)
G.add_node("r1", ntype="reaction")  # 2 S1 -> S2
G.add_edges_from([
    ("S1", "r1", {'stoichiometry': 2}),
    ("r1", "S2", {'stoichiometry': 1})])
G.add_node("r2", ntype="reaction")  # S2 -> S3
G.add_edges_from([
    ("S2", "r2", {'stoichiometry': 1}),
    ("r2", "S3", {'stoichiometry': 1})])
G.add_node("r3", ntype="reaction")  # S3 + S4 -> S5 + S6
G.add_edges_from([
    ("S3", "r3", {'stoichiometry': 1}),
    ("S4", "r3", {'stoichiometry': 1}),
    ("r3", "S5", {'stoichiometry': 1}),
    ("r3", "S6", {'stoichiometry': 1})
])

print(G)
for sid, n in G.nodes.items():
    print(sid, n)
for sid, e in G.edges.items():
    print(sid, e)

'''
Create SBML model from the graph
'''
doc = libsbml.SBMLDocument()  # type: libsbml.SBMLDocument
model = doc.createModel()  # type: libsbml.Model
model.setId("graph_model")
# create species
for sid, n in G.nodes.items():
    print(sid, n)
    if n['ntype'] == "specie":
        s = model.createSpecies()  # type: libsbml.Species
        s.setId(sid)

# create reactions
for sid, n in G.nodes.items():
    if n['ntype'] == "reaction":
        r = model.createReaction()  # type: libsbml.Reaction
        r.setId(sid)
        for reactant_id in G.predecessors(sid):

            stoichiometry = G.edges[reactant_id, sid]['stoichiometry']
            reactant = model.getSpecies(reactant_id)
            r.addReactant(reactant, stoichiometry)

        for product_id in G.successors(sid):
            product = model.getSpecies(product_id)
            stoichiometry = G.edges[sid, product_id]['stoichiometry']
            r.addProduct(product, stoichiometry)

# serialization
sbml_str = libsbml.writeSBMLToString(doc)
print("-" * 80)
print(sbml_str)
libsbml.writeSBMLToFile(doc, "graph2sbml.xml")



