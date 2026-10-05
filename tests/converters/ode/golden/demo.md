# Koenig\_demo\_v15

Model `Koenig_demo_v15`, SBML Level 3 Version 1, read from Koenig\_demo\_v15.xml, written by sbmlutils VERSION.

Koenig Demo Metabolism

Description

This is a demonstration model in SBML format.

Terms of use

The content of this model has been carefully created in a manual research effort. This file has been created by Matthias König using sbmlutils. For questions contact koenigmx@hu-berlin.de. Copyright © 2022 Matthias König.

This work is licensed under a Creative Commons Attribution 4.0 International License.

Redistribution and use of any part of this model, with or without modification, are permitted provided that the following conditions are met:

Redistributions of this SBML file must retain the above copyright notice, this list of conditions and the following disclaimer.

Redistributions in a different form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

This model is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

## Units

| Time | Substance | Extent | Volume | Area | Length |
| --- | --- | --- | --- | --- | --- |
| s | mole | mole | m<sup>3</sup> | m<sup>2</sup> | m |

## Compartments

| Symbol | Id | Name | Size | Unit | Constant |
| --- | --- | --- | --- | --- | :---: |
| $e$ | `e` | external compartment | $10^{-6}$ | m<sup>3</sup> |  |
| $c$ | `c` | cell compartment | $10^{-6}$ | m<sup>3</sup> |  |
| $m$ | `m` | plasma membrane | $1$ | m<sup>2</sup> |  |

## Species

| Symbol | Id | Name | Compartment | Value | Unit | Properties |
| --- | --- | --- | --- | --- | --- | --- |
| $c_{\mathrm{\_A}}$ | `c__A` | A | $c$ | $0$ | mole/m<sup>3</sup> | concentration |
| $c_{\mathrm{\_B}}$ | `c__B` | B | $c$ | $0$ | mole/m<sup>3</sup> | concentration |
| $c_{\mathrm{\_C}}$ | `c__C` | C | $c$ | $0$ | mole/m<sup>3</sup> | concentration |
| $e_{\mathrm{\_A}}$ | `e__A` | A | $e$ | $0$ | mole/m<sup>3</sup> | concentration |
| $e_{\mathrm{\_B}}$ | `e__B` | B | $e$ | $0$ | mole/m<sup>3</sup> | concentration |
| $e_{\mathrm{\_C}}$ | `e__C` | C | $e$ | $0$ | mole/m<sup>3</sup> | concentration |

## Parameters

| Symbol | Id | Name | Value | Unit | Constant |
| --- | --- | --- | --- | --- | :---: |
| $\mathrm{scale}_{\mathrm{f}}$ | `scale_f` | metabolic scaling factor | $10^{-6}$ | \- | ✓ |
| $\mathrm{Vmax}_{\mathrm{bA}}$ | `Vmax_bA` |  | $5$ | mol/s | ✓ |
| $\mathrm{Km}_{\mathrm{A}}$ | `Km_A` |  | $1$ | mmol/l | ✓ |
| $\mathrm{Vmax}_{\mathrm{bB}}$ | `Vmax_bB` |  | $2$ | mol/s | ✓ |
| $\mathrm{Km}_{\mathrm{B}}$ | `Km_B` |  | $0.5$ | mmol/l | ✓ |
| $\mathrm{Vmax}_{\mathrm{bC}}$ | `Vmax_bC` |  | $2$ | mol/s | ✓ |
| $\mathrm{Km}_{\mathrm{C}}$ | `Km_C` |  | $3$ | mmol/l | ✓ |
| $\mathrm{Vmax}_{\mathrm{v1}}$ | `Vmax_v1` |  | $1$ | mol/s | ✓ |
| $\mathrm{Keq}_{\mathrm{v1}}$ | `Keq_v1` |  | $10$ | \- | ✓ |
| $\mathrm{Vmax}_{\mathrm{v2}}$ | `Vmax_v2` |  | $0.5$ | mol/s | ✓ |
| $\mathrm{Vmax}_{\mathrm{v3}}$ | `Vmax_v3` |  | $0.5$ | mol/s | ✓ |
| $\mathrm{Vmax}_{\mathrm{v4}}$ | `Vmax_v4` |  | $0.5$ | mol/s | ✓ |
| $\mathrm{Keq}_{\mathrm{v4}}$ | `Keq_v4` |  | $2$ | \- | ✓ |

## Reactions

| Rate | Id | Name | Equation |
| --- | --- | --- | --- |
| $v_{\mathrm{bA}}$ | `bA` | bA (A import) | $e_{\mathrm{\_A}} \longrightarrow c_{\mathrm{\_A}}$ |
| $v_{\mathrm{bB}}$ | `bB` | bB (B export) | $c_{\mathrm{\_B}} \longrightarrow e_{\mathrm{\_B}}$ |
| $v_{\mathrm{bC}}$ | `bC` | bC (C export) | $c_{\mathrm{\_C}} \longrightarrow e_{\mathrm{\_C}}$ |
| $v_{\mathrm{v1}}$ | `v1` | v1 (A -&gt; B) | $c_{\mathrm{\_A}} \longrightarrow c_{\mathrm{\_B}}$ |
| $v_{\mathrm{v2}}$ | `v2` | v2 (A -&gt; C) | $c_{\mathrm{\_A}} \longrightarrow c_{\mathrm{\_C}}$ |
| $v_{\mathrm{v3}}$ | `v3` | v3 (C -&gt; A) | $c_{\mathrm{\_C}} \longrightarrow c_{\mathrm{\_A}}$ |
| $v_{\mathrm{v4}}$ | `v4` | v4 (C -&gt; B) | $c_{\mathrm{\_C}} \longrightarrow c_{\mathrm{\_B}}$ |

