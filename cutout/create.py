import os
import pandas as pd
import numpy as np
from astropy.io import fits
from cutout.utils import nanomaggie_to_luptitude


def get_cutout(catalog, images, bands, size=64, save_dir="result"):
    """
    Takes a pandas dataframe with columns 'XPEAK_IMAGE' and 'YPEAK_IMAGE'
    and saves cutout images in save_dir.
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


def find_center(xmin, xmax, cut_size, frame_size):
    diff = 0.5 * np.abs((xmax - xmin) - cut_size)
    if xmin + diff < 0:
        r = 0
        l = r + cut_size
    elif xmax + diff >= frame_size:
        l = frame_size
        r = l - cut_size
    else:
        r = np.floor(xmin + diff)
        l = r + cut_size
    return r, l

