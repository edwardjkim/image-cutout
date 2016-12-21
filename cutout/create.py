import os
import sys
import pandas as pd
import numpy as np
from astropy.io import fits
from cutout.utils import nanomaggie_to_luptitude, align_images
from cutout.sdss import fits_file_name, single_field_image
from cutout.sex import run_sex


def get_cutout(catalog, images, bands, size=64):
    """
    Takes a pandas dataframe with columns 'XPEAK_IMAGE' and 'YPEAK_IMAGE'
    and saves cutout images in save_dir.

    Parameters
    ----------
    catalog: A pandas dataframe.
    images: A list of strings.
    bands: A list of strings.

    Returns
    -------
    A numpy array.
    """

    array = np.zeros((len(catalog), len(bands), size, size))
    coord = pd.DataFrame()

    for irow, row in catalog.iterrows():

        xpeak, ypeak = row[["XPEAK_IMAGE", "YPEAK_IMAGE"]].values

        reference = row["FILE"]

        image_data = fits.getdata(reference)

        ymax, xmax = image_data.shape

        right = xpeak - size // 2
        left = right + size
        
        if right < 0:
            right, left = 0, size
        if left > xmax:
            right, left = xmax - size, xmax

        up = ypeak - size // 2
        down = up + size

        if up < 0:
            up, down = 0, size
        if down > ymax:
            up, down = ymax - size, ymax

        for iband, band in enumerate(bands):

            image_data = fits.getdata(images[iband])
            cut_out = image_data[up: down, right: left]
            cut_out = nanomaggie_to_luptitude(cut_out, band)
            array[irow, iband, :, :] = cut_out

    return array


def run_all(rerun, run, camcol, field):
    """
    Run fetch, align, extract in a single field.
    """

    bands = [b for b in "ugriz"]

    try:
        single_field_image(rerun, run, camcol, field)
    except:
        raise

    original_images = [
        fits_file_name(rerun, run, camcol, field, band)
        for band in bands
    ]

    reference_image = fits_file_name(rerun, run, camcol, field, 'r')
    align_images(original_images, reference_image)

    catalog = run_sex(reference_image)

    registered_images = [
        image.replace(".fits", ".registered.fits")
        if image != reference_image else reference_image
        for image in original_images
    ]
    result = get_cutout(catalog, registered_images, bands)

    for image in set(original_images + registered_images):
        if os.path.exists(image):
            os.remove(image)

    filename = fits_file_name(rerun, run, camcol, field, 'r')
    filename = os.path.join("result", filename.replace(".fits", ".npy"))

    if not os.path.exists("result"):
        os.makedirs("result")

    np.save(filename, result)


def parallel_sex(df):
    """
    Parallel mode.
    """

    from mpi4py import MPI

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    start = len(df) // size * rank
    end = len(df) // size * (rank + 1)
    df = df[start:end]

    if rank == 0:
        print("Running on {} cores...\n".format(size))

    for idx, row in df.iterrows():
        print(
            "Core {0}: Procesing {1}-{2}-{3}-{4}".format(
                rank, row["rerun"], row["run"], row["camcol"], row["field"]
            )
        )
        try:
            run_all(row["rerun"], row["run"], row["camcol"], row["field"])
            print("Core {}: Successfully completed.".format(rank))
        except Exception as e:
            print("Core {}: {}".format(rank, e))

