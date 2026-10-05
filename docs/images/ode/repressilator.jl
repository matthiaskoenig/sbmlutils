"""
The ODE system of the model `BIOMD0000000012`: Elowitz2000 - Repressilator.

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
    1  PX  LacI protein  item
    2  PY  TetR protein  item
    3  PZ  cI protein    item
    4  X   LacI mRNA     item
    5  Y   TetR mRNA     item
    6  Z   cI mRNA       item

`initial_values(p)` returns the initial states x0 and the constants p at t = 0,
`f!(dx, x, p, t)` the rates of change of the states and `f_y(x, p, t)` the assigned
values y, the rules and the reaction rates.
`simulate(t_end)` returns a `DataFrame` of a simulation with an integrator of
OrdinaryDiffEq.
"""
module BIOMD0000000012

using DataFrames: DataFrame
import NaNMath
using OrdinaryDiffEq: ODEProblem, ReturnCode, Rodas5P, solve

export XIDS, PIDS, YIDS, NAMES, UNITS, P0, EVENTS, initial_values, f!, f_y, simulate

# the ids of the states x, the constants p and the assigned values y
const XIDS = [
    "PX",  # LacI protein [item]
    "PY",  # TetR protein [item]
    "PZ",  # cI protein [item]
    "X",  # LacI mRNA [item]
    "Y",  # TetR mRNA [item]
    "Z",  # cI mRNA [item]
]
const PIDS = [
    "cell",  # [fl]
    "eff",  # translation efficiency
    "n",
    "KM",
    "tau_mRNA",  # mRNA half life
    "tau_prot",  # protein half life
    "ps_a",  # tps_active
    "ps_0",  # tps_repr
]
const YIDS = [
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
const NAMES = Dict{String, Union{Nothing, String}}(
    "PX" => "LacI protein",
    "PY" => "TetR protein",
    "PZ" => "cI protein",
    "X" => "LacI mRNA",
    "Y" => "TetR mRNA",
    "Z" => "cI mRNA",
    "cell" => nothing,
    "eff" => "translation efficiency",
    "n" => "n",
    "KM" => "KM",
    "tau_mRNA" => "mRNA half life",
    "tau_prot" => "protein half life",
    "ps_a" => "tps_active",
    "ps_0" => "tps_repr",
    "t_ave" => "average mRNA life time",
    "beta" => "beta",
    "k_tl" => "k_tl",
    "a_tr" => "a_tr",
    "a0_tr" => "a0_tr",
    "kd_prot" => "kd_prot",
    "kd_mRNA" => "kd_mRNA",
    "alpha" => "alpha",
    "alpha0" => "alpha0",
    "Reaction1" => "degradation of LacI transcripts",
    "Reaction2" => "degradation of TetR transcripts",
    "Reaction3" => "degradation of CI transcripts",
    "Reaction4" => "translation of LacI",
    "Reaction5" => "translation of TetR",
    "Reaction6" => "translation of CI",
    "Reaction7" => "degradation of LacI",
    "Reaction8" => "degradation of TetR",
    "Reaction9" => "degradation of CI",
    "Reaction10" => "transcription of LacI",
    "Reaction11" => "transcription of TetR",
    "Reaction12" => "transcription of CI",
)
const UNITS = Dict{String, Union{Nothing, String}}(
    "PX" => "item",
    "PY" => "item",
    "PZ" => "item",
    "X" => "item",
    "Y" => "item",
    "Z" => "item",
    "cell" => "fl",
    "eff" => nothing,
    "n" => nothing,
    "KM" => nothing,
    "tau_mRNA" => nothing,
    "tau_prot" => nothing,
    "ps_a" => nothing,
    "ps_0" => nothing,
    "t_ave" => nothing,
    "beta" => nothing,
    "k_tl" => nothing,
    "a_tr" => nothing,
    "a0_tr" => nothing,
    "kd_prot" => nothing,
    "kd_mRNA" => nothing,
    "alpha" => nothing,
    "alpha0" => nothing,
    "Reaction1" => "item/min",
    "Reaction2" => "item/min",
    "Reaction3" => "item/min",
    "Reaction4" => "item/min",
    "Reaction5" => "item/min",
    "Reaction6" => "item/min",
    "Reaction7" => "item/min",
    "Reaction8" => "item/min",
    "Reaction9" => "item/min",
    "Reaction10" => "item/min",
    "Reaction11" => "item/min",
    "Reaction12" => "item/min",
)

# the default values of the constants, `NaN` for one without a value, e.g. one which an
# initial assignment sets and `initial_values` computes
const P0 = [
    1.0,  # cell
    20.0,  # eff
    2.0,  # n
    40.0,  # KM
    2.0,  # tau_mRNA
    10.0,  # tau_prot
    0.5,  # ps_a
    0.0005,  # ps_0
]

"""
    initial_values(p=P0)

The initial states x0 and the constants p at t = 0.

The initial values, initial assignments and the rules they need are evaluated in the
order of their dependencies.

Every constant keeps the value passed.

Returns the initial states x0 and the constants p, a new vector.
"""
function initial_values(p::AbstractVector{<:Real}=P0)
    p = collect(Float64, p)
    # initial values
    PX = 0.0  # LacI protein [item]
    PY = 0.0  # TetR protein [item]
    PZ = 0.0  # cI protein [item]
    X = 0.0  # LacI mRNA [item]
    Y = 20.0  # TetR mRNA [item]
    Z = 0.0  # cI mRNA [item]
    x0 = Float64[PX, PY, PZ, X, Y, Z]
    return x0, p
end

"""
    f!(dx, x, p, t)

The rates of change dx/dt of the states x at the time t, written into dx.
"""
function f!(dx, x, p, t)
    # states
    PX = x[1]  # LacI protein [item]
    PY = x[2]  # TetR protein [item]
    PZ = x[3]  # cI protein [item]
    X = x[4]  # LacI mRNA [item]
    Y = x[5]  # TetR mRNA [item]
    Z = x[6]  # cI mRNA [item]
    # constants
    eff = p[2]  # translation efficiency
    n = p[3]
    KM = p[4]
    tau_mRNA = p[5]  # mRNA half life
    tau_prot = p[6]  # protein half life
    ps_a = p[7]  # tps_active
    ps_0 = p[8]  # tps_repr
    # assigned values and reaction rates
    t_ave = tau_mRNA / NaNMath.log(2.0)  # average mRNA life time
    k_tl = eff / t_ave
    a_tr = (ps_a - ps_0) * 60.0
    a0_tr = ps_0 * 60.0
    kd_prot = NaNMath.log(2.0) / tau_prot
    kd_mRNA = NaNMath.log(2.0) / tau_mRNA
    Reaction1 = kd_mRNA * X  # degradation of LacI transcripts [item/min]
    Reaction2 = kd_mRNA * Y  # degradation of TetR transcripts [item/min]
    Reaction3 = kd_mRNA * Z  # degradation of CI transcripts [item/min]
    Reaction4 = k_tl * X  # translation of LacI [item/min]
    Reaction5 = k_tl * Y  # translation of TetR [item/min]
    Reaction6 = k_tl * Z  # translation of CI [item/min]
    Reaction7 = kd_prot * PX  # degradation of LacI [item/min]
    Reaction8 = kd_prot * PY  # degradation of TetR [item/min]
    Reaction9 = kd_prot * PZ  # degradation of CI [item/min]
    Reaction10 = a0_tr + a_tr * NaNMath.pow(KM, n) / (NaNMath.pow(KM, n) + NaNMath.pow(PZ, n))  # transcription of LacI [item/min]
    Reaction11 = a0_tr + a_tr * NaNMath.pow(KM, n) / (NaNMath.pow(KM, n) + NaNMath.pow(PX, n))  # transcription of TetR [item/min]
    Reaction12 = a0_tr + a_tr * NaNMath.pow(KM, n) / (NaNMath.pow(KM, n) + NaNMath.pow(PY, n))  # transcription of CI [item/min]
    # rates of change
    dx[1] = Reaction4 - Reaction7  # dPX/dt
    dx[2] = Reaction5 - Reaction8  # dPY/dt
    dx[3] = Reaction6 - Reaction9  # dPZ/dt
    dx[4] = -Reaction1 + Reaction10  # dX/dt
    dx[5] = -Reaction2 + Reaction11  # dY/dt
    dx[6] = -Reaction3 + Reaction12  # dZ/dt
    return nothing
end

"""
    f_y(x, p, t)

The assigned values y at the time t, the rules and the reaction rates.
"""
function f_y(x, p, t)
    # states
    PX = x[1]  # LacI protein [item]
    PY = x[2]  # TetR protein [item]
    PZ = x[3]  # cI protein [item]
    X = x[4]  # LacI mRNA [item]
    Y = x[5]  # TetR mRNA [item]
    Z = x[6]  # cI mRNA [item]
    # constants
    eff = p[2]  # translation efficiency
    n = p[3]
    KM = p[4]
    tau_mRNA = p[5]  # mRNA half life
    tau_prot = p[6]  # protein half life
    ps_a = p[7]  # tps_active
    ps_0 = p[8]  # tps_repr
    # assigned values and reaction rates
    t_ave = tau_mRNA / NaNMath.log(2.0)  # average mRNA life time
    beta = tau_mRNA / tau_prot
    k_tl = eff / t_ave
    a_tr = (ps_a - ps_0) * 60.0
    a0_tr = ps_0 * 60.0
    kd_prot = NaNMath.log(2.0) / tau_prot
    kd_mRNA = NaNMath.log(2.0) / tau_mRNA
    alpha = a_tr * eff * tau_prot / (NaNMath.log(2.0) * KM)
    alpha0 = a0_tr * eff * tau_prot / (NaNMath.log(2.0) * KM)
    Reaction1 = kd_mRNA * X  # degradation of LacI transcripts [item/min]
    Reaction2 = kd_mRNA * Y  # degradation of TetR transcripts [item/min]
    Reaction3 = kd_mRNA * Z  # degradation of CI transcripts [item/min]
    Reaction4 = k_tl * X  # translation of LacI [item/min]
    Reaction5 = k_tl * Y  # translation of TetR [item/min]
    Reaction6 = k_tl * Z  # translation of CI [item/min]
    Reaction7 = kd_prot * PX  # degradation of LacI [item/min]
    Reaction8 = kd_prot * PY  # degradation of TetR [item/min]
    Reaction9 = kd_prot * PZ  # degradation of CI [item/min]
    Reaction10 = a0_tr + a_tr * NaNMath.pow(KM, n) / (NaNMath.pow(KM, n) + NaNMath.pow(PZ, n))  # transcription of LacI [item/min]
    Reaction11 = a0_tr + a_tr * NaNMath.pow(KM, n) / (NaNMath.pow(KM, n) + NaNMath.pow(PX, n))  # transcription of TetR [item/min]
    Reaction12 = a0_tr + a_tr * NaNMath.pow(KM, n) / (NaNMath.pow(KM, n) + NaNMath.pow(PY, n))  # transcription of CI [item/min]
    return Float64[
        t_ave, beta, k_tl, a_tr, a0_tr, kd_prot, kd_mRNA, alpha, alpha0, Reaction1,
        Reaction2, Reaction3, Reaction4, Reaction5, Reaction6, Reaction7, Reaction8,
        Reaction9, Reaction10, Reaction11, Reaction12,
    ]
end

# the model has no events
const EVENTS = NamedTuple[]

# the limits of a simulation: the steps of the integrator beyond those which the
# largest step forces
const MAX_STEPS = 100000

"""
    simulate(t_end; points=101, p=nothing, x0=nothing, reltol=1e-8, abstol=1e-10,
             alg=Rodas5P(), dtmax=nothing, max_steps=nothing)

Simulate the model from t = 0 to `t_end`.

# Arguments
- `t_end`: the end time
- `points`: the number of time points, 0 and `t_end` included
- `p`: the constants, `P0` if not given
- `x0`: the initial states, those of `initial_values` if not given
- `reltol`: the relative tolerance of the integration
- `abstol`: the absolute tolerance of the integration
- `alg`: the integrator, an algorithm of OrdinaryDiffEq, e.g. `FBDF()`
- `dtmax`: the largest step of the integrator, by default the distance of the time
  points
- `max_steps`: the largest number of steps of the integrator, by default `MAX_STEPS`
  plus twice the number of steps `dtmax` forces

Returns a `DataFrame` of the time, the states and the assigned values at the time
points.
Throws an error if the integration fails or takes more than `max_steps` steps, e.g.
when a state grows without bound.
"""
function simulate(
    t_end::Real;
    points::Integer=101,
    p::Union{Nothing, AbstractVector{<:Real}}=nothing,
    x0::Union{Nothing, AbstractVector{<:Real}}=nothing,
    reltol::Real=1e-8,
    abstol::Real=1e-10,
    alg=Rodas5P(),
    dtmax::Union{Nothing, Real}=nothing,
    max_steps::Union{Nothing, Integer}=nothing,
)
    x_initial, p = initial_values(something(p, P0))
    x = x0 === nothing ? x_initial : collect(Float64, x0)
    # the time points, a single one at t = 0
    times = points > 1 ? collect(range(0.0, Float64(t_end); length=points)) : zeros(points)
    dtmax = something(dtmax, points > 1 && t_end > 0 ? times[2] : Inf)
    max_steps = something(max_steps, MAX_STEPS + 2 * ceil(Int, t_end / dtmax))
    rows = [(x, p) for _ in times]  # the states and the constants
    if t_end > 0
        problem = ODEProblem(f!, x, (0.0, Float64(t_end)), p)
        # the first step is at most the integration: OrdinaryDiffEq 7 interpolates a
        # first step which the end of the integration shortens with its full length
        solution = solve(
            problem, alg; saveat=times, reltol, abstol, dtmax=min(dtmax, t_end),
            maxiters=max_steps,
        )
        if solution.retcode == ReturnCode.MaxIters
            error(
                "The integration took more than $max_steps steps, at t = " *
                "$(solution.t[end]).",
            )
        elseif solution.retcode != ReturnCode.Success
            error("The integration failed at t = $(solution.t[end]): $(solution.retcode)")
        end
        rows = [(x, p) for x in solution.u]
    end

    # the table: the time, the states and the assigned values
    ys = [f_y(x, p, t) for (t, (x, p)) in zip(times, rows)]
    xt = Float64[x[index] for (x, _) in rows, index in eachindex(XIDS)]
    yt = Float64[y[index] for y in ys, index in eachindex(YIDS)]
    data = hcat(times, xt, yt)
    columns = ["time"; XIDS; YIDS]
    return DataFrame(data, columns; makeunique=true)
end

end  # module BIOMD0000000012
