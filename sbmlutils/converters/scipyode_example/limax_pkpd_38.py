x = [
     + 1.0*(Qlu * (Clu_apap / Kplu_apap) * BP_apap) - 1.0*(Qre * Car_apap) - 1.0*(Qbo * Car_apap) - 1.0*(Qgu * Car_apap) - 1.0*(Qhe * Car_apap) - 1.0*(Qki * Car_apap) - 1.0*(Qsp * Car_apap) - 1.0*(Qha * Car_apap),		# Aar_apap
     + 1.0*(Qlu * (Clu_co2c13 / Kplu_co2c13) * BP_co2c13) - 1.0*(Qre * Car_co2c13) - 1.0*(Qbo * Car_co2c13) - 1.0*(Qgu * Car_co2c13) - 1.0*(Qhe * Car_co2c13) - 1.0*(Qki * Car_co2c13) - 1.0*(Qsp * Car_co2c13) - 1.0*(Qha * Car_co2c13),		# Aar_co2c13
     + 1.0*(Qlu * (Clu_metc13 / Kplu_metc13) * BP_metc13) - 1.0*(Qre * Car_metc13) - 1.0*(Qbo * Car_metc13) - 1.0*(Qgu * Car_metc13) - 1.0*(Qhe * Car_metc13) - 1.0*(Qki * Car_metc13) - 1.0*(Qsp * Car_metc13) - 1.0*(Qha * Car_metc13),		# Aar_metc13
     + 1.0*(Qbo * Car_apap) - 1.0*(Qbo * (Cbo_apap / Kpbo_apap) * BP_apap),		# Abo_apap
     + 1.0*(Qbo * Car_co2c13) - 1.0*(Qbo * (Cbo_co2c13 / Kpbo_co2c13) * BP_co2c13),		# Abo_co2c13
     + 1.0*(KBO_FIXCO2 * 60 * Cve_co2c13 * Vve * (1 - Cbo_co2c13_fix / KBO_MAXCO2)) - 1.0*(KBO_RELCO2 * 60 * Cbo_co2c13_fix * Vve),		# Abo_co2c13_fix
     + 1.0*(Qbo * Car_metc13) - 1.0*(Qbo * (Cbo_metc13 / Kpbo_metc13) * BP_metc13),		# Abo_metc13
     + 1.0*(KLU_EXCO2 * 60 * Clu_co2c13 * Vlu),		# Abreath_co2c13
     + 1.0*((Ka_apap * D_apap / Mr_apap) * F_apap) + 1.0*(Qgu * Car_apap) - 1.0*(Qgu * (Cgu_apap / Kpgu_apap) * BP_apap),		# Agu_apap
     + 1.0*((Ka_co2c13 * D_co2c13 / Mr_co2c13) * F_co2c13) + 1.0*(Qgu * Car_co2c13) - 1.0*(Qgu * (Cgu_co2c13 / Kpgu_co2c13) * BP_co2c13),		# Agu_co2c13
     + 1.0*((Ka_metc13 * D_metc13 / Mr_metc13) * F_metc13) + 1.0*(Qgu * Car_metc13) - 1.0*(Qgu * (Cgu_metc13 / Kpgu_metc13) * BP_metc13),		# Agu_metc13
     + 1.0*(Qhe * Car_apap) - 1.0*(Qhe * (Che_apap / Kphe_apap) * BP_apap),		# Ahe_apap
     + 1.0*(Qhe * Car_co2c13) - 1.0*(Qhe * (Che_co2c13 / Kphe_co2c13) * BP_co2c13),		# Ahe_co2c13
     + 1.0*(Qhe * Car_metc13) - 1.0*(Qhe * (Che_metc13 / Kphe_metc13) * BP_metc13),		# Ahe_metc13
     - 1.0*(CLrenal_apap * Cki_free_apap) + 1.0*(Qki * Car_apap) - 1.0*(Qki * (Cki_apap / Kpki_apap) * BP_apap),		# Aki_apap
     - 1.0*(CLrenal_co2c13 * Cki_free_co2c13) + 1.0*(Qki * Car_co2c13) - 1.0*(Qki * (Cki_co2c13 / Kpki_co2c13) * BP_co2c13),		# Aki_co2c13
     - 1.0*(CLrenal_metc13 * Cki_free_metc13) + 1.0*(Qki * Car_metc13) - 1.0*(Qki * (Cki_metc13 / Kpki_metc13) * BP_metc13),		# Aki_metc13
     + 1.0*(CYP1A2MET_CLliv * 1 * (Cli_free_metc13 / (Cli_free_metc13 + CYP1A2MET_Km_met))) - 1.0*(APAPD_CLliv * 1 * (Cli_free_apap / (Cli_free_apap + APAPD_Km_apap))) + 1.0*(Qgu * (Cgu_apap / Kpgu_apap) * BP_apap) + 1.0*(Qsp * (Csp_apap / Kpsp_apap) * BP_apap) + 1.0*(Qha * Car_apap) - 1.0*(Qh * (Cli_apap / Kpli_apap) * BP_apap),		# Ali_apap
     + 1.0*(CYP1A2MET_CLliv * 1 * (Cli_free_metc13 / (Cli_free_metc13 + CYP1A2MET_Km_met))) - 1.0*(CO2FIX_CLliv * 1 * (Cli_co2c13 / (Cli_co2c13 + CO2FIX_Km_co2))) + 1.0*(Qgu * (Cgu_co2c13 / Kpgu_co2c13) * BP_co2c13) + 1.0*(Qsp * (Csp_co2c13 / Kpsp_co2c13) * BP_co2c13) + 1.0*(Qha * Car_co2c13) - 1.0*(Qh * (Cli_co2c13 / Kpli_co2c13) * BP_co2c13),		# Ali_co2c13
     - 1.0*(CYP1A2MET_CLliv * 1 * (Cli_free_metc13 / (Cli_free_metc13 + CYP1A2MET_Km_met))) + 1.0*(Qgu * (Cgu_metc13 / Kpgu_metc13) * BP_metc13) + 1.0*(Qsp * (Csp_metc13 / Kpsp_metc13) * BP_metc13) + 1.0*(Qha * Car_metc13) - 1.0*(Qh * (Cli_metc13 / Kpli_metc13) * BP_metc13),		# Ali_metc13
     + 1.0*(Qlu * Cve_apap) - 1.0*(Qlu * (Clu_apap / Kplu_apap) * BP_apap),		# Alu_apap
     - 1.0*(KLU_EXCO2 * 60 * Clu_co2c13 * Vlu) + 1.0*(Qlu * Cve_co2c13) - 1.0*(Qlu * (Clu_co2c13 / Kplu_co2c13) * BP_co2c13),		# Alu_co2c13
     + 1.0*(Qlu * Cve_metc13) - 1.0*(Qlu * (Clu_metc13 / Kplu_metc13) * BP_metc13),		# Alu_metc13
     + 1.0*(Qre * Car_apap) - 1.0*(Qre * (Cre_apap / Kpre_apap) * BP_apap),		# Are_apap
     + 1.0*(Qre * Car_co2c13) - 1.0*(Qre * (Cre_co2c13 / Kpre_co2c13) * BP_co2c13),		# Are_co2c13
     + 1.0*(Qre * Car_metc13) - 1.0*(Qre * (Cre_metc13 / Kpre_metc13) * BP_metc13),		# Are_metc13
     + 1.0*(Qsp * Car_apap) - 1.0*(Qsp * (Csp_apap / Kpsp_apap) * BP_apap),		# Asp_apap
     + 1.0*(Qsp * Car_co2c13) - 1.0*(Qsp * (Csp_co2c13 / Kpsp_co2c13) * BP_co2c13),		# Asp_co2c13
     + 1.0*(Qsp * Car_metc13) - 1.0*(Qsp * (Csp_metc13 / Kpsp_metc13) * BP_metc13),		# Asp_metc13
     + 1.0*(CLrenal_apap * Cki_free_apap),		# Aurine_apap
     + 1.0*(CLrenal_co2c13 * Cki_free_co2c13),		# Aurine_co2c13
     + 1.0*(CLrenal_metc13 * Cki_free_metc13),		# Aurine_metc13
     + 1.0*(Ki_apap * DIV_apap / Mr_apap) + 1.0*((Ri_apap / Mr_apap) * 60) - 1.0*(Qlu * Cve_apap) + 1.0*(Qre * (Cre_apap / Kpre_apap) * BP_apap) + 1.0*(Qbo * (Cbo_apap / Kpbo_apap) * BP_apap) + 1.0*(Qhe * (Che_apap / Kphe_apap) * BP_apap) + 1.0*(Qki * (Cki_apap / Kpki_apap) * BP_apap) + 1.0*(Qh * (Cli_apap / Kpli_apap) * BP_apap),		# Ave_apap
     - 1.0*(KBO_FIXCO2 * 60 * Cve_co2c13 * Vve * (1 - Cbo_co2c13_fix / KBO_MAXCO2)) + 1.0*(KBO_RELCO2 * 60 * Cbo_co2c13_fix * Vve) + 1.0*(Ki_co2c13 * DIV_co2c13 / Mr_co2c13) + 1.0*((Ri_co2c13 / Mr_co2c13) * 60) - 1.0*(Qlu * Cve_co2c13) + 1.0*(Qre * (Cre_co2c13 / Kpre_co2c13) * BP_co2c13) + 1.0*(Qbo * (Cbo_co2c13 / Kpbo_co2c13) * BP_co2c13) + 1.0*(Qhe * (Che_co2c13 / Kphe_co2c13) * BP_co2c13) + 1.0*(Qki * (Cki_co2c13 / Kpki_co2c13) * BP_co2c13) + 1.0*(Qh * (Cli_co2c13 / Kpli_co2c13) * BP_co2c13),		# Ave_co2c13
     + 1.0*(Ki_metc13 * DIV_metc13 / Mr_metc13) + 1.0*((Ri_metc13 / Mr_metc13) * 60) - 1.0*(Qlu * Cve_metc13) + 1.0*(Qre * (Cre_metc13 / Kpre_metc13) * BP_metc13) + 1.0*(Qbo * (Cbo_metc13 / Kpbo_metc13) * BP_metc13) + 1.0*(Qhe * (Che_metc13 / Kphe_metc13) * BP_metc13) + 1.0*(Qki * (Cki_metc13 / Kpki_metc13) * BP_metc13) + 1.0*(Qh * (Cli_metc13 / Kpli_metc13) * BP_metc13),		# Ave_metc13
    -Injection_apap * Mr_apap,		# DIV_apap
    -Injection_co2c13 * Mr_co2c13,		# DIV_co2c13
    -Injection_metc13 * Mr_metc13,		# DIV_metc13
    -Absorption_apap * Mr_apap,		# D_apap
    -Absorption_co2c13 * Mr_co2c13,		# D_co2c13
    -Absorption_metc13 * Mr_metc13,		# D_metc13
    Ri_apap * 60,		# cum_dose_apap
    Ri_co2c13 * 60,		# cum_dose_co2c13
    Ri_metc13 * 60,		# cum_dose_metc13
]

