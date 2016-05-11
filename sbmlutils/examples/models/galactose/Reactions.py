"""
Reactions and transporters of Galactose metabolism.
"""
from sbmlutils.modelcreator.processes.ReactionTemplate import ReactionTemplate


#############################################################################################
#    REACTIONS
#############################################################################################
GALK = ReactionTemplate(
    rid='c__GALK',
    name='Galactokinase [c__]',
    equation='c__gal + c__atp <-> c__gal1p + c__adp + c__hydron [c__galM, c__gal1pM]',
    # C6H12O6 (0) + C10H12N5O13P3 (-4) <-> C6H11O9P (-2) + C10H12N5O10P2 (-3) + H (+1)
    localization='c',
    compartments=['c__'],
    pars=[
            ('GALK_PA',      0.024,   'mole'),
            ('GALK_keq',     50,      '-'),
            ('GALK_k_gal1p', 1.5,     'mM'),
            ('GALK_k_adp',   0.8,     'mM'),
            ('GALK_ki_gal1p', 5.3,    'mM'),
            ('GALK_kcat',     8.7,    'per_s'),
            ('GALK_k_gal',   0.14,    'mM'),
            ('GALK_k_atp',   0.034,   'mM'),
            ('c__GALK_P',    1.0,     'mM'),
    ],
    rules=[
            ('c__GALK_Vmax', 'c__scale * GALK_PA * GALK_kcat * c__GALK_P/REF_P', 'mole_per_s'),
            ('c__GALK_dm', '( (1 dimensionless + c__gal_tot/GALK_k_gal)*(1 dimensionless +c__atp/GALK_k_atp) +(1 dimensionless+c__gal1p_tot/GALK_k_gal1p)*(1 dimensionless+c__adp/GALK_k_adp) -1 dimensionless)', '-'),
            ('c__GALK_V', 'c__GALK_Vmax/(GALK_k_gal*GALK_k_atp)*1 dimensionless/(1 dimensionless+c__gal1p_tot/GALK_ki_gal1p) * 1 dimensionless/c__GALK_dm', 'mole_per_s_per_mM2'),
            ('c__GALK_Vf', 'c__GALK_V * c__gal_tot*c__atp', 'mole_per_s'),
            ('c__GALK_Vb', 'c__GALK_V * c__gal1p_tot*c__adp/GALK_keq', 'mole_per_s'),
    ],
    formula=('c__gal/c__gal_tot * c__GALK_Vf - c__gal1p/c__gal1p_tot * c__GALK_Vb', 'mole_per_s')
)

GALKM = ReactionTemplate(
    rid='c__GALKM',
    name='Galactokinase M [c__]',
    equation='c__galM + c__atp -> c__gal1pM + c__adp + c__hydron [c__gal, c__gal1p]',
    # C6H12O6 (0) + C10H12N5O13P3 (-4) <-> C6H11O9P (-2) + C10H12N5O10P2 (-3) + H (+1)
    localization='c',
    compartments=['c__'],
    formula=('c__galM/c__gal_tot * c__GALK_Vf - c__gal1pM/c__gal1p_tot * c__GALK_Vb', 'mole_per_s')
)
#############################################################################################
IMP = ReactionTemplate(
    rid='c__IMP',
    name='Inositol monophosphatase [c__]',
    equation='c__gal1p + c__h2o => c__gal + c__phos [c__gal1pM]',
    # C6H11O9P (-2) + H20 (0) => C6H12O6 (0) + HO4P (-2)
    localization='c',
    compartments=['c__'],
    pars=[
            ('IMP_f', 0.05, '-'),
            ('IMP_k_gal1p', 0.35, 'mM'),
            ('c__IMP_P', 1.0, 'mM'),
    ],
    rules=[
            ('c__IMP_Vmax', 'IMP_f * c__GALK_Vmax * c__IMP_P/REF_P', 'mole_per_s'),
            ('c__IMP_dm', '(1 dimensionless + c__gal1p_tot/IMP_k_gal1p)', '-'),
            ('c__IMP_Vf', 'c__IMP_Vmax/IMP_k_gal1p * c__gal1p_tot/c__IMP_dm', 'mole_per_s'),
    ],
    formula=('c__gal1p/c__gal1p_tot * c__IMP_Vf', 'mole_per_s')
)

