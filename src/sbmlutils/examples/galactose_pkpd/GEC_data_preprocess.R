################################################################
## Data analysis & dataset combination for GEC modeling
################################################################
# Loading, preprocessing & combination of datasets for prediction 
# and for fitting of regression models.
# Here the experimental data is prepared to use in models.
#
# author: Matthias Koenig
# date: 2015-02-18
###############################################################

rm(list=ls())
library(MultiscaleAnalysis)
setwd(ma.settings$dir.results)

##############################################
# Dataset functions & parameters
##############################################
f_liver_density = 1.25     # [g/ml] conversion between volume and weight
f_co_fraction = 0.25       # [-] Liver bloodflow as fraction of cardiac output
dtypes <- c('population', 'individual') # individual or population data


##############################################
# Read datasets
##############################################

# sex, age, liverVolume
alt1962 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Altman1962.csv"), sep="\t")
alt1962$volLiver <- alt1962$liverWeight/f_liver_density * 1000; # [ml]
alt1962$volLiverSd <- NA
alt1962$ageRange <- 0.5*(alt1962$ageMax-alt1962$ageMin)
alt1962 <- process_data_and_save(alt1962, dtype='population')
head(alt1962)

# age [years], volLiver [ml], BSA [m^2], volLiverPerBSA [ml/m^2]
bac1981 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Bach1981_Tab2.csv"), sep="\t")
bac1981 <- process_data_and_save(bac1981, dtype='population')
head(bac1981)

# age [years], sex [M,F], liverWeight [g]
boy1933 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Boyd1933_Fig1.csv"), sep="\t")
boy1933$volLiver <- boy1933$liverWeight/f_liver_density; # [ml]
boy1933 <- process_data_and_save(boy1933, dtype='individual')
head(boy1933)

# age [years], sex [M,F], BSA [m^2], liverBloodFlow [ml/min]
bra1945 <- read.csv(file.path(ma.settings$dir.expdata, "liver_bloodflow", "Bradley1945.csv"), sep="\t")
bra1945$flowLiver <- bra1945$liverBloodFlow
bra1945 <- process_data_and_save(bra1945, dtype='individual')
head(bra1945)

# age [years], sex [M,F], BSA [m^2], liverBloodFlow [ml/min]
bra1952 <- read.csv(file.path(ma.settings$dir.expdata, "liver_bloodflow", "Bradley1952_Tab1.csv"), sep="\t")
bra1952$flowLiver <- bra1952$liverBloodFlow
bra1952 <- process_data_and_save(bra1952, dtype='individual')
head(bra1952)

# age [years], sex [U], cardiac_output [L/min]
# liver blood flow estimated via cardiac output
# cat2010 <- read.csv(file.path(ma.settings$dir.expdata, "cardiac_output", "Cattermole2010_Tab2.csv"), sep="\t")
# cat2010$flowLiver <- cat2010$CO * 1000 * f_co_fraction # [ml/min]
# cat2010$flowLiverMin <- cat2010$COMin * 1000 * f_co_fraction # [ml/min]
# cat2010$flowLiverMax <- cat2010$COMax * 1000 * f_co_fraction # [ml/min]
# cat2010$ageRange <- 0.5*(cat2010$ageMax - cat2010$ageMin)
# # cat2010$flowLiverRange <- 0.5*(cat2010$flowLiverMax - cat2010$flowLiverMin)
# cat2010$flowLiverSd <- 0.5*(cat2010$flowLiverMax - cat2010$flowLiverMin)/2 # only estimate!, read from centiles
# cat2010 <- process_data_and_save(cat2010, dtype='population')
# head(cat2010)

# liver blood flow estimated via cardiac output
# age [years], sex [M,F], bodyweight [kg], height [cm], BSA [m^2], cardiac_output [mL/min], cardiac_outputkg [ml/min/kg]
cat.factor <- 0.75 # data is overestimating the blood flow in comparison to Simmone1997
cat2010 <- read.csv(file.path(ma.settings$dir.expdata, 'raw_data', "cattermole", "Koenig_Cattermole2009.csv"), sep="\t")
cat2010$flowLiver <- cat2010$CO * f_co_fraction * cat.factor # [ml/min]
cat2010$flowLiverkg <- cat2010$COkg * f_co_fraction * cat.factor # [ml/min]
cat2010 <- cat2010[complete.cases(cat2010), ]
cat2010 <- process_data_and_save(cat2010, dtype='individual')
head(cat2010)

