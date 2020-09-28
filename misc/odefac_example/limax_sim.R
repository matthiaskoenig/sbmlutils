rm(list=ls())
library(deSolve)

# ----------------------
# import odes
# ----------------------
# setwd(getSrcDirectory()[1])
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))
model_id = "limax_53"
source(paste0(model_id, ".R"))

# ----------------------
# APAP simulation
# ----------------------
# desolve simulation
times <- seq(0, 24, by=0.01)

# Change parameters & initial amount/concentration (no intial assignments in model)
x0['PODOSE_apap'] = 5600

# ODE integration
X <- ode(y=x0, times=times, func=f_dxdt, parms=p)
# Solution Matrix
s = f_z(times, X, p)

# plot results
plot(s[, 'time'], s[, 'Mve_apap'],
     main="desolve (APAP simulation)",
     xlab='time [h]',
     ylab='Paracetamol [mg/l]')

png(filename=paste0("./results/", model_id, "_apap_desolve.png"))
plot(s[, 'time'], s[, 'Mve_apap'],
     main="desolve",
     xlab='time [h]',
     ylab='Paracetamol [mg/l]')
dev.off()

# ----------------------
# Bicarbonate
# ----------------------
# reset everything
source(paste0(model_id, ".R"))

# desolve simulation
times <- seq(0, 5, by=0.01)

# Change parameters & initial amount/concentration (no intial assignments in model)
x0['IVDOSE_co2c13'] = 46.5  # [mg]

# ODE integration
X <- ode(y=x0, times=times, func=f_dxdt, parms=p)
# Solution Matrix
s = f_z(times, X, p)
Exhalation_co2c13 <- s[, c('Exhalation_co2c13')]
recovery = Exhalation_co2c13/60 * p['Mr_metc13']/p['Ri_co2c13'] * 100 

png(filename=paste0("./results/", model_id, "_bicarbonate_desolve.png"))
par(mfrow = c(1, 1))
plot(s[, 'time']*60, s[, 'DOB'],
     main="desolve (bicarbonate simulation)",
     xlab='time [min]',
     ylab='DOB []')
dev.off()

# ----------------------
# MBT (methacetin)
# ----------------------
# reset everything
source(paste0(model_id, ".R"))

# desolve simulation
times <- seq(0, 2.5, by=0.01)

# Change parameters & initial amount/concentration (no intial assignments in model)
x0['PODOSE_metc13'] = 75  # PODOSE_metc13 [mg]

# ODE integration
X <- ode(y=x0, times=times, func=f_dxdt, parms=p)
# Solution Matrix
s = f_z(times, X, p)
Exhalation_co2c13 <- s[, c('Exhalation_co2c13')]
Abreath_co2c13 <- s[, c('Abreath_co2c13')]

recovery = Exhalation_co2c13/(x0['PODOSE_metc13']/p['Mr_metc13']) * 100 # [% dose/h] momentary recovery
cum = Abreath_co2c13/(x0['PODOSE_metc13']/p['Mr_metc13']) * 100  # [% dose] cummulative recovery


png(filename=paste0("./results/", model_id, "_mbt_desolve.png"), width=1200, height=600)
# plot results
par(mfrow = c(1, 2))
plot(s[, 'time']*60, recovery,
     main="desolve (MBT simulation)",
     xlab='time [min]',
     ylab='Momentary 13C recovery [%dose/h]')

# plot results
plot(s[, 'time']*60, cum,
     main="desolve (MBT simulation)",
     xlab='time [min]',
     ylab='Cummulative 13C recovery [%dose]')
dev.off()
par(mfrow = c(1, 1))