IMPM = ReactionTemplate(
    rid='c__IMPM',
    name='Inositol monophosphatase M [c__]',
    equation='c__gal1pM + c__h2o => c__galM + c__phos [c__gal1p]',
    # C6H11O9P (-2) + H20 (0) => C6H12O6 (0) + HO4P (-2)
    localization='c',
    compartments=['c__'],
    formula=('c__gal1pM/c__gal1p_tot * c__IMP_Vf', 'mole_per_s')
)

#############################################################################################
ATPS = ReactionTemplate(
    rid='c__ATPS',
    name='ATP synthase [c__]',
    equation='c__adp + c__phos + c__hydron <-> c__atp + c__h2o',
    # C10H12N5O10P2 (-3) + HO4P (-2) + H (+1) <-> C10H12N5O13P3 (-4) + H20 (0)
    localization='c',
    compartments=['c__'],
    pars=[
            ('ATPS_f', 100.0,  '-'),
            ('ATPS_keq', 0.58, 'per_mM'),
            ('ATPS_k_adp', 0.1, 'mM'),
            ('ATPS_k_atp', 0.5, 'mM'),
            ('ATPS_k_phos', 0.1, 'mM'),
            ('c__ATPS_P', 1.0, 'mM'),
    ],
    rules=[
            ('c__ATPS_Vmax', 'ATPS_f* c__GALK_Vmax * c__ATPS_P/REF_P', 'mole_per_s'),
    ],
    formula=('c__ATPS_Vmax/(ATPS_k_adp*ATPS_k_phos) *(c__adp*c__phos-c__atp/ATPS_keq)/((1 dimensionless+c__adp/ATPS_k_adp)*(1 dimensionless+c__phos/ATPS_k_phos) + c__atp/ATPS_k_atp)', 'mole_per_s')
)
#############################################################################################
ALDR = ReactionTemplate(
    rid='c__ALDR',
    name='Aldose reductase [c__]',
    equation='c__gal + c__nadph + c__hydron <-> c__galtol + c__nadp [c__galM, c__galtolM]',
    # C6H12O6 (0) + C21H26N7O17P3 (-4) + H (+1) <-> C6H14O6 (0) + C21H25N7O17P3 (-3)
    localization='c',
    compartments=['c__'],
    pars=[
            ('ALDR_f',        1E6,   '-'),
            ('ALDR_keq',       4.0, '-'),
            ('ALDR_k_gal',    40.0, 'mM'),
            ('ALDR_k_galtol', 40.0, 'mM'),
            ('ALDR_k_nadp',   0.1,  'mM'),
            ('ALDR_k_nadph',  0.1,  'mM'),
            ('c__ALDR_P',     1.0,  'mM'),
    ],
    rules=[
            ('c__ALDR_Vmax', 'ALDR_f * c__GALK_Vmax * c__ALDR_P/REF_P', 'mole_per_s'),
            ('c__ALDR_dm', '((1 dimensionless +c__gal_tot/ALDR_k_gal)*(1 dimensionless + c__nadph/ALDR_k_nadph) +(1 dimensionless +c__galtol_tot/ALDR_k_galtol)*(1 dimensionless +c__nadp/ALDR_k_nadp) -1 dimensionless)', '-'),
            ('c__ALDR_V', 'c__ALDR_Vmax/(ALDR_k_gal*ALDR_k_nadp)*1 dimensionless/c__ALDR_dm', 'mole_per_s_per_mM2'),
            ('c__ALDR_Vf', 'c__ALDR_V*c__gal_tot*c__nadph', 'mole_per_s'),
            ('c__ALDR_Vb', 'c__ALDR_V*c__galtol_tot*c__nadp/ALDR_keq', 'mole_per_s'),
    ],
    formula=('c__gal/c__gal_tot * c__ALDR_Vf - c__galtol/c__galtol_tot * c__ALDR_Vb', 'mole_per_s')
)