# weight [kg], liverWeight [kg], liverWeightSd [kg]
del1968.fig1 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "DeLand1968_Fig1.csv"), sep="\t")
del1968.fig1$bodyweight <- del1968.fig1$weight
del1968.fig1$volLiver <- del1968.fig1$liverWeight/f_liver_density * 1000; # [ml]
del1968.fig1$volLiverSd <- del1968.fig1$liverWeightSd/f_liver_density * 1000; # [ml]
del1968.fig1$n <- 10  # n estimated, ~ 10 in every class
del1968.fig1$bodyweightRange <- 0.5*(del1968.fig1$weightMax-del1968.fig1$weightMin)
del1968.fig1 <- process_data_and_save(del1968.fig1, dtype='population')
head(del1968.fig1)

# height [cm], liverWeight [kg], liverWeightSd [kg]
del1968.fig3 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "DeLand1968_Fig3.csv"), sep="\t")
del1968.fig3$volLiver <- del1968.fig3$liverWeight/f_liver_density * 1000; # [ml]
del1968.fig3$volLiverSd <- del1968.fig3$liverWeightSd/f_liver_density * 1000; # [ml]
del1968.fig3$n <- 10  # n estimated, ~ 10 in every class
del1968.fig3$heightRange <- 0.5*(del1968.fig3$heightMax-del1968.fig3$heightMin)
del1968.fig3 <- process_data_and_save(del1968.fig3, dtype='population')
head(del1968.fig3)

# BSA [m^2], liverWeight [kg], liverWeightSd [kg]
del1968.fig4 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "DeLand1968_Fig4.csv"), sep="\t")
del1968.fig4 <- del1968.fig4[complete.cases(del1968.fig4), ] # remove NA in liver weight
del1968.fig4$volLiver <- del1968.fig4$liverWeight/f_liver_density * 1000; # [ml]
del1968.fig4$volLiverSd <- del1968.fig4$liverWeightSd/f_liver_density * 1000; # [ml]
del1968.fig4$n <- 10  # n estimated, ~ 10 in every class
del1968.fig4$BSARange <- 0.5*(del1968.fig4$BSAMax-del1968.fig4$BSAMin)
del1968.fig4 <- process_data_and_save(del1968.fig4, dtype='population')
head(del1968.fig4)

# age [years], bodyweight [kg], GEC [mmol/min], GEC [mmol/min/kg] 
duc1979 <- read.csv(file.path(ma.settings$dir.expdata, "GEC", "Ducry1979_Tab1.csv"), sep="\t")
duc1979$BSA <- calculateBSA(bodyweight_kg=duc1979$bodyweight, height_cm=duc1979$height)
duc1979 <- process_data_and_save(duc1979, dtype="individual")
head(duc1979)

# age [years], sex [M,F], GECmg [mg/min/kg], GEC [mmol/min/kg] 
# age [years], gender [male, female], GECkg [mmole/min/kg]
duf1992 <- read.csv(file.path(ma.settings$dir.expdata, "GEC", "Dufour1992_Tab1.csv"), sep="\t")
duf1992$GECkg <- duf1992$GECmg/180
duf1992 <- duf1992[!is.na(duf1992$GEC), ] # filter cases without GEC
duf1992 <- process_data_and_save(duf1992, dtype='individual')
head(duf1992)

# sex [M,F], height [cm], liverWeight [kg] 
gra2000.tab1 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Grandmaison2000_Tab1.csv"), sep="\t")
gra2000.tab1$height <- gra2000.tab1$heightMean
gra2000.tab1$heightRange <- 0.5*(gra2000.tab1$heightMax - gra2000.tab1$heightMin)
gra2000.tab1$volLiver <- gra2000.tab1$liverWeight/f_liver_density * 1000; # [ml]
gra2000.tab1$volLiverSd <- gra2000.tab1$liverWeightSd/f_liver_density * 1000; # [ml]
gra2000.tab1 <- process_data_and_save(gra2000.tab1, dtype='population')
head(gra2000.tab1)

