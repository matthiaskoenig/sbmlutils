# The ODE system of the model `BIOMD0000000012`: Elowitz2000 - Repressilator.
#
# Written by sbmlutils 0.13.0 from BIOMD0000000012_urn.xml, SBML L2V3.
#
# Units of the model:
#
#   time       min
#   substance  item
#   extent     item
#   volume     fl
#   area       m^2
#   length     m
#
# States x:
#
#      id  name          unit
#   1  PX  LacI protein  item
#   2  PY  TetR protein  item
#   3  PZ  cI protein    item
#   4  X   LacI mRNA     item
#   5  Y   TetR mRNA     item
#   6  Z   cI mRNA       item
#
# `initial_values(p)` returns the initial states x0 and the constants p at t = 0,
# `f_dxdt(t, x, p)` the rates of change of the states (in a list, as deSolve
# wants them) and `f_y(t, x, p)` the assigned values y, the rules and the
# reaction rates.
# `simulate(t_end)` returns a data.frame of a simulation with `deSolve::lsoda`.
# Sourcing the file needs base R only, a simulation the package deSolve; the file
# run as a script prints the head of a simulation.

# the ids of the states x, the constants p and the assigned values y
XIDS <- c(
  "PX",  # LacI protein [item]
  "PY",  # TetR protein [item]
  "PZ",  # cI protein [item]
  "X",  # LacI mRNA [item]
  "Y",  # TetR mRNA [item]
  "Z"  # cI mRNA [item]
)
PIDS <- c(
  "cell",  # [fl]
  "eff",  # translation efficiency
  "n",
  "KM",
  "tau_mRNA",  # mRNA half life
  "tau_prot",  # protein half life
  "ps_a",  # tps_active
  "ps_0"  # tps_repr
)
YIDS <- c(
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
  "Reaction12"  # transcription of CI [item/min]
)

# the names and the units of the ids, `NA` for none
NAMES <- c(
  "PX" = "LacI protein",
  "PY" = "TetR protein",
  "PZ" = "cI protein",
  "X" = "LacI mRNA",
  "Y" = "TetR mRNA",
  "Z" = "cI mRNA",
  "cell" = NA_character_,
  "eff" = "translation efficiency",
  "n" = "n",
  "KM" = "KM",
  "tau_mRNA" = "mRNA half life",
  "tau_prot" = "protein half life",
  "ps_a" = "tps_active",
  "ps_0" = "tps_repr",
  "t_ave" = "average mRNA life time",
  "beta" = "beta",
  "k_tl" = "k_tl",
  "a_tr" = "a_tr",
  "a0_tr" = "a0_tr",
  "kd_prot" = "kd_prot",
  "kd_mRNA" = "kd_mRNA",
  "alpha" = "alpha",
  "alpha0" = "alpha0",
  "Reaction1" = "degradation of LacI transcripts",
  "Reaction2" = "degradation of TetR transcripts",
  "Reaction3" = "degradation of CI transcripts",
  "Reaction4" = "translation of LacI",
  "Reaction5" = "translation of TetR",
  "Reaction6" = "translation of CI",
  "Reaction7" = "degradation of LacI",
  "Reaction8" = "degradation of TetR",
  "Reaction9" = "degradation of CI",
  "Reaction10" = "transcription of LacI",
  "Reaction11" = "transcription of TetR",
  "Reaction12" = "transcription of CI"
)
UNITS <- c(
  "PX" = "item",
  "PY" = "item",
  "PZ" = "item",
  "X" = "item",
  "Y" = "item",
  "Z" = "item",
  "cell" = "fl",
  "eff" = NA_character_,
  "n" = NA_character_,
  "KM" = NA_character_,
  "tau_mRNA" = NA_character_,
  "tau_prot" = NA_character_,
  "ps_a" = NA_character_,
  "ps_0" = NA_character_,
  "t_ave" = NA_character_,
  "beta" = NA_character_,
  "k_tl" = NA_character_,
  "a_tr" = NA_character_,
  "a0_tr" = NA_character_,
  "kd_prot" = NA_character_,
  "kd_mRNA" = NA_character_,
  "alpha" = NA_character_,
  "alpha0" = NA_character_,
  "Reaction1" = "item/min",
  "Reaction2" = "item/min",
  "Reaction3" = "item/min",
  "Reaction4" = "item/min",
  "Reaction5" = "item/min",
  "Reaction6" = "item/min",
  "Reaction7" = "item/min",
  "Reaction8" = "item/min",
  "Reaction9" = "item/min",
  "Reaction10" = "item/min",
  "Reaction11" = "item/min",
  "Reaction12" = "item/min"
)