ALDRM = ReactionTemplate(
    rid='c__ALDRM',
    name='Aldose reductase M [c__]',
    equation='c__galM + c__nadph + c__hydron <-> c__galtolM + c__nadp [c__gal, c__galtol]',
    # C6H12O6 (0) + C21H26N7O17P3 (-4) + H (+1) <-> C6H14O6 (0) + C21H25N7O17P3 (-3)
    localization='c',
    compartments=['c__'],
    formula=('c__galM/c__gal_tot * c__ALDR_Vf - c__galtolM/c__galtol_tot * c__ALDR_Vb', 'mole_per_s')
)
#############################################################################################
NADPR = ReactionTemplate(
    rid='c__NADPR',
    name='NADP Reductase [c__]',
    equation='c__nadp + c__h2 <-> c__nadph + c__hydron',
    # C21H25N7O17P3 (-3) + H2(0) <-> C21H26N7O17P3 (-4) + H (+1)
    localization='c',
    compartments=['c__'],
    pars=[
            ('NADPR_f',      1E-10,   '-'),
            ('NADPR_keq',    1,       '-'),
            ('NADPR_k_nadp',   0.015,   'mM'),
            ('NADPR_ki_nadph', 0.010,   'mM'),
            ('c__NADPR_P',     1.0,     'mM'),
    ],
    rules=[
            ('c__NADPR_Vmax', 'NADPR_f * c__ALDR_Vmax * c__NADPR_P/REF_P', 'mole_per_s'),
    ],
    formula=('c__NADPR_Vmax/NADPR_k_nadp *(c__nadp - c__nadph/NADPR_keq)/(1 dimensionless +c__nadp/NADPR_k_nadp +c__nadph/NADPR_ki_nadph)', 'mole_per_s')
)
#############################################################################################
GALT = ReactionTemplate(
    rid='c__GALT',
    name='Galactose-1-phosphate uridyl transferase [c__]',
    equation='c__gal1p + c__udpglc <-> c__glc1p + c__udpgal [c__utp, c__udp, c__gal1pM, c__udpglcM, c__glc1p, c__udpgalM]',
    # C6H11O9P (-2) + C15H22N2O17P2 (-2) <-> C6H11O9P (-2) + C15H22N2O17P2 (-2)
    localization='c',
    compartments=['c__'],
    pars=[
            ('GALT_f',        0.01,  '-'),
            ('GALT_keq',      1.0,   '-'),
            ('GALT_k_glc1p',  0.37,  'mM'),
            ('GALT_k_udpgal', 0.5,  'mM'),
            ('GALT_ki_utp',   0.13, 'mM'),
            ('GALT_ki_udp',   0.35, 'mM'),
            ('GALT_vm',     804,     '-'),
            ('GALT_k_gal1p',  1.25,  'mM'),
            ('GALT_k_udpglc', 0.43,  'mM'),
            ('c__GALT_P',     1.0,   'mM'),
    ],
    rules=[
            ('c__GALT_Vmax', 'c__GALT_P/REF_P * GALT_f*c__GALK_Vmax*GALT_vm', 'mole_per_s'),
            ('c__GALT_dm', '((1 dimensionless + c__gal1p_tot/GALT_k_gal1p)*(1 dimensionless + c__udpglc_tot/GALT_k_udpglc + c__udp/GALT_ki_udp + c__utp/GALT_ki_utp)' +
                        '+ (1 dimensionless + c__glc1p_tot/GALT_k_glc1p)*(1 dimensionless + c__udpgal_tot/GALT_k_udpgal) -1 dimensionless)', '-'),
            ('c__GALT_V', 'c__GALT_Vmax/(GALT_k_gal1p*GALT_k_udpglc) * 1 dimensionless/c__GALT_dm', 'mole_per_s_per_mM2'),
            ('c__GALT_Vf', 'c__GALT_V*c__gal1p_tot*c__udpglc_tot', 'mole_per_s'),
            ('c__GALT_Vb', 'c__GALT_V*c__glc1p_tot*c__udpgal_tot/GALT_keq', 'mole_per_s'),
    ],
    formula=("c__gal1p/c__gal1p_tot*c__udpglc/c__udpglc_tot * c__GALT_Vf - c__glc1p/c__glc1p_tot*c__udpgal/c__udpgal_tot * c__GALT_Vb", 'mole_per_s')
)

