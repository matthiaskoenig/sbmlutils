# events\_model

Model `events_model`, SBML Level 3 Version 2, read from events.xml, written by sbmlutils VERSION.

## Compartments

| Symbol | Id | Size | Constant |
| --- | --- | --- | :---: |
| $c$ | `c` | $1$ | ✓ |
| $V$ | `V` | $2$ |  |

## Species

| Symbol | Id | Name | Compartment | Value | Properties |
| --- | --- | --- | --- | --- | --- |
| $S$ | `S` | substrate | $c$ |  | concentration |
| $P$ | `P` |  | $c$ | $0$ | concentration |
| $A$ | `A` |  | $V$ | $5$ | concentration |
| $B$ | `B` |  | $V$ | $1$ | concentration |

## Parameters

| Symbol | Id | Value | Constant |
| --- | --- | --- | :---: |
| $\mathrm{vmax}$ | `vmax` | $2$ | ✓ |
| $\mathrm{km}$ | `km` | $0.5$ | ✓ |
| $k_{1}$ | `k1` | $0.1$ | ✓ |
| $k_{2}$ | `k2` |  |  |
| $S_{0}$ | `S0` | $10$ | ✓ |
| $\mathrm{total}$ | `total` | $0$ |  |

## Function definitions

$$
\begin{aligned}
\mathrm{mm}\mathopen{}\left(S, \mathrm{km}\right) &= \frac{S}{\mathrm{km} + S}
\end{aligned}
$$

## Initial assignments and assignment rules

The initial assignments set the values at $t = 0$:

$$
\begin{aligned}
S &= S_{0} \\
n_{A} &= A \cdot V
\end{aligned}
$$

The assignment rules hold at every time $t$:

$$
\begin{aligned}
A &= \frac{n_{A}}{V} \\
k_{2} &= 2 \cdot k_{1}
\end{aligned}
$$

## Reactions

| Rate | Id | Equation |
| --- | --- | --- |
| $v_{\mathrm{J0}}$ | `J0` | $S \rightleftharpoons P$ |
| $v_{\mathrm{J1}}$ | `J1` | $S + A \rightleftharpoons 2 \, P$ |

The rates of the reactions are:

$$
\begin{aligned}
v_{\mathrm{J0}} &= \mathrm{vmax} \cdot \mathrm{mm}\mathopen{}\left(S, \mathrm{km}\right) \\
v_{\mathrm{J1}} &= k_{1} \cdot S \cdot A
\end{aligned}
$$

## ODE system

The states change in time with the rates of the reactions and the rate rules:

$$
\begin{aligned}
\frac{\mathrm{d} V}{\mathrm{d} t} &= 0.1 \qquad \text{(rate rule)} \\
\frac{\mathrm{d} S}{\mathrm{d} t} &= \frac{-v_{\mathrm{J0}} - v_{\mathrm{J1}}}{c} \\
\frac{\mathrm{d} P}{\mathrm{d} t} &= \frac{v_{\mathrm{J0}} + 2 \cdot v_{\mathrm{J1}}}{c} \\
\frac{\mathrm{d} n_{A}}{\mathrm{d} t} &= -v_{\mathrm{J1}} \\
\frac{\mathrm{d} B}{\mathrm{d} t} &= -0.1 \cdot B \qquad \text{(rate rule)}
\end{aligned}
$$

The species $A$ in the compartment $V$ of variable size is integrated as its amount $n_{A}$, its concentration is $A = n_{A} / V$.

## Events

**Event `E1`** (reset)

- Trigger: $t > 5$
- Priority: $1$
- `initialValue` true, `persistent` true, `useValuesFromTriggerTime` true

$$
\begin{aligned}
V &\mathrel{:=} 2 \cdot V \\
S &\mathrel{:=} 10 \\
B &\mathrel{:=} \frac{B \cdot V}{V^{\mathrm{new}}}
\end{aligned}
$$

$B$ is converted from the size of $V$ at the execution of the event to the size $V^{\mathrm{new}}$ the event assigns, so that its amount is kept.

**Event `E2`**

- Trigger: $S < 2$
- Delay: $1$
- `initialValue` true, `persistent` true, `useValuesFromTriggerTime` true

$$
\begin{aligned}
n_{A} &\mathrel{:=} V \\
\mathrm{total} &\mathrel{:=} \mathrm{total} + 1
\end{aligned}
$$

$n_{A}$ is the amount of $A$, the assigned concentration times the size of $V$ at the execution of the event.
