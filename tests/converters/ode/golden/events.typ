#set document(title: [events\_model])
#set page(margin: 2cm)
#set text(size: 10pt)
#set par(justify: true)
#set heading(numbering: "1.")
// the equations of a section are one block, which breaks across pages
#show math.equation.where(block: true): set block(breakable: true)
#show math.equation.where(block: true): set par(leading: 0.9em)

#align(center, text(size: 16pt, weight: "bold")[events\_model])

Model `events_model`, SBML Level 3 Version 2, read from events.xml, written by sbmlutils VERSION.

= Compartments

#table(
  columns: (auto, auto, auto, auto),
  stroke: none,
  align: (left, left, left, center),
  table.hline(stroke: 0.8pt),
  table.header([*Symbol*], [*Id*], [*Size*], [*Constant*]),
  table.hline(stroke: 0.4pt),
  [$c$], [`c`], [$1$], [#sym.checkmark],
  [$V$], [`V`], [$2$], [],
  table.hline(stroke: 0.8pt),
)

= Species

#table(
  columns: (auto, auto, 1fr, auto, auto, 1fr),
  stroke: none,
  align: (left, left, left, left, left, left),
  table.hline(stroke: 0.8pt),
  table.header([*Symbol*], [*Id*], [*Name*], [*Compartment*], [*Value*], [*Properties*]),
  table.hline(stroke: 0.4pt),
  [$S$], [`S`], [substrate], [$c$], [], [concentration],
  [$P$], [`P`], [], [$c$], [$0$], [concentration],
  [$A$], [`A`], [], [$V$], [$5$], [concentration],
  [$B$], [`B`], [], [$V$], [$1$], [concentration],
  table.hline(stroke: 0.8pt),
)

= Parameters

#table(
  columns: (auto, auto, auto, auto),
  stroke: none,
  align: (left, left, left, center),
  table.hline(stroke: 0.8pt),
  table.header([*Symbol*], [*Id*], [*Value*], [*Constant*]),
  table.hline(stroke: 0.4pt),
  [$upright("vmax")$], [`vmax`], [$2$], [#sym.checkmark],
  [$upright("km")$], [`km`], [$0.5$], [#sym.checkmark],
  [$k_(1)$], [`k1`], [$0.1$], [#sym.checkmark],
  [$k_(2)$], [`k2`], [], [],
  [$S_(0)$], [`S0`], [$10$], [#sym.checkmark],
  [$upright("total")$], [`total`], [$0$], [],
  table.hline(stroke: 0.8pt),
)

= Function definitions

$ upright("mm")(S, upright("km")) &= (S)/(upright("km") + S) $

= Initial assignments and assignment rules

The initial assignments set the values at $t = 0$:

$ S &= S_(0) \
  n_(A) &= A dot V $

The assignment rules hold at every time $t$:

$ A &= (n_(A))/(V) \
  k_(2) &= 2 dot k_(1) $

= Reactions

#table(
  columns: (auto, auto, 1fr),
  stroke: none,
  align: (left, left, left),
  table.hline(stroke: 0.8pt),
  table.header([*Rate*], [*Id*], [*Equation*]),
  table.hline(stroke: 0.4pt),
  [$v_("J0")$], [`J0`], [$S harpoons.rtlb P$],
  [$v_("J1")$], [`J1`], [$S + A harpoons.rtlb 2 thin P$],
  table.hline(stroke: 0.8pt),
)

The rates of the reactions are:

$ v_("J0") &= upright("vmax") dot upright("mm")(S, upright("km")) \
  v_("J1") &= k_(1) dot S dot A $

= ODE system

The states change in time with the rates of the reactions and the rate rules:

$ (dif V)/(dif t) &= 0.1 quad "(rate rule)" \
  (dif S)/(dif t) &= (-v_("J0") - v_("J1"))/(c) \
  (dif P)/(dif t) &= (v_("J0") + 2 dot v_("J1"))/(c) \
  (dif n_(A))/(dif t) &= -v_("J1") \
  (dif B)/(dif t) &= -0.1 dot B quad "(rate rule)" $

The species $A$ in the compartment $V$ of variable size is integrated as its amount $n_(A)$, its concentration is $A = n_(A) \/ V$.

= Events

*Event `E1`* (reset)

- Trigger: $t > 5$
- Priority: $1$
- `initialValue` true, `persistent` true, `useValuesFromTriggerTime` true

$ V &colon.eq 2 dot V \
  S &colon.eq 10 \
  B &colon.eq (B dot V)/(V^("new")) $

$B$ is converted from the size of $V$ at the execution of the event to the size $V^("new")$ the event assigns, so that its amount is kept.

*Event `E2`*

- Trigger: $S < 2$
- Delay: $1$
- `initialValue` true, `persistent` true, `useValuesFromTriggerTime` true

$ n_(A) &colon.eq V \
  upright("total") &colon.eq upright("total") + 1 $

$n_(A)$ is the amount of $A$, the assigned concentration times the size of $V$ at the execution of the event.