GALTM1 = ReactionTemplate(
    rid='c__GALTM1',
    name='Galactose-1-phosphate uridyl transferase M1 [c__]',
    equation='c__gal1pM + c__udpglc <-> c__glc1p + c__udpgalM [c__utp, c__udp, c__gal1p, c__udpglcM, c__glc1pM, c__udpgal]',
    # C6H11O9P (-2) + C15H22N2O17P2 (-2) <-> C6H11O9P (-2) + C15H22N2O17P2 (-2)
    localization='c',
    compartments=['c__'],
    pars=[],
    rules=[],
    formula=("c__gal1pM/c__gal1p_tot*c__udpglc/c__udpglc_tot * c__GALT_Vf - c__glc1p/c__glc1p_tot*c__udpgalM/c__udpgal_tot * c__GALT_Vb", 'mole_per_s')
)
GALTM2 = ReactionTemplate(
    rid='c__GALTM2',
    name='Galactose-1-phosphate uridyl transferase M2 [c__]',
    equation='c__gal1p + c__udpglcM <-> c__glc1pM + c__udpgal [c__utp, c__udp, c__gal1pM, c__udpglc, c__glc1p, c__udpgalM]',
    # C6H11O9P (-2) + C15H22N2O17P2 (-2) <-> C6H11O9P (-2) + C15H22N2O17P2 (-2)
    localization='c',
    compartments=['c__'],
    formula=("c__gal1p/c__gal1p_tot*c__udpglcM/c__udpglc_tot * c__GALT_Vf - c__glc1pM/c__glc1p_tot*c__udpgal/c__udpgal_tot * c__GALT_Vb", 'mole_per_s')
)
GALTM3 = ReactionTemplate(
    rid='c__GALTM3',
    name='Galactose-1-phosphate uridyl transferase M3 [c__]',
    equation='c__gal1pM + c__udpglcM <-> c__glc1pM + c__udpgalM [c__utp, c__udp, c__gal1p, c__udpglc, c__glc1p, c__udpgal]',
    # C6H11O9P (-2) + C15H22N2O17P2 (-2) <-> C6H11O9P (-2) + C15H22N2O17P2 (-2)
    localization='c',
    compartments=['c__'],
    formula=("c__gal1pM/c__gal1p_tot*c__udpglcM/c__udpglc_tot * c__GALT_Vf - c__glc1pM/c__glc1p_tot*c__udpgalM/c__udpgal_tot * c__GALT_Vb", 'mole_per_s')
)

#############################################################################################
GALE = ReactionTemplate(
    rid='c__GALE',
    name='UDP-glucose 4-epimerase [c__]',
    equation='c__udpglc <-> c__udpgal [c__udpglcM, c__udpgalM]',
    # C15H22N2O17P2 (-2) <-> C15H22N2O17P2 (-2)
    localization='c',
    compartments=['c__'],
    pars=[
            ('GALE_f',    0.3,   '-'),
            ('GALE_PA',   0.0278, 's'),
            ('GALE_kcat', 36,     'per_s'),
            ('GALE_keq',  0.33,   '-'), 
            ('GALE_k_udpglc', 0.069, 'mM'),
            ('GALE_k_udpgal', 0.3,   'mM'),
            ('c__GALE_P', 1.0,        'mM'),
    ],
    rules=[
            ('c__GALE_Vmax', 'GALE_f*c__GALK_Vmax*GALE_PA*GALE_kcat*c__GALE_P/REF_P', 'mole_per_s'),
            ('c__GALE_dm', '(1 dimensionless + c__udpglc_tot/GALE_k_udpglc + c__udpgal_tot/GALE_k_udpgal)', '-'),
            ('c__GALE_V', 'c__GALE_Vmax/GALE_k_udpglc * 1 dimensionless/c__GALE_dm', 'mole_per_s_per_mM'),
            ('c__GALE_Vf', 'c__GALE_V * c__udpglc_tot', 'mole_per_s'),
            ('c__GALE_Vb', 'c__GALE_V * c__udpgal_tot/GALE_keq', 'mole_per_s'),
    ],
    formula=("c__udpglc/c__udpglc_tot * c__GALE_Vf - c__udpgal/c__udpgal_tot * c__GALE_Vb", 'mole_per_s')
)

GALEM = ReactionTemplate(
    rid='c__GALEM',
    name='UDP-glucose 4-epimerase M [c__]',
    equation='c__udpglcM <-> c__udpgalM [c__udpglc, c__udpgal]',
    # C15H22N2O17P2 (-2) <-> C15H22N2O17P2 (-2)
    localization='c',
    compartments=['c__'],
    formula=("c__udpglcM/c__udpglc_tot * c__GALE_Vf - c__udpgalM/c__udpgal_tot * c__GALE_Vb", 'mole_per_s')
)