# sex [M,F], bmi [kg/m^2], liverWeight [kg] 
gra2000.tab2 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Grandmaison2000_Tab2.csv"), sep="\t")
gra2000.tab2$bmi <- gra2000.tab2$bmiMean
gra2000.tab2$bmiRange <- 0.5*(gra2000.tab2$bmiMax - gra2000.tab2$bmiMin)
gra2000.tab2$volLiver <- gra2000.tab2$liverWeight/f_liver_density * 1000; # [ml]
gra2000.tab2$volLiverSd <- gra2000.tab2$liverWeightSd/f_liver_density * 1000; # [ml]
gra2000.tab2 <- process_data_and_save(gra2000.tab2, dtype='population')
head(gra2000.tab2)

# digitized BSA [m^2], liverVol [ml]
# hei1999 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Heinemann1999.csv"), sep="\t")
# hei1999$gender <- as.character(hei1999$sex)
# hei1999$gender[hei1999$gender=='U'] <- 'all'
# hei1999$volLiver <- hei1999$liverVol
# head(hei1999)

# original data
hei1999 <- read.csv(file.path(ma.settings$dir.expdata, "raw_data", "heinemann", "Heinemann1999.csv"), sep="\t")
hei1999$volLiver <- hei1999$liverWeight/f_liver_density  # [ml]
hei1999$volLiverkg <- hei1999$volLiver/hei1999$bodyweight # [ml/kg]
hei1999$BSA <- hei1999$BSA_DuBois # use the DuBois calculation
# remove outliers found by graphical analysis
outliers.1 <- which((hei1999$liverWeight<500) & (hei1999$age>5))
outliers.2 <- which((hei1999$liverWeight>1500) & (hei1999$liverWeight<2000) & (hei1999$age<10))
outliers.3 <- which((hei1999$BSA_DuBois<0.5) & (hei1999$liverWeight/hei1999$bodyweight<20))
outliers <- c(outliers.1, outliers.2, outliers.3)
hei1999 <- hei1999[-outliers, ]
rm(outliers.1, outliers.2, outliers.3)
# remove the obese people, i.e. only BMI <25 
hei1999 <- hei1999[hei1999$BMI<25, ]
hei1999 <- process_data_and_save(hei1999, dtype='individual')
head(hei1999)


# age [years], sex [M,F], cardiac_output [L/min], liver blood flow [L/min]
# liver blood flow estimated via cardia output
ircp2001.co <- read.csv(file.path(ma.settings$dir.expdata, "cardiac_output", "IRCP2001_CO.csv"), sep="\t")
ircp2001.co$flowLiver <- ircp2001.co$CO * 1000 * f_co_fraction # [ml/min]
ircp2001.co <- process_data_and_save(ircp2001.co, dtype='individual')
head(ircp2001.co)

# sex [M,F], age [years], livWeight [g]
kay1987 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Kayser1987.csv"), sep="\t")
kay1987$volLiver <- kay1987$livWeight/f_liver_density  # [ml]
kay1987$volLiverSd <- kay1987$livWeightSd/f_liver_density  # [ml]
kay1987$ageRange <- 0.5*(kay1987$ageMax - kay1987$ageMin)  # [ml]
kay1987 <- process_data_and_save(kay1987, dtype='population')
head(kay1987)

# age [years], GEC [µmol/min/kg]
lan2011 <- read.csv(file.path(ma.settings$dir.expdata, "GEC", "Lange2011_Fig1.csv"), sep="\t")
lan2011$GECmumolkg <- lan2011$GEC
lan2011$GECkg <- lan2011$GECkg/1000
lan2011 <- process_data_and_save(lan2011, dtype='individual')
head(lan2011)

# age [years], Sex [M], BSA [m^2], EHBF [ml/min]
lee1962 <- read.csv(file.path(ma.settings$dir.expdata, "liver_bloodflow", "Leevy1962_Tab1.csv"), sep="\t")
lee1962$flowLiver <- lee1962$BSP_EHBF
lee1962 <- process_data_and_save(lee1962, dtype='individual')
head(lee1962)