r = [
    APAPD_CLliv * 1 * (Cli_free_apap / (Cli_free_apap + APAPD_Km_apap)),		# APAPD
    (Ka_apap * D_apap / Mr_apap) * F_apap,		# Absorption_apap
    (Ka_co2c13 * D_co2c13 / Mr_co2c13) * F_co2c13,		# Absorption_co2c13
    (Ka_metc13 * D_metc13 / Mr_metc13) * F_metc13,		# Absorption_metc13
    CO2FIX_CLliv * 1 * (Cli_co2c13 / (Cli_co2c13 + CO2FIX_Km_co2)),		# CO2FIX
    CYP1A2MET_CLliv * 1 * (Cli_free_metc13 / (Cli_free_metc13 + CYP1A2MET_Km_met)),		# CYP1A2MET
    KLU_EXCO2 * 60 * Clu_co2c13 * Vlu,		# Exhalation_co2c13
    KBO_FIXCO2 * 60 * Cve_co2c13 * Vve * (1 - Cbo_co2c13_fix / KBO_MAXCO2),		# Fixation_co2c13
    (Ri_apap / Mr_apap) * 60,		# Infusion_apap
    (Ri_co2c13 / Mr_co2c13) * 60,		# Infusion_co2c13
    (Ri_metc13 / Mr_metc13) * 60,		# Infusion_metc13
    Ki_apap * DIV_apap / Mr_apap,		# Injection_apap
    Ki_co2c13 * DIV_co2c13 / Mr_co2c13,		# Injection_co2c13
    Ki_metc13 * DIV_metc13 / Mr_metc13,		# Injection_metc13
    KBO_RELCO2 * 60 * Cbo_co2c13_fix * Vve,		# Release_co2c13
    Qbo * Car_apap,		# ar_bo_apap
    Qbo * Car_co2c13,		# ar_bo_co2c13
    Qbo * Car_metc13,		# ar_bo_metc13
    Qgu * Car_apap,		# ar_gu_apap
    Qgu * Car_co2c13,		# ar_gu_co2c13
    Qgu * Car_metc13,		# ar_gu_metc13
    Qhe * Car_apap,		# ar_he_apap
    Qhe * Car_co2c13,		# ar_he_co2c13
    Qhe * Car_metc13,		# ar_he_metc13
    Qki * Car_apap,		# ar_ki_apap
    Qki * Car_co2c13,		# ar_ki_co2c13
    Qki * Car_metc13,		# ar_ki_metc13
    Qha * Car_apap,		# ar_li_apap
    Qha * Car_co2c13,		# ar_li_co2c13
    Qha * Car_metc13,		# ar_li_metc13
    Qre * Car_apap,		# ar_re_apap
    Qre * Car_co2c13,		# ar_re_co2c13
    Qre * Car_metc13,		# ar_re_metc13
    Qsp * Car_apap,		# ar_sp_apap
    Qsp * Car_co2c13,		# ar_sp_co2c13
    Qsp * Car_metc13,		# ar_sp_metc13
    Qbo * (Cbo_apap / Kpbo_apap) * BP_apap,		# bo_ve_apap
    Qbo * (Cbo_co2c13 / Kpbo_co2c13) * BP_co2c13,		# bo_ve_co2c13
    Qbo * (Cbo_metc13 / Kpbo_metc13) * BP_metc13,		# bo_ve_metc13
    Qgu * (Cgu_apap / Kpgu_apap) * BP_apap,		# gu_li_apap
    Qgu * (Cgu_co2c13 / Kpgu_co2c13) * BP_co2c13,		# gu_li_co2c13
    Qgu * (Cgu_metc13 / Kpgu_metc13) * BP_metc13,		# gu_li_metc13
    Qhe * (Che_apap / Kphe_apap) * BP_apap,		# he_ve_apap
    Qhe * (Che_co2c13 / Kphe_co2c13) * BP_co2c13,		# he_ve_co2c13
    Qhe * (Che_metc13 / Kphe_metc13) * BP_metc13,		# he_ve_metc13
    Qki * (Cki_apap / Kpki_apap) * BP_apap,		# ki_ve_apap
    Qki * (Cki_co2c13 / Kpki_co2c13) * BP_co2c13,		# ki_ve_co2c13
    Qki * (Cki_metc13 / Kpki_metc13) * BP_metc13,		# ki_ve_metc13
    Qh * (Cli_apap / Kpli_apap) * BP_apap,		# li_ve_apap
    Qh * (Cli_co2c13 / Kpli_co2c13) * BP_co2c13,		# li_ve_co2c13
    Qh * (Cli_metc13 / Kpli_metc13) * BP_metc13,		# li_ve_metc13
    Qlu * (Clu_apap / Kplu_apap) * BP_apap,		# lu_ar_apap
    Qlu * (Clu_co2c13 / Kplu_co2c13) * BP_co2c13,		# lu_ar_co2c13
    Qlu * (Clu_metc13 / Kplu_metc13) * BP_metc13,		# lu_ar_metc13
    Qre * (Cre_apap / Kpre_apap) * BP_apap,		# re_ve_apap
    Qre * (Cre_co2c13 / Kpre_co2c13) * BP_co2c13,		# re_ve_co2c13
    Qre * (Cre_metc13 / Kpre_metc13) * BP_metc13,		# re_ve_metc13
    Qsp * (Csp_apap / Kpsp_apap) * BP_apap,		# sp_li_apap
    Qsp * (Csp_co2c13 / Kpsp_co2c13) * BP_co2c13,		# sp_li_co2c13
    Qsp * (Csp_metc13 / Kpsp_metc13) * BP_metc13,		# sp_li_metc13
    Qlu * Cve_apap,		# ve_lu_apap
    Qlu * Cve_co2c13,		# ve_lu_co2c13
    Qlu * Cve_metc13,		# ve_lu_metc13
    CLrenal_apap * Cki_free_apap,		# vre_apap
    CLrenal_co2c13 * Cki_free_co2c13,		# vre_co2c13
    CLrenal_metc13 * Cki_free_metc13,		# vre_metc13
]