#############################################################################################
UGP = ReactionTemplate(
    rid='c__UGP',
    name='UDP-glucose pyrophosphorylase [c__]',
    equation='c__glc1p + c__utp + c__hydron <-> c__udpglc + c__ppi [c__glc1pM, c__udpglcM, c__gal1p, c__gal1pM, c__udpgal, c__udpgalM]',
    # C6H11O9P (-2) + C9H11N2O15P3 (-4) + H (+1) <-> C15H22N2O17P2 (-2) + HO7P2 (-3)
    localization='c',
    compartments=['c__'],
    pars=[
            ('UGP_f',    2000,     '-'),
            ('UGP_keq',   0.45,    '-'),
            ('UGP_k_utp', 0.563,   'mM'),
            ('UGP_k_glc1p', 0.172, 'mM'),
            ('UGP_k_udpglc', 0.049,'mM'),
            ('UGP_k_ppi',    0.166, 'mM'),
            ('UGP_k_gal1p',  5.0,   'mM'),
            ('UGP_k_udpgal', 0.42,  'mM'),
            ('UGP_ki_utp',    0.643, 'mM'),
            ('UGP_ki_udpglc', 0.643,  'mM'),
            ('c__UGP_P',     1.0,     'mM'),
    ],
    rules=[
            ('c__UGP_Vmax', 'UGP_f * c__GALK_Vmax*c__UGP_P/REF_P', 'mole_per_s'),
            ('c__UGP_dm', '((1 dimensionless +c__utp/UGP_k_utp + c__udpglc_tot/UGP_ki_udpglc)*(1 dimensionless + c__glc1p_tot/UGP_k_glc1p + c__gal1p_tot/UGP_k_gal1p)' +
                '+ (1 dimensionless + c__udpglc_tot/UGP_k_udpglc + c__udpgal_tot/UGP_k_udpgal + c__utp/UGP_ki_utp)*(1 dimensionless +c__ppi/UGP_k_ppi) -1 dimensionless)', '-'),
            ('c__UGP_V', 'c__UGP_Vmax/(UGP_k_utp*UGP_k_glc1p) * 1 dimensionless/c__UGP_dm', 'mole_per_s_per_mM2'),
            ('c__UGP_Vf', 'c__UGP_V * c__glc1p_tot*c__utp', 'mole_per_s'),
            ('c__UGP_Vb', 'c__UGP_V * c__udpglc_tot*c__ppi/UGP_keq', 'mole_per_s'),
    ],
    formula=("c__glc1p/c__glc1p_tot * c__UGP_Vf - c__udpglc/c__udpglc_tot*c__UGP_Vb",
             'mole_per_s')
)

UGPM = ReactionTemplate(
    rid='c__UGPM',
    name='UDP-glucose pyrophosphorylase M [c__]',
    equation='c__glc1pM + c__utp + c__hydron <-> c__udpglcM + c__ppi [c__glc1p, c__udpglc, c__gal1p, c__gal1pM, c__udpgal, c__udpgalM]',
    # C6H11O9P (-2) + C9H11N2O15P3 (-4) + H (+1) <-> C15H22N2O17P2 (-2) + HO7P2 (-3)
    localization='c',
    compartments=['c__'],
    pars=[],
    rules=[],
    formula=("c__glc1pM/c__glc1p_tot * c__UGP_Vf - c__udpglcM/c__udpglc_tot*c__UGP_Vb",
             'mole_per_s')
)
#############################################################################################
UGALP = ReactionTemplate(
    rid='c__UGALP',
    name='UDP-galactose pyrophosphorylase [c__]',
    equation='c__gal1p + c__utp + c__hydron <-> c__udpgal + c__ppi [c__glc1p, c__glc1pM, c__udpglc, c__udpglcM, c__gal1pM, c__udpgalM]',
    # C6H11O9P (-2) + C9H11N2O15P3 (-4) + H (+1) <-> C15H22N2O17P2 (-2) + HO7P2 (-3)
    localization='c',
    compartments=['c__'],
    pars=[
            ('UGALP_f', 0.01, '-'),
    ],
    rules=[
             ('c__UGALP_V', 'UGALP_f* c__UGP_Vmax/(UGP_k_utp*UGP_k_gal1p) * 1 dimensionless/c__UGP_dm', 'mole_per_s_per_mM2'),
             ('c__UGALP_Vf', 'c__UGALP_V * c__gal1p_tot*c__utp', 'mole_per_s'),
             ('c__UGALP_Vb', 'c__UGALP_V * c__udpgal_tot*c__ppi/UGP_keq', 'mole_per_s'),
    ],
    formula=(" c__gal1p/c__gal1p_tot * c__UGALP_Vf - c__udpgal/c__udpgal_tot * c__UGALP_Vb",
             'mole_per_s')
)

