"""
Simulations of the whole-body glucose model.
"""
from pylimax.models.glucose_pkpd.model_setup import *


def check_balances(s):
    # check the flow balance on the liver
    print('------------------')
    print('Liver Difference')
    print('------------------')
    inflow = s.Flow_gu_li_glc + s.Flow_sp_li_glc + s.Flow_pa_li_glc + s.Flow_ar_li_glc
    outflow = s.Flow_li_ve_glc
    diff = inflow - outflow
    df = pd.DataFrame({'inflow': inflow, 'outflow': outflow, 'diff': diff}, columns=["inflow", "outflow", "diff"])
    print(df)

    print('------------------')
    print('Venous Difference')
    print('------------------')
    inflow = s.Flow_mu_ve_glc + s.Flow_ad_ve_glc + s.Flow_br_ve_glc + s.Flow_he_ve_glc + s.Flow_re_ve_glc + s.Flow_ki_ve_glc + s.Flow_li_ve_glc
    outflow = s.Flow_ve_lu_glc
    diff = inflow - outflow
    df = pd.DataFrame({'inflow': inflow, 'outflow': outflow, 'diff': diff}, columns=["inflow", "outflow", "diff"])
    print(df)

    print('------------------')
    print('Arterial Difference')
    print('------------------')
    inflow = s.Flow_lu_ar_glc
    outflow = s.Flow_ar_mu_glc + s.Flow_ar_ad_glc + s.Flow_ar_br_glc + s.Flow_ar_he_glc + s.Flow_ar_re_glc + s.Flow_ar_ki_glc + s.Flow_ar_li_glc + s.Flow_ar_pa_glc + s.Flow_ar_sp_glc + s.Flow_ar_gu_glc
    diff = inflow - outflow
    df = pd.DataFrame({'inflow': inflow, 'outflow': outflow, 'diff': diff}, columns=["inflow", "outflow", "diff"])
    print(df)

    print("lung:", r.FQlu)
    print("all:", r.FQmu+r.FQad+r.FQbr+r.FQhe+r.FQre+r.FQki+r.FQh)


def check_fractions(s):
    """ Check the volume and blood flow fractions in the model.

    :param s:
    :return:
    """
    flow_fractions = []
    for key in r.model.getGlobalParameterIds():
        if key.startswith('FQ'):
            ax.plot(s.time, s[key])
            var_range(s, key, '-')
            flow_fractions.append(s[key][0])
    print(f"Sum FQ = {np.sum(flow_fractions)}")

    print('-' * 80)
    vol_fractions = []
    for key in r.model.getGlobalParameterIds():
        if key.startswith('FV'):
            ax.plot(s.time, s[key])
            var_range(s, key, '-')
            vol_fractions.append(s[key][0])
    print(f"Sum VQ = {np.sum(vol_fractions)}")


def print_var_range(key):
    """ Prints ranges for given substance in the different tissues."""
    for key in r.model.getFloatingSpeciesIds():
        if key.endswith('glc'):
            skey = f'[{key}]'
            var_range(s, skey, 'mM')


