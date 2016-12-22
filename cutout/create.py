import os
import sys
import pandas as pd
import numpy as np
from astropy.io import fits
from cutout.utils import nanomaggie_to_luptitude, align_images
from cutout.sdss import fits_file_name, single_field_image, df_radec_to_pixel
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

    return array.astype(np.float32)


def fetch_align(rerun, run, camcol, field, bands=None, remove=True):
    """
    Run fetch and align (but not extract) in a single field.
    """

    if bands is None:
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

    registered_images = [
        image.replace(".fits", ".registered.fits")
        if image != reference_image else reference_image
        for image in original_images
    ]

    if remove:
        images = [i for i in original_images if i != reference_image]
        for image in images:
            if os.path.exists(image):
                os.remove(image)

    return registered_images


def fetch_align_sex(rerun, run, camcol, field,
    bands=None, reference_band='r', remove=True):
    """
    Run fetch, align, and sex in a single field.
    """

    if bands is None:
        bands = [b for b in "ugriz"]

    registered_images = fetch_align(rerun, run, camcol, field, remove=remove)
    reference_image = [i for i in registered_images if 'registered' not in i][0]

    catalog = run_sex(reference_image, remove=remove)

    result = get_cutout(catalog, registered_images, bands)

    if remove:
        for image in registered_images:
            if os.path.exists(image):
                os.remove(image)

    filename = os.path.join("result", reference_image.replace(".fits", ".npy"))

    if not os.path.exists("result"):
        os.makedirs("result")

    np.save(filename, result)


def fetch_align_match(df, filename,
    bands=None, size=64, remove=True, save_dir="result"):
    """
    Match.
    """
    
    if bands is None:
        bands = [b for b in "ugriz"]

    groups = df.groupby(["rerun", "run", "camcol", "field"]).groups

    dtype = [
        ("objID", "u8"), # unsigned integer
        ("image", "f4", (len(bands), size, size)) # 4-byte float
    ]
    if "class" in df.columns:
        dtype += [("class", "U8")] # 8-character unicode string

    if "z" in df.columns:
        dtype += [("z", "f4")] # 4-byte float
       
    result = np.zeros(len(df), dtype=dtype)

    count = 0
    for field, index in groups.items():

        print("{0}-{1}-{2}-{3}: Processing...".format(*field))
        try:
            registered_images = fetch_align(*field, remove=remove)
        except Exception as e:
            print("{0}-{1}-{2}-{3}: {4}".format(*field, e))

        reference_image = [i for i in registered_images if 'registered' not in i][0]

        catalog = df_radec_to_pixel(df.loc[index, :])
        catalog = catalog.reset_index(drop=True)
        catalog["FILE"] = reference_image

        cutout = get_cutout(catalog, registered_images, bands)

        result[count: count + len(catalog)]["objID"] = catalog["objID"]
        result[count: count + len(catalog)]["image"] = cutout

        if "class" in catalog.columns:
            result[count: count + len(catalog)]["class"] = catalog["class"]
        if "z" in catalog.columns:
            result[count: count + len(catalog)]["z"] = catalog["z"]

        count += len(catalog)

        if remove:
            for image in registered_images:
                if os.path.exists(image):
                    os.remove(image)

        print("{0}-{1}-{2}-{3}: Sucessfully completed.".format(*field))

    result = result[:count]

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    np.save(os.path.join(save_dir, filename), result)

    return None


def sequential_match(df, remove=True):
    """
    Sequential mode.
    """

    filename = "match.npy"

    fetch_align_match(df, filename, remove=remove)

    return None


def sequential_sex(df, remove=True):
    """
    Sequential mode.
    """

    for idx, row in df.iterrows():
        rerun, run, camcol, field = \
            row[["rerun", "run", "camcol", "field"]].astype(int).values
        print(
            "{0}-{1}-{2}-{3}: Processing...".format(rerun, run, camcol, field)
        )
        try:
            fetch_align_sex(rerun, run, camcol, field, remove=remove)
            print(
                "{0}-{1}-{2}-{3}: Sucessfully completed.".format(rerun, run, camcol, field)
            )
        except Exception as e:
            print(e)

    return None


def parallel_sex(df, remove=True):
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
        rerun, run, camcol, field = \
            row[["rerun", "run", "camcol", "field"]].astype(int).values
        print(
            "Core {0}, {1}-{2}-{3}-{4}: Processing...".format(
                rank, rerun, run, camcol, field
            )
        )
        try:
            fetch_align_sex(rerun, run, camcol, field, remove=remove)
            print(
                "Core {0}, {1}-{2}-{3}-{4}: Sucessfully completed.".format(
                    rank, rerun, run, camcol, field
                )
            )
        except Exception as e:
            print(
                "Core {0}, {1}-{2}-{3}-{4}: {}".format(
                    rank, rerun, run, camcol, field, e
                )
            )

    return None