# age [years], GEC (galactose elimination capacity) [mmol/min], 
# HVI (hepatic volumetric index) [units], volLiver [cm^3]
mar1988 <- read.csv(file.path(ma.settings$dir.expdata, "GEC", "Marchesini1988_Fig.csv"), sep="\t")
mar1988 <- data.frame(subject=mar1988$subject, 
                      age=mar1988$age,
                      GEC=mar1988$GEC,
                      HVI=mar1988$HVI[order(mar1988$subject)],
                      volLiver=mar1988$volLiver[order(mar1988$subject)])
mar1988$study = 'mar1988'
mar1988$status = 'healthy'
mar1988$gender = 'all'
mar1988 <- process_data_and_save(mar1988, dtype='individual')
head(mar1988)

# age [years], sex [M,F], bodyweight [kg], BSA [kg/m^2], liverVol [ml], height [cm] 
naw1998 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Nawaratne1998_Tab1.csv"), sep="\t")
naw1998$volLiver <- naw1998$liverVol
naw1998$volLiverkg <- naw1998$volLiver/naw1998$bodyweight  # [ml/kg]
naw1998 <- process_data_and_save(naw1998, dtype='individual')
head(naw1998)

# sex [M, F], age [years], bodyweight [kg], height [cm], BSA [m^2], flowLiver [ml/min]
she1950 <- read.csv(file.path(ma.settings$dir.expdata, "liver_bloodflow", "Sherlock1950.csv"), sep="\t")
she1950$flowLiver <- she1950$liverBloodflow
she1950$flowLiverkg <- she1950$flowLiver/she1950$bodyweight
she1950 <- process_data_and_save(she1950, dtype='individual')
head(she1950)

# sex [m,f], age [years], bodyweight [kg], GEC [mg/min/kg]
sch1986.tab1 <- read.csv(file.path(ma.settings$dir.expdata, "GEC", "Schnegg1986_Tab1.csv"), sep="\t")
sch1986.tab1$GECmgkg <- sch1986.tab1$GEC
sch1986.tab1$GEC <- sch1986.tab1$GECmgkg * sch1986.tab1$bodyweight/180; # [mg/min/kg -> mmol/min]
sch1986.tab1$GECkg <- sch1986.tab1$GECmgkg/180
sch1986.tab1 <- process_data_and_save(sch1986.tab1, dtype='individual')
head(sch1986.tab1)

# age [years], GEC [mg/min/kg]
sch1986.fig1 <- read.csv(file.path(ma.settings$dir.expdata, "GEC", "Schnegg1986_Fig1.csv"), sep="\t")
sch1986.fig1$GECmgkg <- sch1986.fig1$GEC
sch1986.fig1$GECkg   <- sch1986.fig1$GEC/180
sch1986.fig1 <- process_data_and_save(sch1986.fig1, dtype='individual')
head(sch1986.fig1)

# age [years], bodyweight [kg], volLiver [ml], volLiverkg [ml/kg]
swi1978 <- read.csv(file.path(ma.settings$dir.expdata, "GEC", "Swift1978_Tab1.csv"), sep="\t")
swi1978$ageRange <- 0.5*(swi1978$ageMax - swi1978$ageMin)
swi1978 <- swi1978[-3, ]     # remove hospitalized cases
swi1978 <- process_data_and_save(swi1978, dtype='population')
head(swi1978)

# bodyweight [kg], COkg [ml/min/kg], CO [ml/min]
sim1997 <- read.csv(file.path(ma.settings$dir.expdata, "cardiac_output", "Simmone1997.csv"), sep="\t")
sim1997$flowLiver <- sim1997$CO * f_co_fraction # [ml/min]
sim1997$flowLiverkg <- sim1997$COkg * f_co_fraction # [ml/min]
sim1997 <- process_data_and_save(sim1997, dtype='individual')
head(sim1997)

# sex [M], age [years], bodyweight [kg], liverWeight [kg]
tom1965 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Thompson1965.csv"), sep="\t")
tom1965$volLiver <- tom1965$liverWeight/f_liver_density * 1000; # [ml]
tom1965$volLiverSd <- tom1965$liverWeightSd/f_liver_density * 1000; # [ml]
tom1965$ageRange <- 0.5*(tom1965$ageMax - tom1965$ageMin)
tom1965 <- process_data_and_save(tom1965, dtype='population')
head(tom1965)

