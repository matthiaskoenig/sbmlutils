"""
Combine Archive helper functions based on libcombine.
"""
from __future__ import absolute_import, print_function
import os
import warnings
import zipfile
try:
    import libcombine
except ImportError:
    import tecombine as libcombine
import pprint


from collections import namedtuple

Entry = namedtuple('Entry', 'location format master description creator')


class Entry(object):
    """ Helper class to store content to create an OmexEntry."""

    def __init__(self, location, format, master=False, description=None, creators=None):
        """ Create entry from information.

        :param location:
        :param format:
        :param master:
        :param description:
        :param creators:
        """
        self.location = location
        self.format = format
        self.master = master
        self.description = description
        self.creators = creators

    def __str__(self):
        if self.master:
            return '<*master* Entry {} | {}>'.format(self.master, self.location, self.format)
        else:
            return '<Entry {} | {}>'.format(self.master, self.location, self.format)


def combineArchiveFromEntries(omexPath, entries, workingDir):
    """ Creates combine archive from given entries.

    Overwrites existing combine archive at omexPath.

    :param entries:
    :param workingDir:
    :return:
    """
    if not os.path.exists(workingDir):
        raise IOError("Working directory does not exist: {}".format(workingDir))

    # delete the old omex file
    if os.path.exists(omexPath):
        warnings.warn("Combine archive is overwritten: {}".format(omexPath))
        os.remove(omexPath)

    # timestamp
    time_now = libcombine.OmexDescription.getCurrentDateAndTime()

    archive = libcombine.CombineArchive()
    for entry in entries:
        location = entry.location
        path = os.path.join(workingDir, location)
        if not os.path.exists(path):
            raise IOError("File does not exist at given location: {}".format(path))

        archive.addFile(path, location, entry.format, entry.master)

        if entry.description or entry.creators:
            omex_d = libcombine.OmexDescription()
            omex_d.setAbout(location)
            omex_d.setCreated(time_now)

            if entry.description:
                omex_d.setDescription(entry.description)

            if entry.creators:
                for c in entry.creators:
                    creator = libcombine.VCard()
                    creator.setFamilyName(c.get("familyName", ""))
                    creator.setGivenName(c.get("givenName", ""))
                    creator.setEmail(c.get("email", ""))
                    creator.setOrganization(c.get("organisation", ""))
                    omex_d.addCreator(creator)

            archive.addMetadata(location, omex_d)

    archive.writeToFile(omexPath)
    archive.cleanUp()
    print('Archive created:', omexPath)


def addEntriesToCombineArchive(omexPath, entries, workingDir):
    """ Adds entries to

    :param omexPath:
    :param entries: iteratable of Entry
    :param workingDir: locations are relative to working dir
    :return:
    """

    raise NotImplementedError


def extractCombineArchive(omexPath, directory, method="zip"):
    """ Extracts combine archive at given path to directory.

    The zip method extracts all entries in the zip, the omex method
    only extracts the entries listed in the manifest.
    In some archives not all content is listed in the manifest.

    :param omexPath:
    :param directory:
    :param method: method to extract content, either 'zip' or 'omex'
    :return:
    """
    if method not in ["zip", "omex"]:
        raise ValueError("Method is not supported: {}".format(method))

    if method is "zip":
        zip_ref = zipfile.ZipFile(omexPath, 'r')
        zip_ref.extractall(directory)
        zip_ref.close()

    elif method is "omex":
        omex = libcombine.CombineArchive()
        if omex.initializeFromArchive(omexPath) is None:
            raise IOError("Invalid Combine Archive: {}", omexPath)

        for i in range(omex.getNumEntries()):
            entry = omex.getEntry(i)
            location = entry.getLocation()
            filename = os.path.join(directory, location)
            omex.extractEntry(location, filename)

        omex.cleanUp()


def getLocationsByFormat(omexPath, formatKey=None):
    """ Returns locations to files with given format in the archive.

    Uses the libcombine KnownFormats for formatKey, e.g., 'sed-ml' or 'sbml'.
    Files which have a master=True have higher priority and are listed first.

    :param omexPath:
    :param formatKey:
    :return:
    """
    if not formatKey:
        raise ValueError("Format must be specified.")

    locations_master = []
    locations = []

    omex = libcombine.CombineArchive()
    if omex.initializeFromArchive(omexPath) is None:
        raise IOError("Invalid Combine Archive: {}", omexPath)

    for i in range(omex.getNumEntries()):
        entry = omex.getEntry(i)
        format = entry.getFormat()
        master = entry.getMaster()
        if libcombine.KnownFormats.isFormat(formatKey, format):
            loc = entry.getLocation()
            if (master is None) or (master is False):
                locations.append(loc)
            else:
                locations_master.append(loc)
    omex.cleanUp()

    return locations_master + locations


def listContents(omexPath, method="omex"):
    """ Returns list of contents of the combine archive.

    :param omexPath:
    :param method: method to extract content, only 'omex' supported
    :return: list of contents
    """
    if method not in ["omex"]:
        raise ValueError("Method is not supported: {}".format(method))

    contents = []
    omex = libcombine.CombineArchive()
    if omex.initializeFromArchive(omexPath) is None:
        raise IOError("Invalid Combine Archive: {}", omexPath)

    for i in range(omex.getNumEntries()):
        entry = omex.getEntry(i)
        location = entry.getLocation()
        format = entry.getFormat()
        master = entry.getMaster()
        info = None
        try:
            info = omex.extractEntryToString(location)
        except:
            pass

        contents.append([i, location, format, master, info])

    omex.cleanUp()

    return contents


def printContents(omexPath):
    """ Prints contents of archive.

    :param omexPath:
    :return:
    """
    pprint.pprint(listContents(omexPath))
