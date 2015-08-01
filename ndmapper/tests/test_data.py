import pytest
import os.path
import numpy as np
from astropy.utils.data import get_pkg_data_filename
from astropy.nddata import NDDataArray
from ..data import FileName, DataFile, DataFileList


# Data in common to some of the tests below:
fn_mefnodq = get_pkg_data_filename('data/eqbprgS20120827S0069_flat.fits')


def test_FileName_gemini_IRAF_1():

    fn = FileName('/home/james/rgS20120827S0066.fits')

    assert fn.dir == '/home/james' and \
           fn.prefix == 'rg' and \
           fn.base == 'S20120827S0066' and \
           fn.suffix == [] and \
           fn.ext == 'fits' and \
           fn.standard == True and \
           str(fn) == '/home/james/rgS20120827S0066.fits'


def test_FileName_nonconforming_1():

    fn = FileName('/home/fred/blah.fits')

    assert fn.dir == '/home/fred' and \
           fn.prefix == '' and \
           fn.base == 'blah' and \
           fn.suffix == [] and \
           fn.ext == 'fits' and \
           fn.standard == False and \
           str(fn) == '/home/fred/blah.fits'


def test_DataFile_gemini_IRAF_new_1():

    # Use a filename that can't exist, just to be sure it doesn't...
    df = DataFile(filename='rgS20120827S9999.fits', mode='new')

    assert df.filename.dir == '' and \
           df.filename.prefix == 'rg' and \
           df.filename.base == 'S20120827S9999' and \
           df.filename.suffix == [] and \
           df.filename.ext == 'fits' and \
           df.filename.standard == True and \
           len(df) == 0


def test_DataFile_gemini_IRAF_existing_1():

    df = DataFile(filename=fn_mefnodq)

    # Ignore the directory name because the above call translates it to the
    # absolute location of this package on the system.
    assert df.filename.prefix == 'eqbprg' and \
           df.filename.base == 'S20120827S0069' and \
           df.filename.suffix == ['_flat'] and \
           df.filename.ext == 'fits' and \
           df.filename.standard == True and \
           df.meta['OBJECT'] == 'GCALflat' and \
           len(df) == 2 and \
           abs(np.mean(df[0]) - 1.0623) < 0.0001 and \
           abs(np.mean(df[1]) - 0.9461) < 0.0001


def test_DataFileList_gemini_IRAF_existing_1():

    dfl = DataFileList(filenames=fn_mefnodq)

    assert len(dfl) == 1 and \
           dfl[0].filename.prefix == 'eqbprg' and \
           dfl[0].filename.base == 'S20120827S0069' and \
           dfl[0].filename.suffix == ['_flat'] and \
           dfl[0].filename.ext == 'fits' and \
           dfl[0].filename.standard == True and \
           dfl[0].meta['OBJECT'] == 'GCALflat' and \
           len(dfl[0]) == 2 and \
           abs(np.mean(dfl[0][0]) - 1.0623) < 0.0001 and \
           abs(np.mean(dfl[0][1]) - 0.9461) < 0.0001


def test_DataFileList_replacing_data_1():

    # Replace the data & header from file with blank ones:
    dfl = DataFileList(data=[], meta={}, filenames=fn_mefnodq)

    assert len(dfl) == 1 and len(dfl[0]) == 0 and len(dfl[0].meta) == 0


def test_DataFileList_len_mismatch_1():

    # Cannot have multiple data objects per filename:
    with pytest.raises(ValueError):
        dfl = DataFileList(data=[DataFile(), DataFile()], filenames=fn_mefnodq)


def test_DataFileList_broadcast_data_1():

    # But we can map the same dataset to multiple files:
    dfl = DataFileList(data=DataFile(), filenames=[fn_mefnodq, 'test_name'],
        mode='overwrite')

    # Produces 2 separate DataFiles referring to the same data array.
    assert len(dfl) == 2 and dfl[0] is not dfl[1] \
        and dfl[0].data is dfl[1].data


def test_DataFileList_copy_self_1():

    dfl1 = DataFileList(filenames=fn_mefnodq)
    dfl2 = DataFileList(dfl1)

    assert dfl1 is not dfl2 and dfl1 == dfl2


def test_DataFileList_append_1():

    dfl = DataFileList(filenames=fn_mefnodq)
    dfl.append(DataFile(filename='some_file', mode='new'))

    assert len(dfl) == 2 and str(dfl[0].filename) == fn_mefnodq \
        and str(dfl[1].filename) == 'some_file'


def test_DataFileList_nested_nddata_1():

    # Here the outer list maps to DataFiles and the inner one (if applicable)
    # to data extensions/groups within a file. The inner list can be omitted
    # where the file only contains a single NDData instance.
    dfl = DataFileList(data=[[NDDataArray([1,2,3]), NDDataArray([4])], \
                             NDDataArray([5,6])], \
                       filenames=['test_name_1', 'test_name_2'], mode='new')

    assert len(dfl[0]) == 2 and len(dfl[1]) == 1

