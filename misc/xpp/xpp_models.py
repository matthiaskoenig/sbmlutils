"""
Download models from ModelDB
"""
import os
import urllib
import zipfile
import re

from bs4 import BeautifulSoup
import requests
import urllib.request
import shutil
import warnings
import traceback
import sys
from sbmlutils import validation
from sbmlutils.converters import xpp
import roadrunner
import numpy as np
from matplotlib import pyplot as plt

URL_ZIP = "https://senselab.med.yale.edu/modeldb/eavBinDown.cshtml?o={}&a=23&mime=application/zip"

def xpp_model_ids():
    """ Find the xpp models on the xpp model page.

    :return:
    """
    r = requests.get("https://senselab.med.yale.edu/modeldb/ModelList.cshtml?id=33977&celldescr=&allsimu=")
    data = r.text
    soup = BeautifulSoup(data)
    model_ids = []
    for link in soup.find_all('a'):
        href = link.get('href')
        groups = re.findall('model=(\d+)', href)
        if len(groups) > 0:
            model_ids.append(groups[0])
    return model_ids


def download_model_zip(model_id, output_dir):
    """ Get zip

    :param theurl:
    :param thedir:
    :return: zip filename
    """
    # target address
    url = URL_ZIP.format(model_id)

    # download file
    file_name = os.path.join(output_dir, '{}.zip'.format(model_id))

    # Download the file from `url` and save it locally under `file_name`:
    print('Downloading', url)
    with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    return file_name


def unzip_odes(model_id, output_dir):
    """ Unzip the ode files for the given model_id.

    :param model_id:
    :param output_dir:
    :return: list of ode files
    """

    name = os.path.join(output_dir, f'{model_id}.zip')
    print('Extracting:', model_id)

    # extract zip file
    z = zipfile.ZipFile(name)
    zip_dir = os.path.join(output_dir, str(model_id))

    ode_files = []

    for n in z.namelist():
        # only extract the xpp ode files
        if n.endswith('.ode'):
            print('\t', n)
            try:
                z.extract(n, path=zip_dir)
                ode_files.append(os.path.join(zip_dir, n))
            except zipfile.BadZipfile as e:
                warnings.warn('BadZipFile: {}'.format(model_id))
                warnings.warn(e)

    return ode_files


def get_models(download=True):
    """ Extract models

    :param download: download the zip files.
    :return: list of all ode files
    """
    # get model ids from webpage
    model_ids = xpp_model_ids()
    print('Number xpp models:', len(model_ids))

    ode_all = []
    for model_id in model_ids:
        if download:
            # download zip files
            download_model_zip(model_id=model_id, output_dir='')

        # extract ode files
        if model_id in [62676]:
            # bad zip files, error reported
            continue
        ode_files = unzip_odes(model_id=model_id, output_dir='')
        ode_all.extend(ode_files)
    return ode_all


def simulate(sbml_file):
    """ Simulate given SBML file.
    :param sbml_file:
    :return:
    """
    print("SIMULATING SBML FILE")

    # tests simulation
    r = roadrunner.RoadRunner(sbml_file)
    s = r.simulate(start=0, end=1000, steps=100)

    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14, 7))
    axes = (ax1, ax2)

    for ax in axes:
        for sid in r.timeCourseSelections[1:]:
            ax.plot(s['time'], s[sid], label=sid)
    ax2.set_yscale('log')
    for ax in axes:
        ax.set_ylabel('Value [?]')
        ax.set_xlabel('Time [?]')
        ax.legend()

    fig.savefig("{}.png".format(sbml_file), bbox_inches='tight')


if __name__ == "__main__":

    # download and unzip all sbml files
    # ode_all = get_models(download=True)

    # get all ode files
    ode_all = []
    xpp_path = ""
    for root, dirnames, filenames in os.walk(xpp_path):
        for f in filenames:
            if f.endswith('.ode'):
                f_path = os.path.join(root, f)
                ode_all.append(f_path)

    # create the sbml files
    out_dir = 'sbml'
    N = len(ode_all)
    Nfail = 0
    force_lower = True
    results = []
    debug, show_errors = False, False

    # tests single model
    # ode_all = ["./87762/Neuron_KATP/NeuronKATP_Stoch.ode"]
    # debug, show_errors = True, True

    for k, xpp_file in enumerate(sorted(ode_all)):

        # convert xpp to sbml
        basename = os.path.basename(xpp_file)
        sbml_file = os.path.join(out_dir, "{}.xml".format(basename))
        try:
            print('[{}]'.format(k))
            xpp.xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file, force_lower=force_lower, validate=False, debug=debug)
            success = True
            Nall, Nerr, Nwarn = validation.check_sbml(sbml_file, name=None, ucheck=False, log_errors=show_errors)
            valid = (Nerr == 0)
            simulates = False
            if valid:
                try:
                    simulate(sbml_file)
                    simulates = True
                except Exception:
                    # simulation exception
                    simulates = False
                    print()
                    traceback.print_exc(file=sys.stdout)
                    print()

        except Exception:
            print()
            traceback.print_exc(file=sys.stdout)
            print()
            success = False
            valid = np.nan
            simulates = np.nan
            Nall, Nerr, Nwarn = np.nan, np.nan, np.nan

            Nfail += 1
        results.append([xpp_file, success, valid, simulates, Nall, Nerr, Nwarn])

    # create report

    import pandas as pd
    df = pd.DataFrame(data=results, columns=['xpp_file', 'success', 'valid', 'simulates', 'Nall', 'Nerr', 'Nwarn'])


    if force_lower:
        csv_file = "xpp_results_lower.tsv"
    else:
        csv_file = "xpp_results.tsv"
    df.to_csv(csv_file, sep="\t")


    print('*'*80)
    print('CONVERTED: {}/{}={:.2f}'.format((N-Nfail), N, 1.0*(N-Nfail)/N))
    Nvalid = np.nansum(df.valid)
    print('VALID: {}/{}={:.2f}'.format(Nvalid, N, 1.0 * Nvalid / N))
    Nsimulates = np.nansum(df.simulates)
    print('SIMULATES: {}/{}={:.2f}'.format(Nsimulates, N, 1.0 * Nsimulates / N))
    print('*' * 80)