p = [
    2.5,		# APAPD_HLM_CL
    0.5,		# APAPD_Km_apap
    1.0,		# BP_apap
    1.0,		# BP_co2c13
    1.0,		# BP_metc13
    75.0,		# BW
    0.714,		# CLrenal_apap
    0.0,		# CLrenal_co2c13
    10.0,		# CLrenal_metc13
    1.5,		# CO2FIX_HLM_CL
    0.2,		# CO2FIX_Km_co2
    1.548,		# COBW
    150.0,		# COHRI
    1.5,		# CYP1A2MET_CL
    0.02,		# CYP1A2MET_Km_met
    0.05,		# FQbo
    0.146,		# FQgu
    0.215,		# FQh
    0.04,		# FQhe
    0.19,		# FQki
    1.0,		# FQlu
    0.017,		# FQsp
    0.0257,		# FVar
    0.0856,		# FVbo
    0.0171,		# FVgu
    0.0047,		# FVhe
    0.0044,		# FVki
    0.021,		# FVli
    0.0076,		# FVlu
    0.0424,		# FVpl
    0.0026,		# FVsp
    0.0514,		# FVve
    0.85,		# F_PAR
    0.87,		# F_apap
    1.0,		# F_co2c13
    1.0,		# F_metc13
    170.0,		# HEIGHT
    70.0,		# HR
    70.0,		# HRrest
    0.0,		# IVDOSE_apap
    0.0,		# IVDOSE_co2c13
    0.0,		# IVDOSE_metc13
    0.1,		# KBO_FIXCO2
    0.2,		# KBO_MAXCO2
    0.0001,		# KBO_RELCO2
    1.2,		# KLU_EXCO2
    2.5,		# Ka_apap
    8.0,		# Ka_co2c13
    4.0,		# Ka_metc13
    1.0,		# Kpbo_apap
    1.0,		# Kpbo_co2c13
    1.0,		# Kpbo_metc13
    1.0,		# Kpgu_apap
    1.0,		# Kpgu_co2c13
    1.0,		# Kpgu_metc13
    1.0,		# Kphe_apap
    1.0,		# Kphe_co2c13
    1.0,		# Kphe_metc13
    1.0,		# Kpki_apap
    1.0,		# Kpki_co2c13
    1.0,		# Kpki_metc13
    1.0,		# Kpli_apap
    1.0,		# Kpli_co2c13
    1.0,		# Kpli_metc13
    1.0,		# Kplu_apap
    1.0,		# Kplu_co2c13
    1.0,		# Kplu_metc13
    0.8,		# Kpre_apap
    1.0,		# Kpre_co2c13
    0.2,		# Kpre_metc13
    1.0,		# Kpsp_apap
    1.0,		# Kpsp_co2c13
    1.0,		# Kpsp_metc13
    45.0,		# MPPGL
    151.16,		# Mr_apap
    62.02,		# Mr_co2c13
    165.19,		# Mr_metc13
    0.0,		# PODOSE_apap
    0.0,		# PODOSE_co2c13
    0.0,		# PODOSE_metc13
    300.0,		# P_CO2BSA
    0.01123,		# R_PDB
    0.0,		# Ri_apap
    0.0,		# Ri_co2c13
    0.0,		# Ri_metc13
    1.0,		# fumic_apap
    1.0,		# fumic_co2c13
    1.0,		# fumic_metc13
    1.0,		# fup_apap
    1.0,		# fup_co2c13
    1.0,		# fup_metc13
    10.0,		# ti_apap
    10.0,		# ti_co2c13
    10.0,		# ti_metc13
]

