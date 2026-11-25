# Groups (groups)

Use the groups package to capture relationships among existing SBML elements. A `classification` group identifies a category, a `partonomy` group represents a whole and its parts, and a `collection` groups elements for a shared purpose. Group membership does not change the reaction rates or stoichiometry.

## Mark the reactions in a pathway

Create a Core model with two reactions, then use libSBML to add a `collection` group. Each member's `idRef` identifies an existing reaction.

```python
from pathlib import Path

import libsbml

from sbmlutils.factory import (
    Compartment,
    Model,
    ModelUnits,
    Reaction,
    Species,
    Units,
    create_model,
)
from sbmlutils.io import read_sbml, write_sbml
from sbmlutils.validation import validate_doc

model = Model(
    sid="pathway",
    model_units=ModelUnits(substance=Units.mole, volume=Units.litre),
    compartments=[Compartment("cell", value=1.0, unit=Units.litre)],
    species=[Species(sid, compartment="cell") for sid in ("A", "B", "C")],
    reactions=[
        Reaction("step1", equation="A -> B"),
        Reaction("step2", equation="B -> C"),
    ],
)
result = create_model(model, Path("pathway.xml"), raise_on_error=True)

doc = read_sbml(result.sbml_path)
namespace = libsbml.GroupsExtension.getXmlnsL3V1V1()
doc.enablePackage(namespace, "groups", True)
doc.setPackageRequired("groups", False)

plugin = doc.getModel().getPlugin("groups")
group = plugin.createGroup()
group.setId("conversion_pathway")
group.setKind(libsbml.GROUP_KIND_COLLECTION)
for reaction_id in ("step1", "step2"):
    member = group.createMember()
    member.setIdRef(reaction_id)

assert not validate_doc(doc).errors
write_sbml(doc, Path("pathway_groups.xml"))

reloaded = read_sbml(Path("pathway_groups.xml"))
group = reloaded.getModel().getPlugin("groups").getGroup("conversion_pathway")
assert [group.getMember(i).getIdRef() for i in range(group.getNumMembers())] == [
    "step1",
    "step2",
]
```

Groups can also reference elements by `metaIdRef`, which is useful for elements that lack a suitable SBML identifier. Keep the document in libSBML and use [`read_sbml` and `write_sbml`](../io.md) to preserve group membership. The factory and its `sbml_to_model` parser omit Groups content.
