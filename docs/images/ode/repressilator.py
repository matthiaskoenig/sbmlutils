"""The ODE system of the model BIOMD0000000012: Elowitz2000 - Repressilator.

Written by sbmlutils 0.13.0 from BIOMD0000000012_urn.xml, SBML L2V3.

Units of the model:

    time       min
    substance  item
    extent     item
    volume     fl
    area       m^2
    length     m

States x:

       id  name          unit
    0  PX  LacI protein  item
    1  PY  TetR protein  item
    2  PZ  cI protein    item
    3  X   LacI mRNA     item
    4  Y   TetR mRNA     item
    5  Z   cI mRNA       item

`initial_values(p)` returns the initial states x0 and the constants p at t = 0,
`f_dxdt(t, x, p)` the rates of change of the states and `f_y(t, x, p)` the assigned
values y, the rules and the reaction rates.
`simulate(t_end)` integrates the model with an integrator of `scipy.integrate`,
the file run as a script prints the head of a simulation.
"""

from functools import partial

import numpy as np
import pandas as pd
import scipy.integrate

# the ids of the states x, the constants p and the assigned values y
XIDS = [
    "PX",  # LacI protein [item]
    "PY",  # TetR protein [item]
    "PZ",  # cI protein [item]
    "X",  # LacI mRNA [item]
    "Y",  # TetR mRNA [item]
    "Z",  # cI mRNA [item]
]
PIDS = [
    "cell",  # [fl]
    "eff",  # translation efficiency
    "n",
    "KM",
    "tau_mRNA",  # mRNA half life
    "tau_prot",  # protein half life
    "ps_a",  # tps_active
    "ps_0",  # tps_repr
]
YIDS = [
    "t_ave",  # average mRNA life time
    "beta",
    "k_tl",
    "a_tr",
    "a0_tr",
    "kd_prot",
    "kd_mRNA",
    "alpha",
    "alpha0",
    "Reaction1",  # degradation of LacI transcripts [item/min]
    "Reaction2",  # degradation of TetR transcripts [item/min]
    "Reaction3",  # degradation of CI transcripts [item/min]
    "Reaction4",  # translation of LacI [item/min]
    "Reaction5",  # translation of TetR [item/min]
    "Reaction6",  # translation of CI [item/min]
    "Reaction7",  # degradation of LacI [item/min]
    "Reaction8",  # degradation of TetR [item/min]
    "Reaction9",  # degradation of CI [item/min]
    "Reaction10",  # transcription of LacI [item/min]
    "Reaction11",  # transcription of TetR [item/min]
    "Reaction12",  # transcription of CI [item/min]
]

# the names and the units of the ids
NAMES = {
    "PX": "LacI protein",
    "PY": "TetR protein",
    "PZ": "cI protein",
    "X": "LacI mRNA",
    "Y": "TetR mRNA",
    "Z": "cI mRNA",
    "cell": None,
    "eff": "translation efficiency",
    "n": "n",
    "KM": "KM",
    "tau_mRNA": "mRNA half life",
    "tau_prot": "protein half life",
    "ps_a": "tps_active",
    "ps_0": "tps_repr",
    "t_ave": "average mRNA life time",
    "beta": "beta",
    "k_tl": "k_tl",
    "a_tr": "a_tr",
    "a0_tr": "a0_tr",
    "kd_prot": "kd_prot",
    "kd_mRNA": "kd_mRNA",
    "alpha": "alpha",
    "alpha0": "alpha0",
    "Reaction1": "degradation of LacI transcripts",
    "Reaction2": "degradation of TetR transcripts",
    "Reaction3": "degradation of CI transcripts",
    "Reaction4": "translation of LacI",
    "Reaction5": "translation of TetR",
    "Reaction6": "translation of CI",
    "Reaction7": "degradation of LacI",
    "Reaction8": "degradation of TetR",
    "Reaction9": "degradation of CI",
    "Reaction10": "transcription of LacI",
    "Reaction11": "transcription of TetR",
    "Reaction12": "transcription of CI",
}
UNITS = {
    "PX": "item",
    "PY": "item",
    "PZ": "item",
    "X": "item",
    "Y": "item",
    "Z": "item",
    "cell": "fl",
    "eff": None,
    "n": None,
    "KM": None,
    "tau_mRNA": None,
    "tau_prot": None,
    "ps_a": None,
    "ps_0": None,
    "t_ave": None,
    "beta": None,
    "k_tl": None,
    "a_tr": None,
    "a0_tr": None,
    "kd_prot": None,
    "kd_mRNA": None,
    "alpha": None,
    "alpha0": None,
    "Reaction1": "item/min",
    "Reaction2": "item/min",
    "Reaction3": "item/min",
    "Reaction4": "item/min",
    "Reaction5": "item/min",
    "Reaction6": "item/min",
    "Reaction7": "item/min",
    "Reaction8": "item/min",
    "Reaction9": "item/min",
    "Reaction10": "item/min",
    "Reaction11": "item/min",
    "Reaction12": "item/min",
}

