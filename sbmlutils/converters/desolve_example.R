# --------------------------
# Example for desolve
# --------------------------

# parameter vectors with assigned names
p <- c(a = -8/3,
       b = -10,
       c =  28)
print(p)

# state variables with initial conditions
x0 <- c(X = 1,
        Y = 1,
        Z = 1)

# ode system
f_dxdt <- function(t, x, p) {
  with(as.list(c(x, p)),{
    # rate of change
    dX <- a*X + Y*Z
    dY <- b * (Y-Z)
    dZ <- -X*Y + c*Y - Z
    
    # return the rate of change
    list(c(dX, dY, dZ))
  })
}

# ----------------------
# ODE integration
# ----------------------
times <- seq(0, 100, by=0.01)
library(deSolve)
out <- ode(y=x0, times=times, func=f_dxdt, parms=p)
head(out)

plot(out, xlab = "time", ylab = "-")
plot(out[, "X"], out[, "Z"], pch = ".")