UGALPM = ReactionTemplate(
    rid='c__UGALPM',
    name='UDP-galactose pyrophosphorylase M [c__]',
    equation='c__gal1pM + c__utp + c__hydron <-> c__udpgalM + c__ppi [c__glc1p, c__glc1pM, c__udpglc, c__udpglcM, c__gal1p, c__udpgal]',
    # C6H11O9P (-2) + C9H11N2O15P3 (-4) + H (+1) <-> C15H22N2O17P2 (-2) + HO7P2 (-3)
    localization='c',
    compartments=['c__'],
    formula=(" c__gal1pM/c__gal1p_tot * c__UGALP_Vf - c__udpgalM/c__udpgal_tot * c__UGALP_Vb",
             'mole_per_s')
)
#############################################################################################
PPASE = ReactionTemplate(
    rid='c__PPASE',
    name='Pyrophosphatase [c__]',
    equation='c__ppi + c__h2o -> 2 c__phos + c__hydron',
    # HO7P2 (-3) + H2O (0) -> 2 HO4P (-2) + H (+1)
    localization='c',
    compartments=['c__'],
    pars=[
            ('PPASE_f', 0.05, '-'),
            ('PPASE_k_ppi', 0.07, 'mM'),
            ('PPASE_n', 4, '-'),
            ('c__PPASE_P', 1, 'mM'),
    ],
    rules=[
            ('c__PPASE_Vmax', 'PPASE_f*c__UGP_Vmax *c__PPASE_P/REF_P', 'mole_per_s'),
    ],
    formula=("c__PPASE_Vmax * c__ppi^PPASE_n/(c__ppi^PPASE_n + PPASE_k_ppi^PPASE_n)",
             'mole_per_s')
)
#############################################################################################
NDKU = ReactionTemplate(
    rid='c__NDKU',
    name='ATP:UDP phosphotransferase [c__]',
    equation='c__atp + c__udp <-> c__adp + c__utp',
    # C10H12N5O13P3 (-4) + C9H11N2O12P2 (-3) <-> C10H12N5O10P2 (-3) + C9H11N2O15P3 (-3)
    localization='c',
    compartments=['c__'],
    pars=[
            ('NDKU_f',    2,     '-'),
            ('NDKU_keq',  1,     '-'),
            ('NDKU_k_atp', 1.33, 'mM'),
            ('NDKU_k_adp', 0.042, 'mM'),
            ('NDKU_k_utp', 27,   'mM'),
            ('NDKU_k_udp', 0.19, 'mM'),
            ('c__NDKU_P',  1.0,  'mM'),
    ],
    rules=[
            ('c__NDKU_Vmax', 'NDKU_f * c__UGP_Vmax * c__NDKU_P/REF_P', 'mole_per_s'),
    ],
    formula=("c__NDKU_Vmax/NDKU_k_atp/NDKU_k_udp *(c__atp*c__udp - c__adp*c__utp/NDKU_keq)/" +
                        "((1 dimensionless +c__atp/NDKU_k_atp)*(1 dimensionless +c__udp/NDKU_k_udp) + (1 dimensionless +c__adp/NDKU_k_adp)*(1 dimensionless+c__utp/NDKU_k_utp) -1 dimensionless)",
             'mole_per_s')
)
#############################################################################################
PGM1 = ReactionTemplate(
    rid='c__PGM1',
    name='Phosphoglucomutase-1 [c__]',
    equation='c__glc1p <-> c__glc6p [c__glc1pM, c__glc6pM]',
    # C6H11O9P (-2) <-> C6H11O9P (-2)
    localization='c',
    compartments=['c__'],
    pars=[
            ('PGM1_f',   50.0,   '-'),
            ('PGM1_keq', 10.0,   '-'),
            ('PGM1_k_glc6p', 0.67,  'mM'),
            ('PGM1_k_glc1p', 0.045, 'mM'),
            ('c__PGM1_P',    1.0,   'mM'),
    ],
    rules=[
            ('c__PGM1_Vmax', 'PGM1_f * c__GALK_Vmax*c__PGM1_P/REF_P', 'mole_per_s'),
            ('c__PGM1_dm', '(1 dimensionless + c__glc1p_tot/PGM1_k_glc1p + c__glc6p_tot/PGM1_k_glc6p)', '-'),
            ('c__PGM1_V', 'c__PGM1_Vmax/PGM1_k_glc1p * 1 dimensionless/c__PGM1_dm', 'mole_per_s_per_mM'),
            ('c__PGM1_Vf', 'c__PGM1_V * c__glc1p_tot', 'mole_per_s'),
            ('c__PGM1_Vb', 'c__PGM1_V * c__glc6p_tot/PGM1_keq', 'mole_per_s'),
    ],
    formula=("c__glc1p/c__glc1p_tot * c__PGM1_Vf - c__glc6p/c__glc6p_tot * c__PGM1_Vb",
             'mole_per_s')
)

