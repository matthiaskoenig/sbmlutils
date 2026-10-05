FROM rocker/r-ver:4.4
RUN Rscript -e 'install.packages("deSolve", repos = "https://cloud.r-project.org")'