# sex [M, F], age [years], bodyweight [kg], BSA [m^2], flowLiver [ml/min], flowLiverkg [ml/min/kg]
tyg1958 <- read.csv(file.path(ma.settings$dir.expdata, "GEC", "Tygstrup1958.csv"), sep="\t")
tyg1958$flowLiver <- tyg1958$bloodflowBS
tyg1958$flowLiverkg <- tyg1958$bloodflowBS/tyg1958$bodyweight
# tyg1958 <- tyg1958[tyg1958$status=='healthy', ]          # reduce to healthy
tyg1958 <- tyg1958[-which(tyg1958$exp %in% c(11,22)), ] # remove strange outlier
tyg1958 <- tyg1958[!is.na(tyg1958$flowLiver), ]
tyg1958 <- process_data_and_save(tyg1958, dtype='individual')
head(tyg1958)

# age [years], bodyweight [kg], GEC [mmol/min]
tyg1963 <- read.csv(file.path(ma.settings$dir.expdata, "GEC", "Tygstrup1963.csv"), sep="\t")
tyg1963$GECkg <- tyg1963$GEC/tyg1963$bodyweight
tyg1963 <- process_data_and_save(tyg1963, dtype='individual')
head(tyg1963)

# BSA [m^2], liverVol [ml]
ura1995.fig2 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Urata1995_Fig2.csv"), sep="\t")
ura1995.fig2 <- process_data_and_save(ura1995.fig2, dtype='individual')
head(ura1995.fig2)

# age [m^2], liverVolkg [ml/kg]
ura1995.fig3 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Urata1995_Fig3.csv"), sep="\t")
ura1995.fig3 <- process_data_and_save(ura1995.fig3, dtype='individual')
head(ura1995.fig3)

# BSA [m^2], liverVol [ml]
vau2002.fig1 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Vauthey2002_Fig1.csv"), sep="\t")
vau2002.fig1$volLiver <- vau2002.fig1$liverVol
vau2002.fig1 <- process_data_and_save(vau2002.fig1, dtype='individual')
head(vau2002.fig1)

# bodyweight [kg], liverVol [ml]
vau2002.fig2 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Vauthey2002_Fig2.csv"), sep="\t")
vau2002.fig2$volLiver <- vau2002.fig2$liverVol
vau2002.fig2$volLiverkg <- vau2002.fig2$volLiver/vau2002.fig2$bodyweight
vau2002.fig2 <- process_data_and_save(vau2002.fig2, dtype='individual')
head(vau2002.fig2)

# sex [male,female], age [years], weight [kg], GEC [mmol/min], bloodFlowM1 [ml/min], bloodFlowM2 [ml/min],
# flowLiver [ml/min]
win1965 <- read.csv(file.path(ma.settings$dir.expdata, "GEC", "Winkler1965.csv"), sep="\t")
win1965$flowLiverkg <- win1965$flowLiver/win1965$bodyweight
win1965$BSA <- calculateBSA(bodyweight_kg=win1965$bodyweight, height_cm=win1965$height)
win1965$GEkg <- win1965$GE/win1965$bodyweight
# win1965 <- win1965[!is.na(win1965$GE), ] # filter cases without GEC
win1965 <- process_data_and_save(win1965, dtype='individual')
head(win1965)

# gender [male, female], age [years], liver volume [ml], bloodflow, perfusion
wyn1989 <- read.csv(file.path(ma.settings$dir.expdata, "raw_data", "wynne", "Wynne1989_corrected.csv"), sep="\t")
wyn1989$volLiver <- wyn1989$livVolume
wyn1989$volLiverkg <- wyn1989$livVolumekg
wyn1989$flowLiver <- wyn1989$livBloodflow
wyn1989$flowLiverkg <- wyn1989$livBloodflowkg
wyn1989$study <- 'wyn1989'
wyn1989 <- process_data_and_save(wyn1989, dtype='individual')
head(wyn1989)

# age [years], liver bloodflow [ml/min]
wyn1990 <- read.csv(file.path(ma.settings$dir.expdata, "liver_bloodflow", "Wynne1990.csv"), sep="\t")
wyn1990$flowLiver <- wyn1990$liverBloodflow
wyn1990 <- process_data_and_save(wyn1990, dtype='individual')
head(wyn1990)