PGM1M = ReactionTemplate(
    rid='c__PGM1M',
    name='Phosphoglucomutase-1 M [c__]',
    equation='c__glc1pM <-> c__glc6pM  [c__glc1p, c__glc6p]',
    # C6H11O9P (-2) <-> C6H11O9P (-2)
    localization='c',
    compartments=['c__'],
    formula=("c__glc1pM/c__glc1p_tot * c__PGM1_Vf - c__glc6pM/c__glc6p_tot * c__PGM1_Vb",
             'mole_per_s')
)
#############################################################################################
GLY = ReactionTemplate(
    rid='c__GLY',
    name='Glycolysis [c__]',
    equation='c__glc6p + 5 c__o2 <-> c__phos + 6 c__co2 + 5 c__h2o',
    # C6H11O9P (-2) + 5 O2 <-> HO4P (-2) + 6 CO2 (0) + 5 H2O (0)
    localization='c',
    compartments=['c__'],
    pars=[
            ('GLY_f',    0.1,    '-'),
            ('GLY_k_glc6p', 0.12, 'mM'),
            ('GLY_k_p',   0.2,    'mM'),
            ('c__GLY_P',     1.0,    'mM'),
    ],
    rules=[
            ('c__GLY_Vmax', 'GLY_f * c__PGM1_Vmax*c__GLY_P/REF_P', 'mole_per_s'),
            
    ],
    formula=("c__GLY_Vmax/GLY_k_glc6p *(c__glc6p - GLY_k_glc6p) * c__phos/(c__phos + GLY_k_p)",
             'mole_per_s')
)

GLYM = ReactionTemplate(
    rid='c__GLYM',
    name='Glycolysis M [c__]',
    equation='c__glc6pM + 5 c__o2 -> c__phos + 6 c__co2 + 5 c__h2o',
    # C6H11O9P (-2) + 5 O2 <-> HO4P (-2) + 6 CO2 (0) + 5 H2O (0)
    #
    localization='c',
    compartments=['c__'],
    formula=("c__GLY_Vmax/GLY_k_glc6p * c__glc6pM * c__phos/(c__phos + GLY_k_p)", 'mole_per_s')
)
#############################################################################################
GTFGAL = ReactionTemplate(
    rid='c__GTFGAL',
    name='Glycosyltransferase galactose [c__]',
    equation='c__udpgal + c__acpt -> c__udp + c__acptgal + c__hydron [c__udpgalM]',
    # C15H22N2O17P2 (-2) + H2R (0) -> C9H11N2O12P2 (-3) + C6H12O6R (0) + H (+1)
    localization='c',
    compartments=['c__'],
    pars=[
            ('GTF_f',    2E-2,   '-'),
            ('GTF_k_udpgal', 0.1, 'mM'),
            ('GTF_k_udpglc', 0.1, 'mM'),
            ('c__GTF_P',     1.0,    'mM'),
    ],
    rules=[
            ('c__GTF_Vmax', 'GTF_f * c__GALK_Vmax * c__GTF_P/REF_P', 'mole_per_s'),
            ('c__GTFGAL_Vf', 'c__GTF_Vmax/GTF_k_udpgal * c__udpgal_tot/(1 dimensionless + c__udpgal_tot/GTF_k_udpgal)', 'mole_per_s'),
    ],
    formula=("c__udpgal/c__udpgal_tot * c__GTFGAL_Vf", 'mole_per_s')
)
GTFGALM = ReactionTemplate(
    rid='c__GTFGALM',
    name='Glycosyltransferase galactose M [c__]',
    equation='c__udpgalM + c__acpt -> c__udp + c__acptgalM + c__hydron [c__udpgal]',
    # C15H22N2O17P2 (-2) + H2R (0) -> C9H11N2O12P2 (-3) + C6H12O6R (0) + H (+1)
    localization='c',
    compartments=['c__'],
    formula=("c__udpgalM/c__udpgal_tot * c__GTFGAL_Vf", 'mole_per_s')
)

