"""
Download models from ModelDB
"""
from __future__ import print_function, absolute_import
import os
import urllib
import zipfile
import re

from bs4 import BeautifulSoup
import requests
import urllib.request
import shutil
import warnings

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

    name = os.path.join(output_dir, '{}.zip'.format(model_id))
    print('Extracting:', model_id)
    # extract zip file
    try:
        z = zipfile.ZipFile(name)
    except zipfile.error as e:
        print("Bad zipfile (from %r): %s" % (url, e))
        return []

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
            download_model_zip(model_id=model_id, output_dir='.')

        # extract ode files
        if model_id in [62676]:
            # bad zip files, error reported
            continue
        ode_files = unzip_odes(model_id=model_id, output_dir='.')
        ode_all.extend(ode_files)
    return ode_all


if __name__ == "__main__":
    # ode_all = get_models(download=True)

    # get all ode files
    ode_all = []
    xpp_path = "."

    for root, dirnames, filenames in os.walk(xpp_path):
        for f in filenames:
            if f.endswith('.ode'):
                f_path = os.path.join(root, f)
                ode_all.append(f_path)

    # from pprint import pprint
    # pprint(sorted(ode_all))

    # create the sbml files
    import traceback
    import sys
    from sbmlutils.converters import xpp
    out_dir = './sbml'
    Nall = len(ode_all)
    Nfail = 0
    for k, xpp_file in enumerate(sorted(ode_all)):

        # convert xpp to sbml
        basename = os.path.basename(xpp_file)
        sbml_file = os.path.join(out_dir, "{}.xml".format(basename))
        try:
            print('[{}]'.format(k))
            xpp.xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file)
        except:
            print()
            traceback.print_exc(file=sys.stdout)
            print()
            Nfail += 1
    print('*'*80)
    print('SUCCESS: {}/{}={:.2f}'.format((Nall-Nfail), Nall, 1.0*(Nall-Nfail)/Nall))
    print('*' * 80)