# the default values of the constants, `NaN` for one without a value, e.g. one
# which an initial assignment sets and `initial_values` computes
P0 <- c(
  "cell" = 1,  # [fl]
  "eff" = 20,  # translation efficiency
  "n" = 2,
  "KM" = 40,
  "tau_mRNA" = 2,  # mRNA half life
  "tau_prot" = 10,  # protein half life
  "ps_a" = 0.5,  # tps_active
  "ps_0" = 0.0005  # tps_repr
)

# The initial states x0 and the constants p at t = 0.
#
# The initial values, initial assignments and the rules they need are evaluated
# in the order of their dependencies.
#
# Every constant keeps the value passed.
#
# Returns a list of the initial states x0 and the constants p, named vectors.
initial_values <- function(p = P0) {
  p <- as.numeric(p)
  # initial values
  PX <- 0  # LacI protein [item]
  PY <- 0  # TetR protein [item]
  PZ <- 0  # cI protein [item]
  X <- 0  # LacI mRNA [item]
  Y <- 20  # TetR mRNA [item]
  Z <- 0  # cI mRNA [item]
  x0 <- as.numeric(c(PX, PY, PZ, X, Y, Z))
  names(x0) <- XIDS
  names(p) <- PIDS
  list(x0 = x0, p = p)
}

# The rates of change dx/dt of the states x at the time t, in a list (deSolve).
f_dxdt <- function(t, x, p) {
  # states
  PX <- x[[1]]  # LacI protein [item]
  PY <- x[[2]]  # TetR protein [item]
  PZ <- x[[3]]  # cI protein [item]
  X <- x[[4]]  # LacI mRNA [item]
  Y <- x[[5]]  # TetR mRNA [item]
  Z <- x[[6]]  # cI mRNA [item]
  # constants
  eff <- p[[2]]  # translation efficiency
  n <- p[[3]]
  KM <- p[[4]]
  tau_mRNA <- p[[5]]  # mRNA half life
  tau_prot <- p[[6]]  # protein half life
  ps_a <- p[[7]]  # tps_active
  ps_0 <- p[[8]]  # tps_repr
  # assigned values and reaction rates
  t_ave <- tau_mRNA / log(2)  # average mRNA life time
  k_tl <- eff / t_ave
  a_tr <- (ps_a - ps_0) * 60
  a0_tr <- ps_0 * 60
  kd_prot <- log(2) / tau_prot
  kd_mRNA <- log(2) / tau_mRNA
  Reaction1 <- kd_mRNA * X  # degradation of LacI transcripts [item/min]
  Reaction2 <- kd_mRNA * Y  # degradation of TetR transcripts [item/min]
  Reaction3 <- kd_mRNA * Z  # degradation of CI transcripts [item/min]
  Reaction4 <- k_tl * X  # translation of LacI [item/min]
  Reaction5 <- k_tl * Y  # translation of TetR [item/min]
  Reaction6 <- k_tl * Z  # translation of CI [item/min]
  Reaction7 <- kd_prot * PX  # degradation of LacI [item/min]
  Reaction8 <- kd_prot * PY  # degradation of TetR [item/min]
  Reaction9 <- kd_prot * PZ  # degradation of CI [item/min]
  Reaction10 <- a0_tr + a_tr * KM ^ n / (KM ^ n + PZ ^ n)  # transcription of LacI [item/min]
  Reaction11 <- a0_tr + a_tr * KM ^ n / (KM ^ n + PX ^ n)  # transcription of TetR [item/min]
  Reaction12 <- a0_tr + a_tr * KM ^ n / (KM ^ n + PY ^ n)  # transcription of CI [item/min]
  # rates of change
  dx <- numeric(6)
  dx[[1]] <- Reaction4 - Reaction7  # dPX/dt
  dx[[2]] <- Reaction5 - Reaction8  # dPY/dt
  dx[[3]] <- Reaction6 - Reaction9  # dPZ/dt
  dx[[4]] <- -Reaction1 + Reaction10  # dX/dt
  dx[[5]] <- -Reaction2 + Reaction11  # dY/dt
  dx[[6]] <- -Reaction3 + Reaction12  # dZ/dt
  list(dx)
}

