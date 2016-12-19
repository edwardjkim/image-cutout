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

    return None