# the default values of the constants, `np.nan` for one without a value, e.g. one
# which an initial assignment sets and `initial_values` computes
P0 = np.array([
    1.0,  # cell
    20.0,  # eff
    2.0,  # n
    40.0,  # KM
    2.0,  # tau_mRNA
    10.0,  # tau_prot
    0.5,  # ps_a
    0.0005,  # ps_0
])


def initial_values(p: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """The initial states x0 and the constants p at t = 0.

    The initial values, initial assignments and the rules they need are evaluated
    in the order of their dependencies.

    Every constant keeps the value passed.

    Args:
        p: the constants, `P0` if not given

    Returns:
        the initial states x0 and the constants p, a new array
    """
    p = np.array(P0 if p is None else p, dtype=float)
    # initial values
    PX = 0.0  # LacI protein [item]
    PY = 0.0  # TetR protein [item]
    PZ = 0.0  # cI protein [item]
    X = 0.0  # LacI mRNA [item]
    Y = 20.0  # TetR mRNA [item]
    Z = 0.0  # cI mRNA [item]
    x0 = np.array([PX, PY, PZ, X, Y, Z], dtype=float)
    return x0, p


def f_dxdt(t: float, x: np.ndarray, p: np.ndarray) -> np.ndarray:
    """The rates of change dx/dt of the states x at the time t."""
    # states
    PX = x[0]  # LacI protein [item]
    PY = x[1]  # TetR protein [item]
    PZ = x[2]  # cI protein [item]
    X = x[3]  # LacI mRNA [item]
    Y = x[4]  # TetR mRNA [item]
    Z = x[5]  # cI mRNA [item]
    # constants
    eff = p[1]  # translation efficiency
    n = p[2]
    KM = p[3]
    tau_mRNA = p[4]  # mRNA half life
    tau_prot = p[5]  # protein half life
    ps_a = p[6]  # tps_active
    ps_0 = p[7]  # tps_repr
    # assigned values and reaction rates
    t_ave = tau_mRNA / np.log(2.0)  # average mRNA life time
    k_tl = eff / t_ave
    a_tr = (ps_a - ps_0) * 60.0
    a0_tr = ps_0 * 60.0
    kd_prot = np.log(2.0) / tau_prot
    kd_mRNA = np.log(2.0) / tau_mRNA
    Reaction1 = kd_mRNA * X  # degradation of LacI transcripts [item/min]
    Reaction2 = kd_mRNA * Y  # degradation of TetR transcripts [item/min]
    Reaction3 = kd_mRNA * Z  # degradation of CI transcripts [item/min]
    Reaction4 = k_tl * X  # translation of LacI [item/min]
    Reaction5 = k_tl * Y  # translation of TetR [item/min]
    Reaction6 = k_tl * Z  # translation of CI [item/min]
    Reaction7 = kd_prot * PX  # degradation of LacI [item/min]
    Reaction8 = kd_prot * PY  # degradation of TetR [item/min]
    Reaction9 = kd_prot * PZ  # degradation of CI [item/min]
    Reaction10 = a0_tr + a_tr * KM ** n / (KM ** n + PZ ** n)  # transcription of LacI [item/min]
    Reaction11 = a0_tr + a_tr * KM ** n / (KM ** n + PX ** n)  # transcription of TetR [item/min]
    Reaction12 = a0_tr + a_tr * KM ** n / (KM ** n + PY ** n)  # transcription of CI [item/min]
    # rates of change
    dx = np.zeros(6)
    dx[0] = Reaction4 - Reaction7  # dPX/dt
    dx[1] = Reaction5 - Reaction8  # dPY/dt
    dx[2] = Reaction6 - Reaction9  # dPZ/dt
    dx[3] = -Reaction1 + Reaction10  # dX/dt
    dx[4] = -Reaction2 + Reaction11  # dY/dt
    dx[5] = -Reaction3 + Reaction12  # dZ/dt
    return dx


def f_y(t: float, x: np.ndarray, p: np.ndarray) -> np.ndarray:
    """The assigned values y at the time t, the rules and the reaction rates."""
    # states
    PX = x[0]  # LacI protein [item]
    PY = x[1]  # TetR protein [item]
    PZ = x[2]  # cI protein [item]
    X = x[3]  # LacI mRNA [item]
    Y = x[4]  # TetR mRNA [item]
    Z = x[5]  # cI mRNA [item]
    # constants
    eff = p[1]  # translation efficiency
    n = p[2]
    KM = p[3]
    tau_mRNA = p[4]  # mRNA half life
    tau_prot = p[5]  # protein half life
    ps_a = p[6]  # tps_active
    ps_0 = p[7]  # tps_repr
    # assigned values and reaction rates
    t_ave = tau_mRNA / np.log(2.0)  # average mRNA life time
    beta = tau_mRNA / tau_prot
    k_tl = eff / t_ave
    a_tr = (ps_a - ps_0) * 60.0
    a0_tr = ps_0 * 60.0
    kd_prot = np.log(2.0) / tau_prot
    kd_mRNA = np.log(2.0) / tau_mRNA
    alpha = a_tr * eff * tau_prot / (np.log(2.0) * KM)
    alpha0 = a0_tr * eff * tau_prot / (np.log(2.0) * KM)
    Reaction1 = kd_mRNA * X  # degradation of LacI transcripts [item/min]
    Reaction2 = kd_mRNA * Y  # degradation of TetR transcripts [item/min]
    Reaction3 = kd_mRNA * Z  # degradation of CI transcripts [item/min]
    Reaction4 = k_tl * X  # translation of LacI [item/min]
    Reaction5 = k_tl * Y  # translation of TetR [item/min]
    Reaction6 = k_tl * Z  # translation of CI [item/min]
    Reaction7 = kd_prot * PX  # degradation of LacI [item/min]
    Reaction8 = kd_prot * PY  # degradation of TetR [item/min]
    Reaction9 = kd_prot * PZ  # degradation of CI [item/min]
    Reaction10 = a0_tr + a_tr * KM ** n / (KM ** n + PZ ** n)  # transcription of LacI [item/min]
    Reaction11 = a0_tr + a_tr * KM ** n / (KM ** n + PX ** n)  # transcription of TetR [item/min]
    Reaction12 = a0_tr + a_tr * KM ** n / (KM ** n + PY ** n)  # transcription of CI [item/min]
    return np.array([
        t_ave, beta, k_tl, a_tr, a0_tr, kd_prot, kd_mRNA, alpha, alpha0, Reaction1,
        Reaction2, Reaction3, Reaction4, Reaction5, Reaction6, Reaction7, Reaction8,
        Reaction9, Reaction10, Reaction11, Reaction12,
    ], dtype=float)


# the model has no events
EVENTS = []


# the limits of a simulation: the steps of the integrator beyond those which the largest
# step forces
MAX_STEPS = 100000


def simulate(
    t_end: float,
    points: int = 101,
    p: np.ndarray | None = None,
    x0: np.ndarray | None = None,
    rtol: float = 1e-8,
    atol: float = 1e-10,
    method: str = "LSODA",
    max_step: float | None = None,
    max_steps: int | None = None,
) -> pd.DataFrame:
    """Simulate the model from t = 0 to `t_end`.

    Args:
        t_end: the end time
        points: the number of time points, 0 and `t_end` included
        p: the constants, `P0` if not given
        x0: the initial states, those of `initial_values` if not given
        rtol: the relative tolerance of the integration
        atol: the absolute tolerance of the integration
        method: the integrator, a class of `scipy.integrate`, e.g. `"BDF"`
        max_step: the largest step of the integrator, by default the distance of
            the time points
        max_steps: the largest number of steps of the integrator, by default
            `MAX_STEPS` plus twice the number of steps `max_step` forces

    Returns:
        the time, the states and the assigned values at the time points

    Raises:
        RuntimeError: if the integration fails, takes more than `max_steps` steps
            or its step is too small to advance the time, e.g. when a state grows
            without bound
    """
    x_initial, p = initial_values(p)
    x = x_initial if x0 is None else np.array(x0, dtype=float)
    times = np.linspace(0.0, t_end, points)
    if max_step is None:
        max_step = times[1] if points > 1 and t_end > 0 else np.inf
    if max_steps is None:
        max_steps = MAX_STEPS + 2 * int(np.ceil(t_end / max_step))
    solver_type = getattr(scipy.integrate, method)  # e.g. scipy.integrate.LSODA
    rows = []  # the states and the constants at each time point
    steps = 0  # the steps of the integrator

    t = 0.0
    while t < t_end:
        t_stop = t_end
        solver = solver_type(
            partial(f_dxdt, p=p), t, x, t_stop, rtol=rtol, atol=atol, max_step=max_step
        )
        while True:
            solver.step()
            steps += 1
            if solver.status == "failed":
                raise RuntimeError(f"The integration failed: {solver.message}")
            if steps > max_steps:
                raise RuntimeError(
                    f"The integration took more than {max_steps} steps, at t = "
                    f"{solver.t}."
                )
            step_size = solver.t - solver.t_old
            if solver.status == "running" and step_size <= 4 * np.spacing(solver.t):
                raise RuntimeError(
                    f"The step of the integration is too small to advance the time "
                    f"at t = {solver.t}, a state may grow without bound."
                )
            interpolant = solver.dense_output()
            # the time points of the step
            while len(rows) < points and times[len(rows)] < solver.t:
                rows.append((interpolant(times[len(rows)]), p))
            if solver.status == "finished":
                break
        t, x = solver.t, solver.y
    # the time points at t_end
    rows.extend((x, p) for _ in range(points - len(rows)))

    xt = np.array([x for x, _ in rows]).reshape(points, len(XIDS))
    yt = np.array([f_y(t, x, p) for t, (x, p) in zip(times, rows, strict=True)])
    data = np.column_stack([times, xt, yt.reshape(points, len(YIDS))])
    return pd.DataFrame(data, columns=["time", *XIDS, *YIDS])


if __name__ == "__main__":
    print(simulate(t_end=10.0).head())
