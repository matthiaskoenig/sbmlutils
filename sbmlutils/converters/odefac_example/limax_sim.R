rm(list=ls())
library(deSolve)

# ----------------------
# import odes
# ----------------------
# setwd(getSrcDirectory()[1])
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))
source("limax_pkpd_38.R")

# ----------------------
# desolve simulation
# ----------------------
# Simulation time
times <- seq(0, 24, by=0.01)

# Change parameters & initial amount/concentration (in copy)
x0[39] = 5600  # indexing from 1 !

# Updated initial conditions
# TODO

# ----------------------
# ODE integration
# ----------------------
X <- ode(y=x0, times=times, func=f_dxdt, parms=p)

# Solution Matrix

Nx = length(x0)
Nt = length(times)
s <- matrix(X, nrow=Nt, ncol=(1+Nx))
colnames(s) <- c('time', xids)
colnames(s)

# s = ode.f_z(X, T, p)

# ---------------------
# plot results
# ---------------------
plot(s[, 'time'], s[, 'Ave_apap'])
