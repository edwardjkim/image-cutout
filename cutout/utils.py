import os
import numpy as np
import montage_wrapper as mw


def align_images(images, reference, save_dir=None):
    """
    Aligns images to the reference image.
    The file names must end with ".fits".

    Parameters
    ----------
    images: A list of strings.
    reference: A string.

    Returns
    -------
    None
    """

    header = reference.replace(".fits", ".header")
    mw.commands.mGetHdr(reference, header)

    if save_dir is None:
        save_dir = os.getcwd()

    registered_path = [
        os.path.join(save_dir, image.replace(".fits", ".registered.fits"))
        for image in images
    ]

    mw.reproject(
        images, registered_path,
        header=header, exact_size=True, silent_cleanup=True, common=True
    )

    if os.path.exists(header):
        os.remove(header)

    return None


def nanomaggie_to_luptitude(array, band):
    """
    Converts nanomaggies (flux) to luptitudes (magnitude).

    http://www.sdss.org/dr12/algorithms/magnitudes/#asinh
    http://arxiv.org/abs/astro-ph/9903081

    Parameters
    ----------
    array: A numpy array.
    band: One of 'u', 'g', 'r', 'i' or 'z'.

    Returns
    -------
    A float
    """

    b = {
        'u': 1.4e-10,
        'g': 0.9e-10,
        'r': 1.2e-10,
        'i': 1.8e-10,
        'z': 7.4e-10
    }
    nanomaggie = array * 1.0e-9 # fluxes are in nanomaggies

    luptitude = -2.5 / np.log(10) * (np.arcsinh((nanomaggie / (2 * b[band]))) + np.log(b[band]))
    
    return luptitude