# BSA [m^2], liverWeight [g]
yos2003 <- read.csv(file.path(ma.settings$dir.expdata, "liver_volume", "Yoshizumi2003.csv"), sep="\t")
yos2003$volLiver <- yos2003$liverWeight/f_liver_density ; # [ml]
yos2003 <- process_data_and_save(yos2003, dtype='individual')
head(yos2003)

# age [years], FHF (functional hepatic flow) [ml/min]
zol1993 <- read.csv(file.path(ma.settings$dir.expdata, "liver_bloodflow", "Zoller1993.csv"), sep="\t")
zol1993$flowLiverkg <- zol1993$liverBloodflowPerBodyweight
zol1993 <- process_data_and_save(zol1993, dtype='individual')
head(zol1993)

# age [years], FHF (functional hepatic flow) [ml/min]
zol1999 <- read.csv(file.path(ma.settings$dir.expdata, "liver_bloodflow", "Zoli1999.csv"), sep="\t")
zol1999$flowLiver <- zol1999$FHF
zol1999 <- process_data_and_save(zol1999, dtype='individual')
head(zol1999)


############################################
# Correlation Functions & Settings
############################################
create_plots = T

library('reshape')
# Combine list of data.frames based on xname and yname
combine_data <- function(df.list, status='healthy'){
  selection <- c('study', 'sex', xname, yname, 'dtype', 'status')
  for (k in 1:length(df.list)){
    # reduce to selection
    df <- df.list[[k]]
    df <- df[, selection]
    # only healthy data
    if (status == 'healthy'){
      df <- df[status=='healthy',]
    }
    # remove the NA
    df <- df[complete.cases(df), ]
    # store again
    df.list[[k]] <- df
  }
  df <- reshape::merge_all(df.list)
  return(df)
}

############################################
# GEC [mmol/min] vs. age [years]
############################################
xname <- 'age'; yname <- 'GEC'
data <- combine_data(list(
  mar1988, 
  tyg1963, 
  sch1986.tab1, 
  duc1979, 
  duf1992
))
save_correlation_data(data)

m1 <- linear_regression(data, xname, yname)
plot_correlation_data(data, m1, xname, yname, create_plots=create_plots)

############################################
# GECkg [mmol/min/kgbw] vs. age [years]
############################################
xname <- 'age'; yname <- 'GECkg'
data <- combine_data(list(
  lan2011,
  duc1979,
  tyg1963,
  sch1986.fig1, 
  # sch1986.tab1, # already part of dataset via sch1986.fig1
  duf1992
  ))
save_correlation_data(data)

m1 <- linear_regression(data, xname, yname)
plot_correlation_data(data, m1, xname, yname, create_plots=create_plots)

############################################
# GEC [mmol/min] vs. volLiver [ml]
############################################
xname <- 'volLiver'; yname <- 'GEC'
data <- combine_data(list(
  mar1988
))
save_correlation_data(data)

m1 <- linear_regression(data, xname, yname)
plot_correlation_data(data, m1, xname, yname, create_plots=create_plots)

############################################
# GEC [mmol/min] vs. flowLiver [ml/min]
############################################
xname <- 'flowLiver'; yname <- 'GEC'
data <- combine_data(list(
  win1965  # outlier compare to other datasets
))
save_correlation_data(data)

m1 <- linear_regression(data, xname, yname)
plot_correlation_data(data, m1, xname, yname, create_plots=create_plots)

############################################
# volLiver [ml] vs. age [years]
############################################
xname <- 'age'; yname <- 'volLiver'
data <- combine_data(list(
  mar1988,
  wyn1989,
  naw1998,
  boy1933,
  hei1999
))
# data <- addRandomizedPopulationData(data, alt1962) # no range/Sd for volLiver
# data <- addRandomizedPopulationData(data, tom1965)
# data <- addRandomizedPopulationData(data, kay1987)
save_correlation_data(data)
plot_correlation_data(data, NULL, xname, yname, create_plots=create_plots)