The rates of the reactions are:

$$
\begin{aligned}
v_{\mathrm{bA}} &= \frac{\mathrm{scale}_{\mathrm{f}} \cdot \frac{\mathrm{Vmax}_{\mathrm{bA}}}{\mathrm{Km}_{\mathrm{A}}} \cdot \mathopen{}\left(e_{\mathrm{\_A}} - c_{\mathrm{\_A}}\right)}{1 + \frac{e_{\mathrm{\_A}}}{\mathrm{Km}_{\mathrm{A}}} + \frac{c_{\mathrm{\_A}}}{\mathrm{Km}_{\mathrm{A}}}} \\
v_{\mathrm{bB}} &= \frac{\mathrm{scale}_{\mathrm{f}} \cdot \frac{\mathrm{Vmax}_{\mathrm{bB}}}{\mathrm{Km}_{\mathrm{B}}} \cdot \mathopen{}\left(c_{\mathrm{\_B}} - e_{\mathrm{\_B}}\right)}{1 + \frac{e_{\mathrm{\_B}}}{\mathrm{Km}_{\mathrm{B}}} + \frac{c_{\mathrm{\_B}}}{\mathrm{Km}_{\mathrm{B}}}} \\
v_{\mathrm{bC}} &= \frac{\mathrm{scale}_{\mathrm{f}} \cdot \frac{\mathrm{Vmax}_{\mathrm{bC}}}{\mathrm{Km}_{\mathrm{C}}} \cdot \mathopen{}\left(c_{\mathrm{\_C}} - e_{\mathrm{\_C}}\right)}{1 + \frac{e_{\mathrm{\_C}}}{\mathrm{Km}_{\mathrm{C}}} + \frac{c_{\mathrm{\_C}}}{\mathrm{Km}_{\mathrm{C}}}} \\
v_{\mathrm{v1}} &= \frac{\mathrm{scale}_{\mathrm{f}} \cdot \mathrm{Vmax}_{\mathrm{v1}}}{\mathrm{Km}_{\mathrm{A}}} \cdot \mathopen{}\left(c_{\mathrm{\_A}} - \frac{1}{\mathrm{Keq}_{\mathrm{v1}}} \cdot c_{\mathrm{\_B}}\right) \\
v_{\mathrm{v2}} &= \frac{\mathrm{scale}_{\mathrm{f}} \cdot \mathrm{Vmax}_{\mathrm{v2}}}{\mathrm{Km}_{\mathrm{A}}} \cdot c_{\mathrm{\_A}} \\
v_{\mathrm{v3}} &= \frac{\mathrm{scale}_{\mathrm{f}} \cdot \mathrm{Vmax}_{\mathrm{v3}}}{\mathrm{Km}_{\mathrm{A}}} \cdot c_{\mathrm{\_C}} \\
v_{\mathrm{v4}} &= \frac{\mathrm{scale}_{\mathrm{f}} \cdot \mathrm{Vmax}_{\mathrm{v4}}}{\mathrm{Km}_{\mathrm{A}}} \cdot \mathopen{}\left(c_{\mathrm{\_C}} - \frac{1}{\mathrm{Keq}_{\mathrm{v4}}} \cdot c_{\mathrm{\_B}}\right)
\end{aligned}
$$

## ODE system

The states change in time with the rates of the reactions:

$$
\begin{aligned}
\frac{\mathrm{d} c_{\mathrm{\_A}}}{\mathrm{d} t} &= \frac{v_{\mathrm{bA}} - v_{\mathrm{v1}} - v_{\mathrm{v2}} + v_{\mathrm{v3}}}{c} \\
\frac{\mathrm{d} c_{\mathrm{\_B}}}{\mathrm{d} t} &= \frac{-v_{\mathrm{bB}} + v_{\mathrm{v1}} + v_{\mathrm{v4}}}{c} \\
\frac{\mathrm{d} c_{\mathrm{\_C}}}{\mathrm{d} t} &= \frac{-v_{\mathrm{bC}} + v_{\mathrm{v2}} - v_{\mathrm{v3}} - v_{\mathrm{v4}}}{c} \\
\frac{\mathrm{d} e_{\mathrm{\_A}}}{\mathrm{d} t} &= \frac{-v_{\mathrm{bA}}}{e} \\
\frac{\mathrm{d} e_{\mathrm{\_B}}}{\mathrm{d} t} &= \frac{v_{\mathrm{bB}}}{e} \\
\frac{\mathrm{d} e_{\mathrm{\_C}}}{\mathrm{d} t} &= \frac{v_{\mathrm{bC}}}{e}
\end{aligned}
$$
