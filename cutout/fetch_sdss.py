import os
import requests
import bz2
from time import sleep
import numpy as np
import pandas as pd


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

    files = [
        fits_file_name(rerun, run, camcol, field, band)
        for band in bands
    ]

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
        dtype={"run": np.int, "rerun": np.int, "camcol": np.int, "field": np.int}
    )
    if shuffle:
        df = df.sample(frac=1).reset_index(drop=True)

    return df