# The assigned values y at the time t, the rules and the reaction rates.
f_y <- function(t, x, p) {
  # states
  PX <- x[[1]]  # LacI protein [item]
  PY <- x[[2]]  # TetR protein [item]
  PZ <- x[[3]]  # cI protein [item]
  X <- x[[4]]  # LacI mRNA [item]
  Y <- x[[5]]  # TetR mRNA [item]
  Z <- x[[6]]  # cI mRNA [item]
  # constants
  eff <- p[[2]]  # translation efficiency
  n <- p[[3]]
  KM <- p[[4]]
  tau_mRNA <- p[[5]]  # mRNA half life
  tau_prot <- p[[6]]  # protein half life
  ps_a <- p[[7]]  # tps_active
  ps_0 <- p[[8]]  # tps_repr
  # assigned values and reaction rates
  t_ave <- tau_mRNA / log(2)  # average mRNA life time
  beta <- tau_mRNA / tau_prot
  k_tl <- eff / t_ave
  a_tr <- (ps_a - ps_0) * 60
  a0_tr <- ps_0 * 60
  kd_prot <- log(2) / tau_prot
  kd_mRNA <- log(2) / tau_mRNA
  alpha <- a_tr * eff * tau_prot / (log(2) * KM)
  alpha0 <- a0_tr * eff * tau_prot / (log(2) * KM)
  Reaction1 <- kd_mRNA * X  # degradation of LacI transcripts [item/min]
  Reaction2 <- kd_mRNA * Y  # degradation of TetR transcripts [item/min]
  Reaction3 <- kd_mRNA * Z  # degradation of CI transcripts [item/min]
  Reaction4 <- k_tl * X  # translation of LacI [item/min]
  Reaction5 <- k_tl * Y  # translation of TetR [item/min]
  Reaction6 <- k_tl * Z  # translation of CI [item/min]
  Reaction7 <- kd_prot * PX  # degradation of LacI [item/min]
  Reaction8 <- kd_prot * PY  # degradation of TetR [item/min]
  Reaction9 <- kd_prot * PZ  # degradation of CI [item/min]
  Reaction10 <- a0_tr + a_tr * KM ^ n / (KM ^ n + PZ ^ n)  # transcription of LacI [item/min]
  Reaction11 <- a0_tr + a_tr * KM ^ n / (KM ^ n + PX ^ n)  # transcription of TetR [item/min]
  Reaction12 <- a0_tr + a_tr * KM ^ n / (KM ^ n + PY ^ n)  # transcription of CI [item/min]
  as.numeric(c(
      t_ave, beta, k_tl, a_tr, a0_tr, kd_prot, kd_mRNA, alpha, alpha0, Reaction1,
      Reaction2, Reaction3, Reaction4, Reaction5, Reaction6, Reaction7, Reaction8,
      Reaction9, Reaction10, Reaction11, Reaction12
  ))
}

# the model has no events
EVENTS <- list()

# the limits of a simulation: the steps of the integrator beyond those which the
# largest step forces
MAX_STEPS <- 100000

