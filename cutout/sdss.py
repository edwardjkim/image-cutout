import os
import requests
import bz2
from time import sleep
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy import wcs


def fits_file_name(rerun, run, camcol, field, band):
    """
    SDSS FITS files are named, e.g., 'frame-g-001000-1-0027.fits.bz2'.
    We will uncompress this and save it as 'frame-g-001000-1-0027.fits'.

    This function returns 'frame-g-001000-1-0027.fits' in this case
    (without the '.bz2' extension).
    """

    return "frame-{4}-{1:06d}-{2}-{3:04d}.fits".format(
        rerun, run, camcol, field, band
    )


def field_image_url(rerun, run, camcol, field, band, base_url=None):
    """
    Returns URL for compressed FITS file for a single field SDSS DR12 image.
    """

    if base_url is None:
        base_url = requests.compat.urljoin(
            "http://data.sdss3.org/sas/dr12/boss/photoObj/frames/",
            "{0}/{1}/{2}/".format(rerun, run, camcol)
        )

    file_name = fits_file_name(rerun, run, camcol, field, band) + ".bz2"

    url = requests.compat.urljoin(base_url, file_name)

    return url


def single_field_image(rerun, run, camcol, field,
    base_url=None, bands='ugriz', ntry=10, save_dir=None):
    """
    Download a single field SDSS DR12 image.
    """

    files = [
        fits_file_name(rerun, run, camcol, field, band)
        for band in bands
    ]

    if all(os.path.exists(f) for f in files):
        return

    if save_dir is None:
        save_dir = os.getcwd()

    bands = [b for b in bands]

    for band in bands:

        url = field_image_url(rerun, run, camcol, field, band, base_url)
        file_name = fits_file_name(rerun, run, camcol, field, band)
        file_path = os.path.join(save_dir, file_name)

        for _ in range(ntry):

            try:
                resp = requests.get(url)
            except Exception as e:
                print(e)
                sleep(1)
                continue
                
            if resp.status_code == 200:

                with open(file_path, "wb") as f:
                    image = bz2.decompress(resp.content)
                    f.write(image)

                break

            else:
                print("{}: HTTP {}".format(file_name, resp.status_code))
                sleep(1)

    if all(os.path.exists(f) for f in files):
        return
    else:
        raise Exception


def sdss_fields(filename, shuffle=True):
    """
    Return all SDSS DR12 fields.
    Columns: run,rerun,camcol,field
    """

    df = pd.read_csv(
        filename,
        header=0,
        dtype={
            "rerun": np.uint16,
            "run": np.uint16,
            "camcol": np.uint16,
            "field": np.uint16
        }
    )
    if shuffle:
        df = df.sample(frac=1).reset_index(drop=True)

    return df


def fetch_sdss(filename):
    """
    Reads a CSV file and fetches all field images listed in the file.
    """

    df = sdss_fields(filename)

    for group in df.groupby(["rerun", "run", "camcol", "field"]).groups:
        single_field_image(*group)

    return None


def read_match_csv(filename, shuffle=True, skiprows=None, chunksize=None):
    """
    Reads a CSV file with a list of objects to be matched.

    The file should have the following columns:
    objID,ra,dec,rerun,run,camcol,field
    """

    if skiprows is not None:
        skiprows = (1, skiprows + 1)

    dtype = {
        "objID": np.uint64,
        "ra": np.float,
        "dec": np.float,
        "rerun": np.uint16,
        "run": np.uint16,
        "camcol": np.uint16,
        "field": np.uint16
    }

    df = pd.read_csv(
        filename,
        dtype=dtype,
        header=0,
        skiprows=skiprows,
        chunksize=chunksize
    )

    if shuffle:
        df = df.sample(frac=1).reset_index(drop=True)

    return df


def single_radec_to_pixel(rerun, run, camcol, field, ra, dec):
    """
    Converts world position (RA, DEC) to pixel position.

    Returns
    -------
    A tuple of (float, float)
    """

    fits_file = fits_file_name(rerun, run, camcol, field, 'r')
    hdulist = fits.open(fits_file)
    w = wcs.WCS(hdulist[0].header, relax=False)
    px, py = w.all_world2pix(ra, dec, 1)

    return px.item(), py.item()


def df_radec_to_pixel(df):
    """
    Takes a pandas dataframe with ra, dec columns and converts radec to pixel positions.

    Paramters
    ---------
    df: A pandas dataframe
    """

    result = df.copy()

    for idx, row in df.iterrows():

        rerun, run, camcol, field = \
            row[["rerun", "run", "camcol", "field"]].astype(int).values
        ra, dec = row[["ra", "dec"]].values

        px, py = single_radec_to_pixel(rerun, run, camcol, field, ra, dec)

        result.loc[idx, "XPEAK_IMAGE"] = px
        result.loc[idx, "YPEAK_IMAGE"] = py

    return result


def csv_radec_to_pixel(filename):
    """
    Reads a CSV file with ra, dec columns and converts radec to pixel positions.

    Paramters
    ---------
    filename: match.csv
    """

    df = read_match_csv(filename)
    result = df_radec_to_pixel(df)

    return result