# ------------------------------------------------------------------------------------------------------------
# Simulations
# ------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    save_figs = False

    r = load_model()

    # -------------------------------
    # 1. Check reference simulation
    # -------------------------------
    r.resetToOrigin()

    set_initial_concentrations(r=r, sid="glc", value=5)  # [mM]

    # r.setValue('BR__GLC2LAC_Vmax', 2000)
    # r.setValue('LI__LAC2GLC_Vmax', 200)
    s_pre = simulate(r, start=0, end=0.1, steps=10)  # pre-simulation

    s = simulate(r, start=0, end=24, steps=800)


    f1 = plot_overview(r, s)
    if save_figs:
        save_glc_fig(f1, "basal_overview")
    plot_body_concentrations(r, s)
    # plot_body_fluxes(r, s)
    plt.show()


    def plot_misc(r, s):
        """ Overview plot of whole-body glucose metabolism"""
        s_iter = s
        if not isinstance(s_iter, (list, dict)):
            s_iter = [s_iter]
        if isinstance(s_iter, dict):
            s_iter = s_iter.values()

        f, ((ax1, ax2, ax3, ax4), (ax5, ax6, ax7, ax8)) = plt.subplots(2, 4, figsize=(14, 8))
        f.subplots_adjust(wspace=.3, hspace=.3)
        axes = (ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8)

        for ax in (ax1, ax2, ax3, ax4):
            ax.set_ylabel('Concentration [mmole/l]')
        for ax in (ax5, ax6, ax7, ax8):
            ax.set_ylabel('Flux [µmole/min/kg]')
            # ax.set_ylim(0, 20)

        for s in s_iter:
            # concentrations
            ax1.set_title("glucose (liver)")
            ax1.plot(s.time, s.Cve_glc, color="darkgrey", linestyle="-", label="glucose (venous)")
            ax1.plot(s.time, s.Car_glc, color="darkgrey", linestyle="-", label="glucose (arterial)")
            ax1.plot(s.time, s.Cli_blood_glc, color="black", linestyle="--", label="glucose (liver blood)")
            ax1.plot(s.time, s.LI__Cext_glc, color="black", linestyle="-", label="glucose (liver tissue)")

            ax2.set_title("lactate (liver)")
            ax2.plot(s.time, s.Cve_lac, color="darkgrey", linestyle="-", label="lactate (venous)")
            ax2.plot(s.time, s.Car_lac, color="darkgrey", linestyle="-", label="lactate (arterial)")
            ax2.plot(s.time, s.Cli_blood_lac, color="black", linestyle="--", label="lactate (liver blood)")
            ax2.plot(s.time, s.LI__Cext_lac, color="black", linestyle="-", label="lactate (liver tissue)")

            ax3.set_title("glucose (tissues)")
            ax3.plot(s.time, s.Cbr_blood_glc, color="black", linestyle="--", label="glucose (brain blood)")
            ax3.plot(s.time, s.BR__Cext_glc, color="black", linestyle="-", label="glucose (brain tissue)")
            ax3.plot(s.time, s.RBCVE__glcRBC/r.RBCVE__Vrbc, color="blue", linestyle="-", label="glucose (RBC ve)")
            ax3.plot(s.time, s.RBCAR__glcRBC / r.RBCAR__Vrbc, color="blue", linestyle="-", label="glucose (RBC ve)")


            ax4.set_title("lactate (tissues)")
            ax4.plot(s.time, s.Cbr_blood_lac, color="black", linestyle="--", label="lactate (brain blood)")
            ax4.plot(s.time, s.BR__Cext_lac, color="black", linestyle="-", label="lactate (brain tissue)")
            ax4.plot(s.time, s.RBCVE__lacRBC / r.RBCVE__Vrbc, color="blue", linestyle="-", label="lactate (RBC ve)")
            ax4.plot(s.time, s.RBCAR__lacRBC / r.RBCAR__Vrbc, color="blue", linestyle="-", label="lactate (RBC ar)")

            # fluxes
            f_flux = 1.0/r.BW*1000/60  # [mmole/h] -> [µmole/min/kg]
            ax5.set_title("Hepatic glucose production")
            ax5.plot(s.time, s.LI__LAC2GLC*f_flux)
            ax5.plot(s.time, -s.LI__GLCIM*f_flux)

            ax6.set_title("Hepatic lactate consumption")
            ax6.plot(s.time, s.LI__LACIM*f_flux)

            ax7.set_title("Tissue glucose consumption")
            ax7.plot(s.time, s.BR__GLC2LAC*f_flux)
            ax7.plot(s.time, s.BR__GLCIM*f_flux)
            ax7.plot(s.time, s.RBCVE__GLCIM * f_flux)
            ax7.plot(s.time, s.RBCAR__GLCIM * f_flux)

            ax8.set_title("Tissue lactate production")
            ax8.plot(s.time, -s.BR__LACIM*f_flux)
            ax8.plot(s.time, s.RBCVE__LACEX * f_flux)
            ax8.plot(s.time, s.RBCAR__LACEX * f_flux)

        for ax in axes:
            ax.legend()
            ax.set_xlabel('time [h]')
            ylim = ax.get_ylim()
            if ylim[0] > 0:
                ax.set_ylim(bottom=0)
            ax.set_ylim(top=1.1 * (ax.get_ylim()[1]))
        return f


    f = plot_misc(r, s)
    # save_glc_fig(f, "wholebody_glucose")
    plt.show()