# The states at the times, integrated with `deSolve::lsoda` from the states x at
# the first time.
#
# The integrator steps at most `hmax`. An interval which is too short for the
# integrator, to the rounding of the time, is extrapolated with the rates of
# change.
#
# Returns a list of the times, the states at them (a matrix of a row per time) and
# the number of steps, `steps` plus those of the integration. Throws an error if
# the integration fails or takes more than `max_steps` steps in all.
integrate_segment <- function(x, times, p, rtol, atol, hmax, steps, max_steps) {
  n_times <- length(times)
  if (times[[n_times]] - times[[1]] < 4 * .Machine$double.eps * max(1, abs(times))) {
    dx <- f_dxdt(times[[1]], x, p)[[1]]
    states <- matrix(x, n_times, length(x), byrow = TRUE)
    states <- states + outer(times - times[[1]], dx)
    return(list(time = times, states = states, steps = steps))
  }
  # the steps of the integrator, counted while it integrates as the new times at
  # which it evaluates the rates of change (a step evaluates them at its end, a step
  # which fails as well): deSolve limits the steps between two outputs only
  # (`maxsteps`), the count stops the integration as soon as it exceeds `max_steps`
  counted <- steps
  t_counted <- NA_real_
  exceeded <- function(t_at) {
    stop(
      "The integration took more than ", max_steps, " steps, at t = ",
      format(t_at, digits = 15), ".",
      call. = FALSE
    )
  }
  rates <- function(t, y, p) {
    if (!identical(t, t_counted)) {
      t_counted <<- t
      counted <<- counted + 1
      if (counted > max_steps) {
        exceeded(t)
      }
    }
    f_dxdt(t, y, p)
  }
  # the warnings, e.g. of the math of the model, and the messages the solver prints
  warned <- character(0)
  messages <- utils::capture.output(
    solution <- withCallingHandlers(
      deSolve::lsoda(
        x, times, rates, p,
        rtol = rtol, atol = atol,
        tcrit = times[[n_times]], hmax = if (is.finite(hmax)) hmax else 0,
        maxsteps = max(1, max_steps - steps + 1), ynames = FALSE
      ),
      warning = function(condition) {
        warned <<- c(warned, conditionMessage(condition))
        invokeRestart("muffleWarning")
      }
    )
  )
  # the messages of the solver, separated by empty lines, hold bytes which are no
  # text, e.g. of DLSODAR
  printed <- trimws(gsub("[^ -~]", "", messages, useBytes = TRUE))
  blocks <- split(printed, cumsum(!nzchar(printed)))
  solver <- unique(vapply(blocks, function(lines) {
    paste(lines[nzchar(lines)], collapse = " ")
  }, character(1)))
  solver <- solver[nzchar(solver)]
  warned <- unique(warned)
  istate <- attr(solution, "istate")
  t_reached <- attr(solution, "rstate")[[3]]
  steps <- max(counted, steps + max(1, istate[[2]]))
  if (istate[[1]] == -1 || steps > max_steps) {
    exceeded(t_reached)
  }
  if (istate[[1]] < 0) {
    stop(
      "The integration failed at t = ", format(t_reached, digits = 15), ": ",
      paste(c(warned, solver), collapse = " "),
      call. = FALSE
    )
  }
  # the warnings and the messages of the solver, one by one
  for (reported in warned) {
    warning(reported, call. = FALSE)
  }
  for (reported in solver) {
    warning(
      "The integrator reports at t = ", format(t_reached, digits = 15), ": ",
      reported,
      call. = FALSE
    )
  }
  list(
    time = solution[, 1],
    states = solution[, -1, drop = FALSE],
    steps = steps
  )
}

# Simulate the model from t = 0 to `t_end`.
#
# Arguments:
# - t_end: the end time
# - points: the number of time points, 0 and `t_end` included
# - p: the constants, `P0` if not given
# - x0: the initial states, those of `initial_values` if not given
# - rtol: the relative tolerance of the integration
# - atol: the absolute tolerance of the integration
# - hmax: the largest step of the integrator, by default the distance of the
#   time points
# - max_steps: the largest number of steps of the integrator, by default
#   `MAX_STEPS` plus twice the number of steps `hmax` forces
#
# Returns a data.frame of the time, the states and the assigned values at the
# time points.
# Throws an error if the integration fails or takes more than `max_steps` steps,
# e.g. when a state grows without bound.
simulate <- function(t_end, points = 101, p = NULL, x0 = NULL, rtol = 1e-8,
                     atol = 1e-10, hmax = NULL, max_steps = NULL) {
  initial <- initial_values(if (is.null(p)) P0 else p)
  p <- unname(initial$p)
  x <- if (is.null(x0)) unname(initial$x0) else as.numeric(x0)
  # the time points, a single one at t = 0
  times <- if (points > 1) seq(0, t_end, length.out = points) else rep(0, points)
  if (is.null(hmax)) {
    hmax <- if (points > 1 && t_end > 0) times[[2]] else Inf
  }
  if (is.null(max_steps)) {
    max_steps <- MAX_STEPS + 2 * ceiling(t_end / hmax)
  }
  xs <- rep(list(x), points)  # the states at the time points
  ps <- rep(list(p), points)  # the constants at the time points
  if (points > 1 && t_end > 0) {
    segment <- integrate_segment(x, times, p, rtol, atol, hmax, 0, max_steps)
    xs <- lapply(seq_len(points), function(k_point) segment$states[k_point, ])
  }

  # the table: the time, the states and the assigned values
  ys <- lapply(seq_len(points), function(k_point) {
    f_y(times[[k_point]], xs[[k_point]], ps[[k_point]])
  })
  xt <- matrix(as.numeric(unlist(xs)), points, length(XIDS), byrow = TRUE)
  yt <- matrix(as.numeric(unlist(ys)), points, length(YIDS), byrow = TRUE)
  data <- as.data.frame(cbind(times, xt, yt))
  names(data) <- c("time", XIDS, YIDS)
  data
}

if (sys.nframe() == 0L) {
  print(utils::head(simulate(10)))
}
