# Copyright(c) 2015 Association of Universities for Research in Astronomy, Inc.
# by James E.H. Turner.

import pyfits

from .. import config
from .mapio import NDMapIO


def load_common_meta(filename):

    return pyfits.getheader(str(filename))


def load_array_meta(filename, index):

    # This should probably have an optional header
    return pyfits.getheader(str(filename), index)


def load_array(filename, index):

    # Treat any int (flags) array as unsigned for the appropriate BZERO/BSCALE
    # (to avoid scaling int16 DQ to float32).
    return pyfits.getdata(str(filename), index, uint=True)


def save_array(filename, index, data, meta=None):

    # Convert the inputs to a PyFITS HDU:
    hdr = pyfits.Header(meta) if meta else None
    hdu = pyfits.ImageHDU(data=data, header=hdr, uint=True)

    # Open & parse the existing file:
    hdulist = pyfits.open(str(filename), mode='update', memmap=True, uint=True)

    # Overwrite or append our new HDU at the specified index, producing an
    # error if it doesn't already exist and isn't the next one.
    narr = len(hdulist)
    if index == narr:
        hdulist.append(hdu)
    elif index < narr:
        hdulist[index] = hdu
    else:
        raise IndexError('index %d is out of range for %s' % \
                         (index, str(filename)))

    hdulist.close()


def map_file(filename):

    hdulist = pyfits.open(str(filename), mode='readonly')

    # A dict of empty lists to sort recognized extensions into:
    idx_dict = {'data' : [], 'uncertainty' : [], 'flags' : [], 'undef' : []}

    # Sort any FITS image extensions by EXTNAME into SCI/VAR/DQ lists
    # (remembering the original MEF index for later I/O):
    have_names = False
    idx = 0
    for hdu in hdulist:

        # Ignore any non-image extensions (NB. any data in a FITS primary
        # header must be an image array according to the std & PyFITS docs):
        if (isinstance(hdu, pyfits.ImageHDU) or idx==0) and hdu.size > 0:

            # The name/ver attributes are semi-documented but seem to be
            # part of the public API now. The name seems to default to ''
            # when undefined but the following would also work for None:
            if hdu.name and idx > 0:  # ignore 'PRIMARY'
                have_names = True

            if hdu.name == config['data_name']:
                idx_dict['data'].append(idx)

            elif hdu.name == config['uncertainty_name']:
                idx_dict['uncertainty'].append(idx)

            elif hdu.name == config['flags_name']:
                idx_dict['flags'].append(idx)

            elif not hdu.name or idx == 0:  # ignore 'PRIMARY'
                idx_dict['undef'].append(idx)

            # else:
            #     ignore any extensions with unrecognized names

            # print idx_dict

        idx += 1

    # If there are no named image extensions, treat the unnamed ones as our
    # "data" (SCI) arrays (otherwise ignore them):
    if not have_names:
        idx_dict['data'] = idx_dict['undef']

    # List existing data (SCI) array extension numbers for reference:
    extvers = [hdulist[idx].ver for idx in idx_dict['data']]

    # Create the NDLater instances. Since the main data array is mandatory,
    # we just ignore any uncertainty (VAR) or flags (DQ) extensions without a
    # corresponding data (SCI) array and loop over the latter:
    lastver = 0
    maplist = []
    for data_idx in idx_dict['data']:

        data_hdu = hdulist[data_idx]

        # Give any unnumbered SCI extensions the next available EXTVER after
        # the last one used:
        if data_hdu.ver < 1:  # seems to default to -1; also works for None
            thisver = lastver + 1
            while thisver in extvers:
                thisver += 1
            data_hdu.ver = thisver
            uncert_idx = None
            flags_idx = None

        # Otherwise, if the EXTVER was defined to begin with, look for
        # associated uncertainty & flags (VAR/DQ) extensions:
        else:
            # Find uncertainty & flags HDUs matching this EXTVER:
            uncert_idx = None
            for idx in idx_dict['uncertainty']:
                hdu = hdulist[idx]
                if hdu.ver == data_hdu.ver:
                    uncert_idx = idx
                    break

            flags_idx = None
            for idx in idx_dict['flags']:
                hdu = hdulist[idx]
                if hdu.ver == data_hdu.ver:
                    flags_idx = idx
                    break

        lastver = data_hdu.ver

        # Instantiate the NDMapIO instance, recording the original FITS
        # extension indices and the group extver (== data extver).
        maplist.append(NDMapIO(filename, group_id=data_hdu.ver,
            data_idx=data_idx, uncertainty_idx=uncert_idx, \
            flags_idx=flags_idx))

    # We don't keep the file open continually, since it may get updated later
    # by IRAF or whatever (this means some trickery later on to keep io.fits
    # happy, since we haven't read in the lazy-loaded data arrays yet).
    hdulist.close()

    return maplist