y = [
    0.024265 * (BW / 1)**0.5378 * (HEIGHT / 1)**0.3964,		# BSA
    BW * COBW + (HR - HRrest) * COHRI / 60,		# CO
    1 - (FQbo + FQhe + FQgu + FQki + FQh + FQsp),		# FQre
    1 - (FVbo + FVhe + FVgu + FVki + FVli + FVlu + FVsp + FVve + FVar + FVpl),		# FVre
    (1.386 / ti_apap) * 3600,		# Ki_apap
    (1.386 / ti_co2c13) * 3600,		# Ki_co2c13
    (1.386 / ti_metc13) * 3600,		# Ki_metc13
    BW * FVar,		# Var
    BW * FVbo,		# Vbo
    BW * FVgu,		# Vgu
    BW * FVhe,		# Vhe
    BW * FVki,		# Vki
    BW * FVli,		# Vli
    BW * FVlu,		# Vlu
    BW * FVpl,		# Vpl
    BW * FVsp,		# Vsp
    BW * FVve,		# Vve
    Aar_apap * Mr_apap,		# Xar_apap
    Aar_co2c13 * Mr_co2c13,		# Xar_co2c13
    Aar_metc13 * Mr_metc13,		# Xar_metc13
    Abo_apap * Mr_apap,		# Xbo_apap
    Abo_co2c13 * Mr_co2c13,		# Xbo_co2c13
    Abo_co2c13_fix * Mr_co2c13,		# Xbo_co2c13_fix
    Abo_metc13 * Mr_metc13,		# Xbo_metc13
    Abreath_co2c13 * Mr_co2c13,		# Xbreath_co2c13
    Agu_apap * Mr_apap,		# Xgu_apap
    Agu_co2c13 * Mr_co2c13,		# Xgu_co2c13
    Agu_metc13 * Mr_metc13,		# Xgu_metc13
    Ahe_apap * Mr_apap,		# Xhe_apap
    Ahe_co2c13 * Mr_co2c13,		# Xhe_co2c13
    Ahe_metc13 * Mr_metc13,		# Xhe_metc13
    Aki_apap * Mr_apap,		# Xki_apap
    Aki_co2c13 * Mr_co2c13,		# Xki_co2c13
    Aki_metc13 * Mr_metc13,		# Xki_metc13
    Ali_apap * Mr_apap,		# Xli_apap
    Ali_co2c13 * Mr_co2c13,		# Xli_co2c13
    Ali_metc13 * Mr_metc13,		# Xli_metc13
    Alu_apap * Mr_apap,		# Xlu_apap
    Alu_co2c13 * Mr_co2c13,		# Xlu_co2c13
    Alu_metc13 * Mr_metc13,		# Xlu_metc13
    Are_apap * Mr_apap,		# Xre_apap
    Are_co2c13 * Mr_co2c13,		# Xre_co2c13
    Are_metc13 * Mr_metc13,		# Xre_metc13
    Asp_apap * Mr_apap,		# Xsp_apap
    Asp_co2c13 * Mr_co2c13,		# Xsp_co2c13
    Asp_metc13 * Mr_metc13,		# Xsp_metc13
    Aurine_apap * Mr_apap,		# Xurine_apap
    Aurine_co2c13 * Mr_co2c13,		# Xurine_co2c13
    Aurine_metc13 * Mr_metc13,		# Xurine_metc13
    Ave_apap * Mr_apap,		# Xve_apap
    Ave_co2c13 * Mr_co2c13,		# Xve_co2c13
    Ave_metc13 * Mr_metc13,		# Xve_metc13
    (APAPD_HLM_CL / fumic_apap) * MPPGL * Vli * F_PAR * 60 / 1000,		# APAPD_CLliv
    CO2FIX_HLM_CL * MPPGL * Vli * F_PAR * 60 / 1000,		# CO2FIX_CLliv
    (CYP1A2MET_CL / fumic_metc13) * MPPGL * Vli * F_PAR * 60 / 1000,		# CYP1A2MET_CLliv
    Aar_apap / Var,		# Car_apap
    Aar_co2c13 / Var,		# Car_co2c13
    Aar_metc13 / Var,		# Car_metc13
    Abo_apap / Vbo,		# Cbo_apap
    Abo_co2c13 / Vbo,		# Cbo_co2c13
    Abo_co2c13_fix / Vbo,		# Cbo_co2c13_fix
    Abo_metc13 / Vbo,		# Cbo_metc13
    Agu_apap / Vgu,		# Cgu_apap
    Agu_co2c13 / Vgu,		# Cgu_co2c13
    Agu_metc13 / Vgu,		# Cgu_metc13
    Ahe_apap / Vhe,		# Che_apap
    Ahe_co2c13 / Vhe,		# Che_co2c13
    Ahe_metc13 / Vhe,		# Che_metc13
    Aki_apap / Vki,		# Cki_apap
    Aki_co2c13 / Vki,		# Cki_co2c13
    Aki_metc13 / Vki,		# Cki_metc13
    Ali_apap / Vli,		# Cli_apap
    Ali_co2c13 / Vli,		# Cli_co2c13
    Ali_metc13 / Vli,		# Cli_metc13
    Alu_apap / Vlu,		# Clu_apap
    Alu_co2c13 / Vlu,		# Clu_co2c13
    Alu_metc13 / Vlu,		# Clu_metc13
    Asp_apap / Vsp,		# Csp_apap
    Asp_co2c13 / Vsp,		# Csp_co2c13
    Asp_metc13 / Vsp,		# Csp_metc13
    Ave_apap / Vve,		# Cve_apap
    Ave_co2c13 / Vve,		# Cve_co2c13
    Ave_metc13 / Vve,		# Cve_metc13
    (Aar_apap / Var) * Mr_apap,		# Mar_apap
    (Aar_co2c13 / Var) * Mr_co2c13,		# Mar_co2c13
    (Aar_metc13 / Var) * Mr_metc13,		# Mar_metc13
    (Abo_apap / Vbo) * Mr_apap,		# Mbo_apap
    (Abo_co2c13 / Vbo) * Mr_co2c13,		# Mbo_co2c13
    (Abo_metc13 / Vbo) * Mr_metc13,		# Mbo_metc13
    (Agu_apap / Vgu) * Mr_apap,		# Mgu_apap
    (Agu_co2c13 / Vgu) * Mr_co2c13,		# Mgu_co2c13
    (Agu_metc13 / Vgu) * Mr_metc13,		# Mgu_metc13
    (Ahe_apap / Vhe) * Mr_apap,		# Mhe_apap
    (Ahe_co2c13 / Vhe) * Mr_co2c13,		# Mhe_co2c13
    (Ahe_metc13 / Vhe) * Mr_metc13,		# Mhe_metc13
    (Aki_apap / Vki) * Mr_apap,		# Mki_apap
    (Aki_co2c13 / Vki) * Mr_co2c13,		# Mki_co2c13
    (Aki_metc13 / Vki) * Mr_metc13,		# Mki_metc13
    (Ali_apap / Vli) * Mr_apap,		# Mli_apap
    (Ali_co2c13 / Vli) * Mr_co2c13,		# Mli_co2c13
    (Ali_metc13 / Vli) * Mr_metc13,		# Mli_metc13
    (Alu_apap / Vlu) * Mr_apap,		# Mlu_apap
    (Alu_co2c13 / Vlu) * Mr_co2c13,		# Mlu_co2c13
    (Alu_metc13 / Vlu) * Mr_metc13,		# Mlu_metc13
    (Asp_apap / Vsp) * Mr_apap,		# Msp_apap
    (Asp_co2c13 / Vsp) * Mr_co2c13,		# Msp_co2c13
    (Asp_metc13 / Vsp) * Mr_metc13,		# Msp_metc13
    (Ave_apap / Vve) * Mr_apap,		# Mve_apap
    (Ave_co2c13 / Vve) * Mr_co2c13,		# Mve_co2c13
    (Ave_metc13 / Vve) * Mr_metc13,		# Mve_metc13
    BSA * P_CO2BSA / 60,		# P_CO2
    (CO / 1000) * 3600,		# QC
    Vpl * Var / (Vve + Var),		# Vplas_art
    Vpl * Vve / (Vve + Var),		# Vplas_ven
    BW * FVre,		# Vre
    Xar_apap + Xbo_apap + Xhe_apap + Xgu_apap + Xki_apap + Xli_apap + Xlu_apap + Xsp_apap + Xre_apap + Xve_apap,		# Xbody_apap
    Xar_co2c13 + Xbo_co2c13 + Xhe_co2c13 + Xgu_co2c13 + Xki_co2c13 + Xli_co2c13 + Xlu_co2c13 + Xsp_co2c13 + Xre_co2c13 + Xve_co2c13,		# Xbody_co2c13
    Xar_metc13 + Xbo_metc13 + Xhe_metc13 + Xgu_metc13 + Xki_metc13 + Xli_metc13 + Xlu_metc13 + Xsp_metc13 + Xre_metc13 + Xve_metc13,		# Xbody_metc13
    Cki_apap * fup_apap,		# Cki_free_apap
    Cki_co2c13 * fup_co2c13,		# Cki_free_co2c13
    Cki_metc13 * fup_metc13,		# Cki_free_metc13
    Cli_apap * fup_apap,		# Cli_free_apap
    Cli_co2c13 * fup_co2c13,		# Cli_free_co2c13
    Cli_metc13 * fup_metc13,		# Cli_free_metc13
    Cve_apap / BP_apap,		# Cpl_ve_apap
    Cve_co2c13 / BP_co2c13,		# Cpl_ve_co2c13
    Cve_metc13 / BP_metc13,		# Cpl_ve_metc13
    Are_apap / Vre,		# Cre_apap
    Are_co2c13 / Vre,		# Cre_co2c13
    Are_metc13 / Vre,		# Cre_metc13
    (Are_apap / Vre) * Mr_apap,		# Mre_apap
    (Are_co2c13 / Vre) * Mr_co2c13,		# Mre_co2c13
    (Are_metc13 / Vre) * Mr_metc13,		# Mre_metc13
    (1 / (1 + R_PDB)) * P_CO2,		# P_CO2c12
    (R_PDB / (1 + R_PDB)) * P_CO2 + Exhalation_co2c13 / 60,		# P_CO2c13
    QC * FQbo,		# Qbo
    QC * FQgu,		# Qgu
    QC * FQh,		# Qh
    QC * FQhe,		# Qhe
    QC * FQki,		# Qki
    QC * FQlu,		# Qlu
    QC * FQre,		# Qre
    QC * FQsp,		# Qsp
    ((P_CO2c13 / P_CO2c12 - R_PDB) / R_PDB) * 1000,		# DOB
    P_CO2c13 / (P_CO2c12 + P_CO2c13),		# P_CO2Fc13
    P_CO2c13 / P_CO2c12,		# P_CO2R
    Qh - Qgu - Qsp,		# Qha
]