# points(hei1999[[xname]], hei1999[[yname]], col='black', bg='black', pch=21, cex=1.5)
# points(wyn1989[[xname]], wyn1989[[yname]], col='black', bg='black', pch=21, cex=1.5)
# points(naw1998[[xname]], naw1998[[yname]], col='black', bg='black', pch=21, cex=1.5)
#points(mar1988[[xname]], mar1988[[yname]], col='black', bg='black', pch=21, cex=1.5)
#addPopulationSegments(tom1965, xname, yname)
#addPopulationSegments(kay1987, xname, yname)

############################################
# volLiverkg [ml/kg] vs. age [years]
############################################
xname <- 'age'; yname <- 'volLiverkg'
data <- combine_data(list(
  wyn1989,
  naw1998,
  ura1995.fig3,
  hei1999
))
save_correlation_data(data)
plot_correlation_data(data, NULL, xname, yname, create_plots=create_plots)
# points(ura1995.fig3[[xname]], ura1995.fig3[[yname]], col='black', bg='black', pch=21, cex=1.5)
# points(wyn1989[[xname]], wyn1989[[yname]], col='black', bg='black', pch=21, cex=1.5)

############################################
# volLiver [ml] vs. BSA [m^2]
############################################
xname <- 'BSA'; yname <- 'volLiver'
data <- combine_data(list(
  naw1998,
  hei1999,
  ura1995.fig2,
  vau2002.fig1,
  yos2003
))

# data <- addRandomizedPopulationData(data, del1968.fig4)
save_correlation_data(data)
plot_correlation_data(data, NULL, xname, yname, create_plots=create_plots)
# points(ura1995.fig2[[xname]], ura1995.fig2[[yname]], col='black', bg='black', pch=21, cex=1.5)
# addPopulationSegments(del1968.fig4, xname, yname)

############################################
# volLiverkg [ml/kg] vs. BSA [m^2]
############################################
xname <- 'BSA'; yname <- 'volLiverkg'
data <- combine_data(list(
  naw1998,
  hei1999
))
save_correlation_data(data)
plot_correlation_data(data, NULL, xname, yname, create_plots=create_plots)

############################################
# volLiver [ml] vs. bodyweight [kg]
############################################
xname <- 'bodyweight'; yname <- 'volLiver'
data <- combine_data(list(
  naw1998,
  vau2002.fig2,
  wyn1989,
  hei1999
))
# data <- addRandomizedPopulationData(data, del1968.fig1)
# data <- addRandomizedPopulationData(data, tom1965)
save_correlation_data(data)
plot_correlation_data(data, NULL, xname, yname, create_plots=create_plots)
addPopulationSegments(del1968.fig1, xname, yname)
addPopulationSegments(tom1965, xname, yname)

############################################
# volLiverkg [ml/kg] vs. bodyweight [kg]
############################################
xname <- 'bodyweight'; yname <- 'volLiverkg'
data <- combine_data(list(
  naw1998,
  vau2002.fig2,
  wyn1989,
  hei1999
))
save_correlation_data(data)
plot_correlation_data(data, NULL, xname, yname, create_plots=create_plots)

############################################
# volLiver [ml] vs. height [cm]
############################################
xname <- 'height'; yname <- 'volLiver'
data <- combine_data(list(
  naw1998,
  hei1999
))
# data <- addRandomizedPopulationData(data, del1968.fig3)
# data <- addRandomizedPopulationData(data, gra2000.tab1)
save_correlation_data(data)
plot_correlation_data(data, NULL, xname, yname, create_plots=create_plots)
addPopulationSegments(del1968.fig3, xname, yname)
addPopulationSegments(gra2000.tab1, xname, yname)

############################################
# volLiverkg [ml/kg] vs. height [cm]
############################################
xname <- 'height'; yname <- 'volLiverkg'
data <- combine_data(list(
  naw1998,
  hei1999
))
save_correlation_data(data)
plot_correlation_data(data, NULL, xname, yname, create_plots=create_plots)

############################################
# flowLiver [ml/min] vs. age [years]
############################################
xname <- 'age'; yname <- 'flowLiver'
data <- combine_data(list(
  win1965, 
  wyn1989,
  bra1945,
  bra1952,
  zol1999,
  she1950,
  wyn1990,
  tyg1958,
  cat2010,     # estimate via cardiac output
  ircp2001.co  # estimate via cardiac output
))
save_correlation_data(data)
plot_correlation_data(data, NULL, xname, yname, create_plots=create_plots)
# points(lee1962[[xname]], lee1962[[yname]], col='black', bg='black', pch=21, cex=1.5)

