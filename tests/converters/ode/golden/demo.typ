#set document(title: [Koenig\_demo\_v15])
#set page(margin: 2cm)
#set text(size: 10pt)
#set par(justify: true)
#set heading(numbering: "1.")
// the equations of a section are one block, which breaks across pages
#show math.equation.where(block: true): set block(breakable: true)
#show math.equation.where(block: true): set par(leading: 0.9em)

#align(center, text(size: 16pt, weight: "bold")[Koenig\_demo\_v15])

Model `Koenig_`#sym.zws;`demo_`#sym.zws;`v15`, SBML Level 3 Version 1, read from Koenig\_demo\_v15.xml, written by sbmlutils VERSION.

Koenig Demo Metabolism

Description

This is a demonstration model in SBML format.

Terms of use

The content of this model has been carefully created in a manual research effort. This file has been created by Matthias König using sbmlutils. For questions contact koenigmx\@hu-berlin.de. Copyright © 2022 Matthias König.

This work is licensed under a Creative Commons Attribution 4.0 International License.

Redistribution and use of any part of this model, with or without modification, are permitted provided that the following conditions are met:

Redistributions of this SBML file must retain the above copyright notice, this list of conditions and the following disclaimer.

Redistributions in a different form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

This model is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

= Units

#table(
  columns: 6,
  stroke: none,
  column-gutter: 1.5em,
  table.hline(stroke: 0.8pt),
  table.header([*Time*], [*Substance*], [*Extent*], [*Volume*], [*Area*], [*Length*]),
  table.hline(stroke: 0.4pt),
  [s], [mole], [mole], [m#super[3]], [m#super[2]], [m],
  table.hline(stroke: 0.8pt),
)

= Compartments