GTFGLC = ReactionTemplate(
    rid='c__GTFGLC',
    name='Glycosyltransferase glucose [c__]',
    equation='c__udpglc + c__acpt -> c__udp + c__acptglc + c__hydron [c__udpglcM]',
    # C15H22N2O17P2 (-2) + H2R (0) -> C9H11N2O12P2 (-3) + C6H12O6R (0) + H (+1)
    localization='c',
    compartments=['c__'],
    rules=[
             ('c__GTFGLC_Vf', '0.0 dimensionless * c__GTF_Vmax/GTF_k_udpglc * c__udpglc_tot/(1 dimensionless + c__udpglc_tot/GTF_k_udpglc)', 'mole_per_s'),
    ],
    formula=("c__udpglc/c__udpglc_tot * c__GTFGLC_Vf", 'mole_per_s')
)

GTFGLCM = ReactionTemplate(
    rid='c__GTFGLCM',
    name='Glycosyltransferase glucose M [c__]',
    equation='c__udpglcM + c__acpt -> c__udp + c__acptglcM + c__hydron [c__udpglc]',
    # C15H22N2O17P2 (-2) + H2R (0) -> C9H11N2O12P2 (-3) + C6H12O6R (0) + H (+1)
    localization='c',
    compartments=['c__'],
    pars=[],
    rules=[],
    formula=("c__udpglcM/c__udpglc_tot * c__GTFGLC_Vf", 'mole_per_s')
)

#############################################################################################
#    TRANSPORTERS
#############################################################################################
# create all single transporters
H2OTM = ReactionTemplate(
    rid='e__H2OTM',
    name='H2O M transport [e__]',
    equation='e__h2oM <-> h__h2oM',
    # H2O (0) <-> H2O (0)
    localization='m',
    compartments=['c__', 'h__', 'e__'],
    pars=[
            ('H2OT_f', 8.0, 'mole_per_s'),
            ('H2OT_k',  1.0, 'mM'),
    ],
    rules=[
            ('c__H2OT_Vmax', 'H2OT_f/Nf * c__scale', 'mole_per_s'),
    ],
    formula=('c__H2OT_Vmax/H2OT_k * (e__h2oM - h__h2oM)', 'mole_per_s')
)

#############################################################################################
GLUT2_GAL = ReactionTemplate(
    rid='e__GLUT2_GAL',
    name='galactose transport [e__]',
    equation='e__gal <-> c__gal [e__galM, c__galM]',
    # C6H1206 (0) <-> C6H1206 (0)
    localization='m',
    compartments=['c__', 'e__'],
    pars=[
            ('GLUT2_f',    17.0,   'mole_per_s'),
            ('GLUT2_k_gal', 27.8, 'mM'),
            ('c__GLUT2_P',   1.0, 'mM'),
    ],
    rules=[
            ('c__GLUT2_Vmax', 'GLUT2_f/Nf * c__scale * c__GLUT2_P/REF_P', 'mole_per_s'),
            ('c__GLUT2_V', 'c__GLUT2_Vmax/GLUT2_k_gal * 1 dimensionless/(1 dimensionless + e__gal_tot/GLUT2_k_gal + c__gal_tot/GLUT2_k_gal)', 'mole_per_s_per_mM'),
    ],
    formula=('c__GLUT2_V * (e__gal - c__gal)', 'mole_per_s')
)

GLUT2_GALM = ReactionTemplate(
    rid='e__GLUT2_GALM',
    name='galactose transport M [e__]',
    equation='e__galM <-> c__galM [e__gal, c__gal]',
    # C6H1206 (0) <-> C6H1206 (0)
    localization='m',
    compartments=['c__', 'e__'],
    formula=('c__GLUT2_V * (e__galM - c__galM)', 'mole_per_s')
)
