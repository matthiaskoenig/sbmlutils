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
    y = [
        0.024265 * (p[5] / 1)**0.5378 * (p[36] / 1)**0.3964,		# BSA
        p[5] * p[11] + (p[37] - p[38]) * p[12] / 60,		# CO
        1 - (p[15] + p[18] + p[16] + p[19] + p[17] + p[21]),		# FQre
        1 - (p[23] + p[25] + p[24] + p[26] + p[27] + p[28] + p[30] + p[31] + p[22] + p[29]),		# FVre
        (1.386 / p[91]) * 3600,		# Ki_apap
        (1.386 / p[92]) * 3600,		# Ki_co2c13
        (1.386 / p[93]) * 3600,		# Ki_metc13
        p[5] * p[22],		# Var
        p[5] * p[23],		# Vbo
        p[5] * p[24],		# Vgu
        p[5] * p[25],		# Vhe
        p[5] * p[26],		# Vki
        p[5] * p[27],		# Vli
        p[5] * p[28],		# Vlu
        p[5] * p[29],		# Vpl
        p[5] * p[30],		# Vsp
        p[5] * p[31],		# Vve
        x[0] * p[74],		# Xar_apap
        x[1] * p[75],		# Xar_co2c13
        x[2] * p[76],		# Xar_metc13
        x[3] * p[74],		# Xbo_apap
        x[4] * p[75],		# Xbo_co2c13
        x[5] * p[75],		# Xbo_co2c13_fix
        x[6] * p[76],		# Xbo_metc13
        x[7] * p[75],		# Xbreath_co2c13
        x[8] * p[74],		# Xgu_apap
        x[9] * p[75],		# Xgu_co2c13
        x[10] * p[76],		# Xgu_metc13
        x[11] * p[74],		# Xhe_apap
        x[12] * p[75],		# Xhe_co2c13
        x[13] * p[76],		# Xhe_metc13
        x[14] * p[74],		# Xki_apap
        x[15] * p[75],		# Xki_co2c13
        x[16] * p[76],		# Xki_metc13
        x[17] * p[74],		# Xli_apap
        x[18] * p[75],		# Xli_co2c13
        x[19] * p[76],		# Xli_metc13
        x[20] * p[74],		# Xlu_apap
        x[21] * p[75],		# Xlu_co2c13
        x[22] * p[76],		# Xlu_metc13
        x[23] * p[74],		# Xre_apap
        x[24] * p[75],		# Xre_co2c13
        x[25] * p[76],		# Xre_metc13
        x[26] * p[74],		# Xsp_apap
        x[27] * p[75],		# Xsp_co2c13
        x[28] * p[76],		# Xsp_metc13
        x[29] * p[74],		# Xurine_apap
        x[30] * p[75],		# Xurine_co2c13
        x[31] * p[76],		# Xurine_metc13
        x[32] * p[74],		# Xve_apap
        x[33] * p[75],		# Xve_co2c13
        x[34] * p[76],		# Xve_metc13
        (p[0] / p[85]) * p[73] * y[101] * p[32] * 60 / 1000,		# APAPD_CLliv
        p[9] * p[73] * y[101] * p[32] * 60 / 1000,		# CO2FIX_CLliv
        (p[13] / p[87]) * p[73] * y[101] * p[32] * 60 / 1000,		# CYP1A2MET_CLliv
        x[0] / y[96],		# Car_apap
        x[1] / y[96],		# Car_co2c13
        x[2] / y[96],		# Car_metc13
        x[3] / y[97],		# Cbo_apap
        x[4] / y[97],		# Cbo_co2c13
        x[5] / y[97],		# Cbo_co2c13_fix
        x[6] / y[97],		# Cbo_metc13
        x[8] / y[98],		# Cgu_apap
        x[9] / y[98],		# Cgu_co2c13
        x[10] / y[98],		# Cgu_metc13
        x[11] / y[99],		# Che_apap
        x[12] / y[99],		# Che_co2c13
        x[13] / y[99],		# Che_metc13
        x[14] / y[100],		# Cki_apap
        x[15] / y[100],		# Cki_co2c13
        x[16] / y[100],		# Cki_metc13
        x[17] / y[101],		# Cli_apap
        x[18] / y[101],		# Cli_co2c13
        x[19] / y[101],		# Cli_metc13
        x[20] / y[102],		# Clu_apap
        x[21] / y[102],		# Clu_co2c13
        x[22] / y[102],		# Clu_metc13
        x[26] / y[107],		# Csp_apap
        x[27] / y[107],		# Csp_co2c13
        x[28] / y[107],		# Csp_metc13
        x[32] / y[108],		# Cve_apap
        x[33] / y[108],		# Cve_co2c13
        x[34] / y[108],		# Cve_metc13
        (x[0] / y[96]) * p[74],		# Mar_apap
        (x[1] / y[96]) * p[75],		# Mar_co2c13
        (x[2] / y[96]) * p[76],		# Mar_metc13
        (x[3] / y[97]) * p[74],		# Mbo_apap
        (x[4] / y[97]) * p[75],		# Mbo_co2c13
        (x[6] / y[97]) * p[76],		# Mbo_metc13
        (x[8] / y[98]) * p[74],		# Mgu_apap
        (x[9] / y[98]) * p[75],		# Mgu_co2c13
        (x[10] / y[98]) * p[76],		# Mgu_metc13
        (x[11] / y[99]) * p[74],		# Mhe_apap
        (x[12] / y[99]) * p[75],		# Mhe_co2c13
        (x[13] / y[99]) * p[76],		# Mhe_metc13
        (x[14] / y[100]) * p[74],		# Mki_apap
        (x[15] / y[100]) * p[75],		# Mki_co2c13
        (x[16] / y[100]) * p[76],		# Mki_metc13
        (x[17] / y[101]) * p[74],		# Mli_apap
        (x[18] / y[101]) * p[75],		# Mli_co2c13
        (x[19] / y[101]) * p[76],		# Mli_metc13
        (x[20] / y[102]) * p[74],		# Mlu_apap
        (x[21] / y[102]) * p[75],		# Mlu_co2c13
        (x[22] / y[102]) * p[76],		# Mlu_metc13
        (x[26] / y[107]) * p[74],		# Msp_apap
        (x[27] / y[107]) * p[75],		# Msp_co2c13
        (x[28] / y[107]) * p[76],		# Msp_metc13
        (x[32] / y[108]) * p[74],		# Mve_apap
        (x[33] / y[108]) * p[75],		# Mve_co2c13
        (x[34] / y[108]) * p[76],		# Mve_metc13
        y[1] * p[80] / 60,		# P_CO2
        (y[2] / 1000) * 3600,		# QC
        y[103] * y[96] / (y[108] + y[96]),		# Vplas_art
        y[103] * y[108] / (y[108] + y[96]),		# Vplas_ven
        p[5] * y[47],		# Vre
        y[109] + y[112] + y[123] + y[120] + y[126] + y[129] + y[132] + y[138] + y[135] + y[144],		# Xbody_apap
        y[110] + y[113] + y[124] + y[121] + y[127] + y[130] + y[133] + y[139] + y[136] + y[145],		# Xbody_co2c13
        y[111] + y[115] + y[125] + y[122] + y[128] + y[131] + y[134] + y[140] + y[137] + y[146],		# Xbody_metc13
        y[18] * p[88],		# Cki_free_apap
        y[19] * p[89],		# Cki_free_co2c13
        y[23] * p[90],		# Cki_free_metc13
        y[24] * p[88],		# Cli_free_apap
        y[25] * p[89],		# Cli_free_co2c13
        y[29] * p[90],		# Cli_free_metc13
        y[42] / p[2],		# Cpl_ve_apap
        y[43] / p[3],		# Cpl_ve_co2c13
        y[44] / p[4],		# Cpl_ve_metc13
        x[23] / y[106],		# Cre_apap
        x[24] / y[106],		# Cre_co2c13
        x[25] / y[106],		# Cre_metc13
        (x[23] / y[106]) * p[74],		# Mre_apap
        (x[24] / y[106]) * p[75],		# Mre_co2c13
        (x[25] / y[106]) * p[76],		# Mre_metc13
        (1 / (1 + p[81])) * y[81],		# P_CO2c12
        (p[81] / (1 + p[81])) * y[81] + Exhalation_co2c13 / 60,		# P_CO2c13
        y[86] * p[15],		# Qbo
        y[86] * p[16],		# Qgu
        y[86] * p[17],		# Qh
        y[86] * p[18],		# Qhe
        y[86] * p[19],		# Qki
        y[86] * p[20],		# Qlu
        y[86] * y[46],		# Qre
        y[86] * p[21],		# Qsp
        ((y[85] / y[84] - p[81]) / p[81]) * 1000,		# DOB
        y[85] / (y[84] + y[85]),		# P_CO2Fc13
        y[85] / y[84],		# P_CO2R
        y[89] - y[88] - y[95],		# Qha
    ]

    # reactions
    APAPD = y[0] * 1 * (y[26] / (y[26] + p[1]))
    Absorption_apap = (p[46] * x[38] / p[74]) * p[33]
    Absorption_co2c13 = (p[47] * x[39] / p[75]) * p[34]
    Absorption_metc13 = (p[48] * x[40] / p[76]) * p[35]
    CO2FIX = y[3] * 1 * (y[25] / (y[25] + p[10]))
    CYP1A2MET = y[4] * 1 * (y[28] / (y[28] + p[14]))
    Exhalation_co2c13 = p[45] * 60 * y[31] * y[102]
    Fixation_co2c13 = p[42] * 60 * y[43] * y[108] * (1 - y[10] / p[43])
    Infusion_apap = (p[82] / p[74]) * 60
    Infusion_co2c13 = (p[83] / p[75]) * 60
    Infusion_metc13 = (p[84] / p[76]) * 60
    Injection_apap = y[48] * x[35] / p[74]
    Injection_co2c13 = y[49] * x[36] / p[75]
    Injection_metc13 = y[50] * x[37] / p[76]
    Release_co2c13 = p[44] * 60 * y[10] * y[108]
    ar_bo_apap = y[87] * y[5]
    ar_bo_co2c13 = y[87] * y[6]
    ar_bo_metc13 = y[87] * y[7]
    ar_gu_apap = y[88] * y[5]
    ar_gu_co2c13 = y[88] * y[6]
    ar_gu_metc13 = y[88] * y[7]
    ar_he_apap = y[91] * y[5]
    ar_he_co2c13 = y[91] * y[6]
    ar_he_metc13 = y[91] * y[7]
    ar_ki_apap = y[92] * y[5]
    ar_ki_co2c13 = y[92] * y[6]
    ar_ki_metc13 = y[92] * y[7]
    ar_li_apap = y[90] * y[5]
    ar_li_co2c13 = y[90] * y[6]
    ar_li_metc13 = y[90] * y[7]
    ar_re_apap = y[94] * y[5]
    ar_re_co2c13 = y[94] * y[6]
    ar_re_metc13 = y[94] * y[7]
    ar_sp_apap = y[95] * y[5]
    ar_sp_co2c13 = y[95] * y[6]
    ar_sp_metc13 = y[95] * y[7]
    bo_ve_apap = y[87] * (y[8] / p[49]) * p[2]
    bo_ve_co2c13 = y[87] * (y[9] / p[50]) * p[3]
    bo_ve_metc13 = y[87] * (y[11] / p[51]) * p[4]
    gu_li_apap = y[88] * (y[12] / p[52]) * p[2]
    gu_li_co2c13 = y[88] * (y[13] / p[53]) * p[3]
    gu_li_metc13 = y[88] * (y[14] / p[54]) * p[4]
    he_ve_apap = y[91] * (y[15] / p[55]) * p[2]
    he_ve_co2c13 = y[91] * (y[16] / p[56]) * p[3]
    he_ve_metc13 = y[91] * (y[17] / p[57]) * p[4]
    ki_ve_apap = y[92] * (y[18] / p[58]) * p[2]
    ki_ve_co2c13 = y[92] * (y[19] / p[59]) * p[3]
    ki_ve_metc13 = y[92] * (y[23] / p[60]) * p[4]
    li_ve_apap = y[89] * (y[24] / p[61]) * p[2]
    li_ve_co2c13 = y[89] * (y[25] / p[62]) * p[3]
    li_ve_metc13 = y[89] * (y[29] / p[63]) * p[4]
    lu_ar_apap = y[93] * (y[30] / p[64]) * p[2]
    lu_ar_co2c13 = y[93] * (y[31] / p[65]) * p[3]
    lu_ar_metc13 = y[93] * (y[32] / p[66]) * p[4]
    re_ve_apap = y[94] * (y[36] / p[67]) * p[2]
    re_ve_co2c13 = y[94] * (y[37] / p[68]) * p[3]
    re_ve_metc13 = y[94] * (y[38] / p[69]) * p[4]
    sp_li_apap = y[95] * (y[39] / p[70]) * p[2]
    sp_li_co2c13 = y[95] * (y[40] / p[71]) * p[3]
    sp_li_metc13 = y[95] * (y[41] / p[72]) * p[4]
    ve_lu_apap = y[93] * y[42]
    ve_lu_co2c13 = y[93] * y[43]
    ve_lu_metc13 = y[93] * y[44]
    vre_apap = p[6] * y[20]
    vre_co2c13 = p[7] * y[21]
    vre_metc13 = p[8] * y[22]


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

