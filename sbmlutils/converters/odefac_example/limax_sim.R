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
s = f_z(times, X, p)

# ---------------------
# plot results
# ---------------------
png(filename="./results/desolve.png")
plot(s[, 'time'], s[, 'Mve_apap'], 
     main="desolve",
     xlab='time [h]', 
     ylab='Paracetamol [mg/l]')
dev.off()