#table(
  columns: (auto, auto, 1fr, auto, auto, auto),
  stroke: none,
  align: (left, left, left, left, left, center),
  table.hline(stroke: 0.8pt),
  table.header([*Symbol*], [*Id*], [*Name*], [*Size*], [*Unit*], [*Constant*]),
  table.hline(stroke: 0.4pt),
  [$e$], [`e`], [external compartment], [$10^(-6)$], [m#super[3]], [],
  [$c$], [`c`], [cell compartment], [$10^(-6)$], [m#super[3]], [],
  [$m$], [`m`], [plasma membrane], [$1$], [m#super[2]], [],
  table.hline(stroke: 0.8pt),
)

= Species

#table(
  columns: (auto, auto, 1fr, auto, auto, auto, 1fr),
  stroke: none,
  align: (left, left, left, left, left, left, left),
  table.hline(stroke: 0.8pt),
  table.header([*Symbol*], [*Id*], [*Name*], [*Compartment*], [*Value*], [*Unit*], [*Properties*]),
  table.hline(stroke: 0.4pt),
  [$c_("_A")$], [`c__A`], [A], [$c$], [$0$], [mole/m#super[3]], [concentration],
  [$c_("_B")$], [`c__B`], [B], [$c$], [$0$], [mole/m#super[3]], [concentration],
  [$c_("_C")$], [`c__C`], [C], [$c$], [$0$], [mole/m#super[3]], [concentration],
  [$e_("_A")$], [`e__A`], [A], [$e$], [$0$], [mole/m#super[3]], [concentration],
  [$e_("_B")$], [`e__B`], [B], [$e$], [$0$], [mole/m#super[3]], [concentration],
  [$e_("_C")$], [`e__C`], [C], [$e$], [$0$], [mole/m#super[3]], [concentration],
  table.hline(stroke: 0.8pt),
)

= Parameters

#table(
  columns: (auto, auto, 1fr, auto, auto, auto),
  stroke: none,
  align: (left, left, left, left, left, center),
  table.hline(stroke: 0.8pt),
  table.header([*Symbol*], [*Id*], [*Name*], [*Value*], [*Unit*], [*Constant*]),
  table.hline(stroke: 0.4pt),
  [$upright("scale")_("f")$], [`scale_f`], [metabolic scaling factor], [$10^(-6)$], [\-], [#sym.checkmark],
  [$upright("Vmax")_("bA")$], [`Vmax_bA`], [], [$5$], [mol/s], [#sym.checkmark],
  [$upright("Km")_("A")$], [`Km_A`], [], [$1$], [mmol/l], [#sym.checkmark],
  [$upright("Vmax")_("bB")$], [`Vmax_bB`], [], [$2$], [mol/s], [#sym.checkmark],
  [$upright("Km")_("B")$], [`Km_B`], [], [$0.5$], [mmol/l], [#sym.checkmark],
  [$upright("Vmax")_("bC")$], [`Vmax_bC`], [], [$2$], [mol/s], [#sym.checkmark],
  [$upright("Km")_("C")$], [`Km_C`], [], [$3$], [mmol/l], [#sym.checkmark],
  [$upright("Vmax")_("v1")$], [`Vmax_v1`], [], [$1$], [mol/s], [#sym.checkmark],
  [$upright("Keq")_("v1")$], [`Keq_v1`], [], [$10$], [\-], [#sym.checkmark],
  [$upright("Vmax")_("v2")$], [`Vmax_v2`], [], [$0.5$], [mol/s], [#sym.checkmark],
  [$upright("Vmax")_("v3")$], [`Vmax_v3`], [], [$0.5$], [mol/s], [#sym.checkmark],
  [$upright("Vmax")_("v4")$], [`Vmax_v4`], [], [$0.5$], [mol/s], [#sym.checkmark],
  [$upright("Keq")_("v4")$], [`Keq_v4`], [], [$2$], [\-], [#sym.checkmark],
  table.hline(stroke: 0.8pt),
)

= Reactions

#table(
  columns: (auto, auto, 1fr, 1fr),
  stroke: none,
  align: (left, left, left, left),
  table.hline(stroke: 0.8pt),
  table.header([*Rate*], [*Id*], [*Name*], [*Equation*]),
  table.hline(stroke: 0.4pt),
  [$v_("bA")$], [`bA`], [bA (A import)], [$e_("_A") --> c_("_A")$],
  [$v_("bB")$], [`bB`], [bB (B export)], [$c_("_B") --> e_("_B")$],
  [$v_("bC")$], [`bC`], [bC (C export)], [$c_("_C") --> e_("_C")$],
  [$v_("v1")$], [`v1`], [v1 (A -\> B)], [$c_("_A") --> c_("_B")$],
  [$v_("v2")$], [`v2`], [v2 (A -\> C)], [$c_("_A") --> c_("_C")$],
  [$v_("v3")$], [`v3`], [v3 (C -\> A)], [$c_("_C") --> c_("_A")$],
  [$v_("v4")$], [`v4`], [v4 (C -\> B)], [$c_("_C") --> c_("_B")$],
  table.hline(stroke: 0.8pt),
)

The rates of the reactions are:

$ v_("bA") &= (upright("scale")_("f") dot (upright("Vmax")_("bA"))/(upright("Km")_("A")) dot (e_("_A") - c_("_A")))/(1 + (e_("_A"))/(upright("Km")_("A")) + (c_("_A"))/(upright("Km")_("A"))) \
  v_("bB") &= (upright("scale")_("f") dot (upright("Vmax")_("bB"))/(upright("Km")_("B")) dot (c_("_B") - e_("_B")))/(1 + (e_("_B"))/(upright("Km")_("B")) + (c_("_B"))/(upright("Km")_("B"))) \
  v_("bC") &= (upright("scale")_("f") dot (upright("Vmax")_("bC"))/(upright("Km")_("C")) dot (c_("_C") - e_("_C")))/(1 + (e_("_C"))/(upright("Km")_("C")) + (c_("_C"))/(upright("Km")_("C"))) \
  v_("v1") &= (upright("scale")_("f") dot upright("Vmax")_("v1"))/(upright("Km")_("A")) dot (c_("_A") - (1)/(upright("Keq")_("v1")) dot c_("_B")) \
  v_("v2") &= (upright("scale")_("f") dot upright("Vmax")_("v2"))/(upright("Km")_("A")) dot c_("_A") \
  v_("v3") &= (upright("scale")_("f") dot upright("Vmax")_("v3"))/(upright("Km")_("A")) dot c_("_C") \
  v_("v4") &= (upright("scale")_("f") dot upright("Vmax")_("v4"))/(upright("Km")_("A")) dot (c_("_C") - (1)/(upright("Keq")_("v4")) dot c_("_B")) $

= ODE system

The states change in time with the rates of the reactions:

$ (dif c_("_A"))/(dif t) &= (v_("bA") - v_("v1") - v_("v2") + v_("v3"))/(c) \
  (dif c_("_B"))/(dif t) &= (-v_("bB") + v_("v1") + v_("v4"))/(c) \
  (dif c_("_C"))/(dif t) &= (-v_("bC") + v_("v2") - v_("v3") - v_("v4"))/(c) \
  (dif e_("_A"))/(dif t) &= (-v_("bA"))/(e) \
  (dif e_("_B"))/(dif t) &= (v_("bB"))/(e) \
  (dif e_("_C"))/(dif t) &= (v_("bC"))/(e) $
