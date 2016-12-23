import os
import shutil
import sys
import pandas as pd
import numpy as np
from astropy.io import fits
from cutout.utils import nanomaggie_to_luptitude, align_images
from cutout.sdss import (
    fits_file_name, single_field_image, df_radec_to_pixel, read_match_csv
)
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


def get_registered_images(rerun, run, camcol, field, bands=None):
    """
    Returns a list of registed image FITS files.
    """

    if bands is None:
        bands = [b for b in "ugriz"]

    original_images = [
        fits_file_name(rerun, run, camcol, field, band)
        for band in bands
    ]

    reference_image = fits_file_name(rerun, run, camcol, field, 'r')

    registered_images = [
        image.replace(".fits", ".registered.fits")
        if image != reference_image else reference_image
        for image in original_images
    ]

    return registered_images


def fetch_align(rerun, run, camcol, field, bands=None, remove=True):
    """
    Run fetch and align (but not extract) in a single field.
    """

    if bands is None:
        bands = [b for b in "ugriz"]

    original_images = [
        fits_file_name(rerun, run, camcol, field, band)
        for band in bands
    ]

    reference_image = fits_file_name(rerun, run, camcol, field, 'r')

    registered_images = [
        image.replace(".fits", ".registered.fits")
        if image != reference_image else reference_image
        for image in original_images
    ]

    if not all(os.path.exists(i) for i in registered_images):

        try:
            single_field_image(rerun, run, camcol, field)
            align_images(original_images, reference_image)
            print("{}-{}-{}-{}: Aligned.".format(rerun, run, camcol, field))
        except:
            raise

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

        try:
            registered_images = fetch_align(*field, remove=remove)

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

            print("{0}-{1}-{2}-{3}: Sucessfully completed.".format(*field))

        except Exception as e:
            rerun, run, camcol, field_ = field
            print(
                "{0}-{1}-{2}-{3}: {4}".format(rerun, run, camcol, field_, e)
            )
            registered_image = registered_images(rerun, run, camcol, field_)

        if remove:
            for image in registered_images:
                if os.path.exists(image):
                    os.remove(image)

    result = result[:count]

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)


    np.save(os.path.join(save_dir, filename), result)

    return None


def sequential_match(filename, remove=True):
    """
    Sequential mode.
    """

    groups = write_group_csv(filename)
        
    print("Sequential mode: Processing {} fields...\n".format(len(groups)))

    for group in groups:

        npy_file = group.replace(".temp", ".npy")
        if os.path.exists(os.path.join("result", npy_file)):
            continue

        chunk = read_match_csv(os.path.join("temp", group))
        field = group.replace("frame-", "").replace(".temp", "")

        print(
            "{}: Processing {} object(s)...".format(field, len(chunk))
        )
        
        npy_file = group.replace(".temp", ".npy")

        try:
            fetch_align_match(chunk, npy_file, remove=remove)
            print("{}: Sucessfully completed.".format(field))
        except Exception as e:
            raise

    if remove:
        clean_group_temp()

    return None


def write_group_csv(filename, save_dir="temp", skip_exists=True):
    """
    """

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    df = read_match_csv(filename)
    groups = df.groupby(["rerun", "run", "camcol", "field"]).groups

    group_list = []

    for field, index in groups.items():

        rerun, run, camcol, field_ = field
        fout = "frame-{}-{}-{}-{}.temp".format(rerun, run, camcol, field_)
        group_list.append(fout)

        file_path = os.path.join(save_dir, fout)
        if skip_exists and os.path.exists(file_path):
            continue
        else:
            df.loc[index, :].to_csv(file_path)

    return group_list


def check_npy_success(filename, save_dir="result"):
    """
    """

    return os.path.exists(os.path.join(save_dir, filename))


def clean_group_temp(save_dir="temp"):
    """
    """

    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)


def parallel_match(filename, remove=True, chunksize=1000):
    """
    Parallel mode.
    """

    from mpi4py import MPI

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if rank == 0:
        groups = write_group_csv(filename)
        print("Parallel mode: Processing {} fields on {} cores...\n".format(len(groups), size))
    else:
        groups = None

    groups = comm.bcast(groups, root=0)
  
    start = len(groups) // size * rank
    end = len(groups) // size * (rank + 1)

    for group in groups[start: end]:

        npy_file = group.replace(".temp", ".npy")

        if check_npy_success(group):
            continue

        chunk = read_match_csv(os.path.join("temp", group))

        field = group.replace("frame-", "").replace(".temp", "")

        print(
            "{}: Processing {} object(s) on core {}..."
            "".format(field, len(chunk), rank)
        )
        
        npy_file = group.replace(".temp", ".npy")

        try:
            fetch_align_match(chunk, npy_file, remove=remove)
            print(
                "{0}: Sucessfully completed on core {1}.".format(field, rank)
            )
        except Exception as e:
            print(
                "Core {0}: {1}".format(rank, e)
            )

    if remove and all(check_npy_success(group) for group in groups):
        clean_group_temp()

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