############################################
# flowLiverkg [ml/min/kg] vs. age [years]
############################################
xname <- 'age'; yname <- 'flowLiverkg'
data <- combine_data(list(
  win1965, 
  wyn1989,
  she1950,
  zol1993,
  tyg1958,
  cat2010  # estimate via cardiac output
))
save_correlation_data(data)
# m1 <- linear_regression(data, xname, yname)
plot_correlation_data(data, NULL, xname, yname, create_plots=create_plots)
#points(tyg1958$age, tyg1958$flowLiverkg, col='black', bg='black', pch=21, cex=1.5)

############################################
# flowLiver [ml/min] vs. bodyweight [kg]
############################################
xname <- 'bodyweight'; yname <- 'flowLiver'
data <- combine_data(list(
  wyn1989,
  tyg1958,
  she1950,
  sim1997   # estimate via cardiac output
  # cat2010 # estimate via cardiac output
))
save_correlation_data(data)
m1 <- linear_regression(data, xname, yname)
plot_correlation_data(data, m1, xname, yname, create_plots=create_plots)
# points(sim1997[[xname]], sim1997[[yname]], col='black', bg='black', pch=21, cex=1.5)
# points(cat2010[[xname]], cat2010[[yname]], col='black', bg='black', pch=21, cex=0.8)


############################################
# flowLiverkg [ml/min] vs. bodyweight [kg]
############################################
xname <- 'bodyweight'; yname <- 'flowLiverkg'
data <- combine_data(list(
  wyn1989,
  tyg1958,
  she1950,
  sim1997, # estimate via cardiac output
  cat2010  # estimate via cardiac output
))
save_correlation_data(data)

# m1 <- linear_regression(data, xname, yname)
plot_correlation_data(data, m1=NULL, xname, yname, create_plots=create_plots)
#points(she1950[[xname]], she1950[[yname]], col='black', bg='black', pch=21, cex=1.5)


############################################
# flowLiver [ml/min] vs. BSA [m^2]
############################################
xname <- 'BSA'; yname <- 'flowLiver'
data <- combine_data(list(
  bra1945,
  bra1952,
  she1950,
  tyg1958,
  cat2010  # estimate via cardiac output
))
save_correlation_data(data)

m1 <- linear_regression(data, xname, yname)
plot_correlation_data(data, m1, xname, yname, create_plots=create_plots)
# points(cat2010[[xname]], cat2010[[yname]], col='black', bg='black', pch=21, cex=1.5)

############################################
# flowLiverkg [ml/min/kg] vs. BSA [m^2]
############################################
xname <- 'BSA'; yname <- 'flowLiverkg'
data <- combine_data(list(
  she1950,
  tyg1958,
  cat2010 # estimate via cardiac output
))
save_correlation_data(data)
# m1 <- linear_regression(data, xname, yname)
plot_correlation_data(data, NULL, xname, yname, create_plots=create_plots)

############################################
# flowLiver [ml/min] vs. volLiver [ml]
############################################
xname <- 'volLiver'; yname <- 'flowLiver'
data <- combine_data(list(
  wyn1989
))
save_correlation_data(data)

m1 <- linear_regression(data, xname, yname)
plot_correlation_data(data, m1, xname, yname, create_plots=create_plots)

############################################
# flowLiverkg [ml/min/kg] vs. volLiverkg [ml/kg]
############################################
xname <- 'volLiverkg'; yname <- 'flowLiverkg'
data <- combine_data(list(
  wyn1989
))
save_correlation_data(data)

m1 <- linear_regression(data, xname, yname)
plot_correlation_data(data, m1, xname, yname, create_plots=create_plots)

############################################
# perfusion [ml/min/ml] vs. age [years]
############################################
xname <- 'age'; yname <- 'perfusion'
data <- combine_data(list(
  wyn1989
))
save_correlation_data(data)

m1 <- linear_regression(data, xname, yname)
plot_correlation_data(data, m1, xname, yname, create_plots=create_plots)
