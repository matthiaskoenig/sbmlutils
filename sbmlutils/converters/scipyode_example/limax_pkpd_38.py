"""
limax_pkpd_38
"""
import numpy as np


x0 = [
    0.0,		# Aar_apap
    0.0,		# Aar_co2c13
    0.0,		# Aar_metc13
    0.0,		# Abo_apap
    0.0,		# Abo_co2c13
    0.0,		# Abo_co2c13_fix
    0.0,		# Abo_metc13
    0.0,		# Abreath_co2c13
    0.0,		# Agu_apap
    0.0,		# Agu_co2c13
    0.0,		# Agu_metc13
    0.0,		# Ahe_apap
    0.0,		# Ahe_co2c13
    0.0,		# Ahe_metc13
    0.0,		# Aki_apap
    0.0,		# Aki_co2c13
    0.0,		# Aki_metc13
    0.0,		# Ali_apap
    0.0,		# Ali_co2c13
    0.0,		# Ali_metc13
    0.0,		# Alu_apap
    0.0,		# Alu_co2c13
    0.0,		# Alu_metc13
    0.0,		# Are_apap
    0.0,		# Are_co2c13
    0.0,		# Are_metc13
    0.0,		# Asp_apap
    0.0,		# Asp_co2c13
    0.0,		# Asp_metc13
    0.0,		# Aurine_apap
    0.0,		# Aurine_co2c13
    0.0,		# Aurine_metc13
    0.0,		# Ave_apap
    0.0,		# Ave_co2c13
    0.0,		# Ave_metc13
    0.0,		# DIV_apap
    0.0,		# DIV_co2c13
    0.0,		# DIV_metc13
    0.0,		# D_apap
    0.0,		# D_co2c13
    0.0,		# D_metc13
    0.0,		# cum_dose_apap
    0.0,		# cum_dose_co2c13
    0.0,		# cum_dose_metc13
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

def f_dxdt(x, t, p):
    """ ODE system """
    y = np.zeros(shape=(147, 1))
    y[0] = 0.024265 * (p[5] / 1)**0.5378 * (p[36] / 1)**0.3964,		# BSA
    y[1] = p[5] * p[11] + (p[37] - p[38]) * p[12] / 60,		# CO
    y[2] = 1 - (p[15] + p[18] + p[16] + p[19] + p[17] + p[21]),		# FQre
    y[3] = 1 - (p[23] + p[25] + p[24] + p[26] + p[27] + p[28] + p[30] + p[31] + p[22] + p[29]),		# FVre
    y[4] = (1.386 / p[91]) * 3600,		# Ki_apap
    y[5] = (1.386 / p[92]) * 3600,		# Ki_co2c13
    y[6] = (1.386 / p[93]) * 3600,		# Ki_metc13
    y[7] = p[5] * p[22],		# Var
    y[8] = p[5] * p[23],		# Vbo
    y[9] = p[5] * p[24],		# Vgu
    y[10] = p[5] * p[25],		# Vhe
    y[11] = p[5] * p[26],		# Vki
    y[12] = p[5] * p[27],		# Vli
    y[13] = p[5] * p[28],		# Vlu
    y[14] = p[5] * p[29],		# Vpl
    y[15] = p[5] * p[30],		# Vsp
    y[16] = p[5] * p[31],		# Vve
    y[17] = x[0] * p[74],		# Xar_apap
    y[18] = x[1] * p[75],		# Xar_co2c13
    y[19] = x[2] * p[76],		# Xar_metc13
    y[20] = x[3] * p[74],		# Xbo_apap
    y[21] = x[4] * p[75],		# Xbo_co2c13
    y[22] = x[5] * p[75],		# Xbo_co2c13_fix
    y[23] = x[6] * p[76],		# Xbo_metc13
    y[24] = x[7] * p[75],		# Xbreath_co2c13
    y[25] = x[8] * p[74],		# Xgu_apap
    y[26] = x[9] * p[75],		# Xgu_co2c13
    y[27] = x[10] * p[76],		# Xgu_metc13
    y[28] = x[11] * p[74],		# Xhe_apap
    y[29] = x[12] * p[75],		# Xhe_co2c13
    y[30] = x[13] * p[76],		# Xhe_metc13
    y[31] = x[14] * p[74],		# Xki_apap
    y[32] = x[15] * p[75],		# Xki_co2c13
    y[33] = x[16] * p[76],		# Xki_metc13
    y[34] = x[17] * p[74],		# Xli_apap
    y[35] = x[18] * p[75],		# Xli_co2c13
    y[36] = x[19] * p[76],		# Xli_metc13
    y[37] = x[20] * p[74],		# Xlu_apap
    y[38] = x[21] * p[75],		# Xlu_co2c13
    y[39] = x[22] * p[76],		# Xlu_metc13
    y[40] = x[23] * p[74],		# Xre_apap
    y[41] = x[24] * p[75],		# Xre_co2c13
    y[42] = x[25] * p[76],		# Xre_metc13
    y[43] = x[26] * p[74],		# Xsp_apap
    y[44] = x[27] * p[75],		# Xsp_co2c13
    y[45] = x[28] * p[76],		# Xsp_metc13
    y[46] = x[29] * p[74],		# Xurine_apap
    y[47] = x[30] * p[75],		# Xurine_co2c13
    y[48] = x[31] * p[76],		# Xurine_metc13
    y[49] = x[32] * p[74],		# Xve_apap
    y[50] = x[33] * p[75],		# Xve_co2c13
    y[51] = x[34] * p[76],		# Xve_metc13
    y[52] = (p[0] / p[85]) * p[73] * y[12] * p[32] * 60 / 1000,		# APAPD_CLliv
    y[53] = p[9] * p[73] * y[12] * p[32] * 60 / 1000,		# CO2FIX_CLliv
    y[54] = (p[13] / p[87]) * p[73] * y[12] * p[32] * 60 / 1000,		# CYP1A2MET_CLliv
    y[55] = x[0] / y[7],		# Car_apap
    y[56] = x[1] / y[7],		# Car_co2c13
    y[57] = x[2] / y[7],		# Car_metc13
    y[58] = x[3] / y[8],		# Cbo_apap
    y[59] = x[4] / y[8],		# Cbo_co2c13
    y[60] = x[5] / y[8],		# Cbo_co2c13_fix
    y[61] = x[6] / y[8],		# Cbo_metc13
    y[62] = x[8] / y[9],		# Cgu_apap
    y[63] = x[9] / y[9],		# Cgu_co2c13
    y[64] = x[10] / y[9],		# Cgu_metc13
    y[65] = x[11] / y[10],		# Che_apap
    y[66] = x[12] / y[10],		# Che_co2c13
    y[67] = x[13] / y[10],		# Che_metc13
    y[68] = x[14] / y[11],		# Cki_apap
    y[69] = x[15] / y[11],		# Cki_co2c13
    y[70] = x[16] / y[11],		# Cki_metc13
    y[71] = x[17] / y[12],		# Cli_apap
    y[72] = x[18] / y[12],		# Cli_co2c13
    y[73] = x[19] / y[12],		# Cli_metc13
    y[74] = x[20] / y[13],		# Clu_apap
    y[75] = x[21] / y[13],		# Clu_co2c13
    y[76] = x[22] / y[13],		# Clu_metc13
    y[77] = x[26] / y[15],		# Csp_apap
    y[78] = x[27] / y[15],		# Csp_co2c13
    y[79] = x[28] / y[15],		# Csp_metc13
    y[80] = x[32] / y[16],		# Cve_apap
    y[81] = x[33] / y[16],		# Cve_co2c13
    y[82] = x[34] / y[16],		# Cve_metc13
    y[83] = (x[0] / y[7]) * p[74],		# Mar_apap
    y[84] = (x[1] / y[7]) * p[75],		# Mar_co2c13
    y[85] = (x[2] / y[7]) * p[76],		# Mar_metc13
    y[86] = (x[3] / y[8]) * p[74],		# Mbo_apap
    y[87] = (x[4] / y[8]) * p[75],		# Mbo_co2c13
    y[88] = (x[6] / y[8]) * p[76],		# Mbo_metc13
    y[89] = (x[8] / y[9]) * p[74],		# Mgu_apap
    y[90] = (x[9] / y[9]) * p[75],		# Mgu_co2c13
    y[91] = (x[10] / y[9]) * p[76],		# Mgu_metc13
    y[92] = (x[11] / y[10]) * p[74],		# Mhe_apap
    y[93] = (x[12] / y[10]) * p[75],		# Mhe_co2c13
    y[94] = (x[13] / y[10]) * p[76],		# Mhe_metc13
    y[95] = (x[14] / y[11]) * p[74],		# Mki_apap
    y[96] = (x[15] / y[11]) * p[75],		# Mki_co2c13
    y[97] = (x[16] / y[11]) * p[76],		# Mki_metc13
    y[98] = (x[17] / y[12]) * p[74],		# Mli_apap
    y[99] = (x[18] / y[12]) * p[75],		# Mli_co2c13
    y[100] = (x[19] / y[12]) * p[76],		# Mli_metc13
    y[101] = (x[20] / y[13]) * p[74],		# Mlu_apap
    y[102] = (x[21] / y[13]) * p[75],		# Mlu_co2c13
    y[103] = (x[22] / y[13]) * p[76],		# Mlu_metc13
    y[104] = (x[26] / y[15]) * p[74],		# Msp_apap
    y[105] = (x[27] / y[15]) * p[75],		# Msp_co2c13
    y[106] = (x[28] / y[15]) * p[76],		# Msp_metc13
    y[107] = (x[32] / y[16]) * p[74],		# Mve_apap
    y[108] = (x[33] / y[16]) * p[75],		# Mve_co2c13
    y[109] = (x[34] / y[16]) * p[76],		# Mve_metc13
    y[110] = y[0] * p[80] / 60,		# P_CO2
    y[111] = (y[1] / 1000) * 3600,		# QC
    y[112] = y[14] * y[7] / (y[16] + y[7]),		# Vplas_art
    y[113] = y[14] * y[16] / (y[16] + y[7]),		# Vplas_ven
    y[114] = p[5] * y[3],		# Vre
    y[115] = y[17] + y[20] + y[28] + y[25] + y[31] + y[34] + y[37] + y[43] + y[40] + y[49],		# Xbody_apap
    y[116] = y[18] + y[21] + y[29] + y[26] + y[32] + y[35] + y[38] + y[44] + y[41] + y[50],		# Xbody_co2c13
    y[117] = y[19] + y[23] + y[30] + y[27] + y[33] + y[36] + y[39] + y[45] + y[42] + y[51],		# Xbody_metc13
    y[118] = y[68] * p[88],		# Cki_free_apap
    y[119] = y[69] * p[89],		# Cki_free_co2c13
    y[120] = y[70] * p[90],		# Cki_free_metc13
    y[121] = y[71] * p[88],		# Cli_free_apap
    y[122] = y[72] * p[89],		# Cli_free_co2c13
    y[123] = y[73] * p[90],		# Cli_free_metc13
    y[124] = y[80] / p[2],		# Cpl_ve_apap
    y[125] = y[81] / p[3],		# Cpl_ve_co2c13
    y[126] = y[82] / p[4],		# Cpl_ve_metc13
    y[127] = x[23] / y[114],		# Cre_apap
    y[128] = x[24] / y[114],		# Cre_co2c13
    y[129] = x[25] / y[114],		# Cre_metc13
    y[130] = (x[23] / y[114]) * p[74],		# Mre_apap
    y[131] = (x[24] / y[114]) * p[75],		# Mre_co2c13
    y[132] = (x[25] / y[114]) * p[76],		# Mre_metc13
    y[133] = (1 / (1 + p[81])) * y[110],		# P_CO2c12
    y[134] = (p[81] / (1 + p[81])) * y[110] + Exhalation_co2c13 / 60,		# P_CO2c13
    y[135] = y[111] * p[15],		# Qbo
    y[136] = y[111] * p[16],		# Qgu
    y[137] = y[111] * p[17],		# Qh
    y[138] = y[111] * p[18],		# Qhe
    y[139] = y[111] * p[19],		# Qki
    y[140] = y[111] * p[20],		# Qlu
    y[141] = y[111] * y[2],		# Qre
    y[142] = y[111] * p[21],		# Qsp
    y[143] = ((y[134] / y[133] - p[81]) / p[81]) * 1000,		# DOB
    y[144] = y[134] / (y[133] + y[134]),		# P_CO2Fc13
    y[145] = y[134] / y[133],		# P_CO2R
    y[146] = y[137] - y[136] - y[142],		# Qha


    # reactions
    APAPD = y[52] * 1 * (y[121] / (y[121] + p[1]))
    Absorption_apap = (p[46] * x[38] / p[74]) * p[33]
    Absorption_co2c13 = (p[47] * x[39] / p[75]) * p[34]
    Absorption_metc13 = (p[48] * x[40] / p[76]) * p[35]
    CO2FIX = y[53] * 1 * (y[72] / (y[72] + p[10]))
    CYP1A2MET = y[54] * 1 * (y[123] / (y[123] + p[14]))
    Exhalation_co2c13 = p[45] * 60 * y[75] * y[13]
    Fixation_co2c13 = p[42] * 60 * y[81] * y[16] * (1 - y[60] / p[43])
    Infusion_apap = (p[82] / p[74]) * 60
    Infusion_co2c13 = (p[83] / p[75]) * 60
    Infusion_metc13 = (p[84] / p[76]) * 60
    Injection_apap = y[4] * x[35] / p[74]
    Injection_co2c13 = y[5] * x[36] / p[75]
    Injection_metc13 = y[6] * x[37] / p[76]
    Release_co2c13 = p[44] * 60 * y[60] * y[16]
    ar_bo_apap = y[135] * y[55]
    ar_bo_co2c13 = y[135] * y[56]
    ar_bo_metc13 = y[135] * y[57]
    ar_gu_apap = y[136] * y[55]
    ar_gu_co2c13 = y[136] * y[56]
    ar_gu_metc13 = y[136] * y[57]
    ar_he_apap = y[138] * y[55]
    ar_he_co2c13 = y[138] * y[56]
    ar_he_metc13 = y[138] * y[57]
    ar_ki_apap = y[139] * y[55]
    ar_ki_co2c13 = y[139] * y[56]
    ar_ki_metc13 = y[139] * y[57]
    ar_li_apap = y[146] * y[55]
    ar_li_co2c13 = y[146] * y[56]
    ar_li_metc13 = y[146] * y[57]
    ar_re_apap = y[141] * y[55]
    ar_re_co2c13 = y[141] * y[56]
    ar_re_metc13 = y[141] * y[57]
    ar_sp_apap = y[142] * y[55]
    ar_sp_co2c13 = y[142] * y[56]
    ar_sp_metc13 = y[142] * y[57]
    bo_ve_apap = y[135] * (y[58] / p[49]) * p[2]
    bo_ve_co2c13 = y[135] * (y[59] / p[50]) * p[3]
    bo_ve_metc13 = y[135] * (y[61] / p[51]) * p[4]
    gu_li_apap = y[136] * (y[62] / p[52]) * p[2]
    gu_li_co2c13 = y[136] * (y[63] / p[53]) * p[3]
    gu_li_metc13 = y[136] * (y[64] / p[54]) * p[4]
    he_ve_apap = y[138] * (y[65] / p[55]) * p[2]
    he_ve_co2c13 = y[138] * (y[66] / p[56]) * p[3]
    he_ve_metc13 = y[138] * (y[67] / p[57]) * p[4]
    ki_ve_apap = y[139] * (y[68] / p[58]) * p[2]
    ki_ve_co2c13 = y[139] * (y[69] / p[59]) * p[3]
    ki_ve_metc13 = y[139] * (y[70] / p[60]) * p[4]
    li_ve_apap = y[137] * (y[71] / p[61]) * p[2]
    li_ve_co2c13 = y[137] * (y[72] / p[62]) * p[3]
    li_ve_metc13 = y[137] * (y[73] / p[63]) * p[4]
    lu_ar_apap = y[140] * (y[74] / p[64]) * p[2]
    lu_ar_co2c13 = y[140] * (y[75] / p[65]) * p[3]
    lu_ar_metc13 = y[140] * (y[76] / p[66]) * p[4]
    re_ve_apap = y[141] * (y[127] / p[67]) * p[2]
    re_ve_co2c13 = y[141] * (y[128] / p[68]) * p[3]
    re_ve_metc13 = y[141] * (y[129] / p[69]) * p[4]
    sp_li_apap = y[142] * (y[77] / p[70]) * p[2]
    sp_li_co2c13 = y[142] * (y[78] / p[71]) * p[3]
    sp_li_metc13 = y[142] * (y[79] / p[72]) * p[4]
    ve_lu_apap = y[140] * y[80]
    ve_lu_co2c13 = y[140] * y[81]
    ve_lu_metc13 = y[140] * y[82]
    vre_apap = p[6] * y[118]
    vre_co2c13 = p[7] * y[119]
    vre_metc13 = p[8] * y[120]


    return [
         + lu_ar_apap - ar_re_apap - ar_bo_apap - ar_gu_apap - ar_he_apap - ar_ki_apap - ar_sp_apap - ar_li_apap,		# Aar_apap
         + lu_ar_co2c13 - ar_re_co2c13 - ar_bo_co2c13 - ar_gu_co2c13 - ar_he_co2c13 - ar_ki_co2c13 - ar_sp_co2c13 - ar_li_co2c13,		# Aar_co2c13
         + lu_ar_metc13 - ar_re_metc13 - ar_bo_metc13 - ar_gu_metc13 - ar_he_metc13 - ar_ki_metc13 - ar_sp_metc13 - ar_li_metc13,		# Aar_metc13
         + ar_bo_apap - bo_ve_apap,		# Abo_apap
         + ar_bo_co2c13 - bo_ve_co2c13,		# Abo_co2c13
         + Fixation_co2c13 - Release_co2c13,		# Abo_co2c13_fix
         + ar_bo_metc13 - bo_ve_metc13,		# Abo_metc13
         + Exhalation_co2c13,		# Abreath_co2c13
         + Absorption_apap + ar_gu_apap - gu_li_apap,		# Agu_apap
         + Absorption_co2c13 + ar_gu_co2c13 - gu_li_co2c13,		# Agu_co2c13
         + Absorption_metc13 + ar_gu_metc13 - gu_li_metc13,		# Agu_metc13
         + ar_he_apap - he_ve_apap,		# Ahe_apap
         + ar_he_co2c13 - he_ve_co2c13,		# Ahe_co2c13
         + ar_he_metc13 - he_ve_metc13,		# Ahe_metc13
         - vre_apap + ar_ki_apap - ki_ve_apap,		# Aki_apap
         - vre_co2c13 + ar_ki_co2c13 - ki_ve_co2c13,		# Aki_co2c13
         - vre_metc13 + ar_ki_metc13 - ki_ve_metc13,		# Aki_metc13
         + CYP1A2MET - APAPD + gu_li_apap + sp_li_apap + ar_li_apap - li_ve_apap,		# Ali_apap
         + CYP1A2MET - CO2FIX + gu_li_co2c13 + sp_li_co2c13 + ar_li_co2c13 - li_ve_co2c13,		# Ali_co2c13
         - CYP1A2MET + gu_li_metc13 + sp_li_metc13 + ar_li_metc13 - li_ve_metc13,		# Ali_metc13
         + ve_lu_apap - lu_ar_apap,		# Alu_apap
         - Exhalation_co2c13 + ve_lu_co2c13 - lu_ar_co2c13,		# Alu_co2c13
         + ve_lu_metc13 - lu_ar_metc13,		# Alu_metc13
         + ar_re_apap - re_ve_apap,		# Are_apap
         + ar_re_co2c13 - re_ve_co2c13,		# Are_co2c13
         + ar_re_metc13 - re_ve_metc13,		# Are_metc13
         + ar_sp_apap - sp_li_apap,		# Asp_apap
         + ar_sp_co2c13 - sp_li_co2c13,		# Asp_co2c13
         + ar_sp_metc13 - sp_li_metc13,		# Asp_metc13
         + vre_apap,		# Aurine_apap
         + vre_co2c13,		# Aurine_co2c13
         + vre_metc13,		# Aurine_metc13
         + Injection_apap + Infusion_apap - ve_lu_apap + re_ve_apap + bo_ve_apap + he_ve_apap + ki_ve_apap + li_ve_apap,		# Ave_apap
         - Fixation_co2c13 + Release_co2c13 + Injection_co2c13 + Infusion_co2c13 - ve_lu_co2c13 + re_ve_co2c13 + bo_ve_co2c13 + he_ve_co2c13 + ki_ve_co2c13 + li_ve_co2c13,		# Ave_co2c13
         + Injection_metc13 + Infusion_metc13 - ve_lu_metc13 + re_ve_metc13 + bo_ve_metc13 + he_ve_metc13 + ki_ve_metc13 + li_ve_metc13,		# Ave_metc13
        -Injection_apap * p[74],		# DIV_apap
        -Injection_co2c13 * p[75],		# DIV_co2c13
        -Injection_metc13 * p[76],		# DIV_metc13
        -Absorption_apap * p[74],		# D_apap
        -Absorption_co2c13 * p[75],		# D_co2c13
        -Absorption_metc13 * p[76],		# D_metc13
        p[82] * 60,		# cum_dose_apap
        p[83] * 60,		# cum_dose_co2c13
        p[84] * 60,		# cum_dose_metc13
    ]

