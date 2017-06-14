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


def getunzipped(model_id, output_dir):
    """ Get zip

    :param theurl:
    :param thedir:
    :return:
    """
    # target address
    url = URL_ZIP.format(model_id)
    print(url)

    # download file
    name = os.path.join(output_dir, '{}.zip'.format(model_id))

    # Download the file from `url` and save it locally under `file_name`:
    with urllib.request.urlopen(url) as response, open(name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)






    # extract zip file
    try:
        z = zipfile.ZipFile(name)
    except zipfile.error as e:
        print("Bad zipfile (from %r): %s" % (url, e))
        return

    zip_dir = os.path.join(output_dir, model_id)

    for n in z.namelist():
        dest = os.path.join(zip_dir, n)
        destdir = os.path.dirname(dest)
        if not os.path.isdir(destdir):
            os.makedirs(destdir)
        data = z.read(n)
        f = open(dest, 'w')
        f.write(data)
        f.close()
        z.close()
        os.unlink(name)


if __name__ == "__main__":
    model_ids = xpp_model_ids()
    from pprint import pprint
    pprint(model_ids)
    print(len(model_ids))

    model_id = 84606
    getunzipped(model_id=model_id, output_dir='.')
