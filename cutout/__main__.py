import os
import sys
import numpy as np
from cutout.fetch_sdss import single_field_image
from cutout.utils import align_images
from cutout.sex import run_sex
from cutout.create import get_cutout


def main(args=None):

    if args is None:
        args = sys.argv[1:]

    # check for subcommand
    if len(args) == 0:
        sys.stderr.write(
            "Usage: cutout <subcommand>\n"
            "Valid subcommands are: fetch\n"
        )
        return 1

    # fetch subcommand
    if args[0] == "fetch":
        single_field_image(301, 1000, 1, 27)

    if args[0] == "align":
        images = [
            "frame-u-001000-1-0027.fits",
            "frame-g-001000-1-0027.fits",
            "frame-r-001000-1-0027.fits",
            "frame-i-001000-1-0027.fits",
            "frame-z-001000-1-0027.fits"
        ]
        align_images(images, "frame-r-001000-1-0027.fits")

    if args[0] == "extract":
        catalog = run_sex("frame-r-001000-1-0027.fits")
        images = [
            "frame-u-001000-1-0027.registered.fits",
            "frame-g-001000-1-0027.registered.fits",
            "frame-r-001000-1-0027.fits",
            "frame-i-001000-1-0027.registered.fits",
            "frame-z-001000-1-0027.registered.fits"
        ]
        bands = [b for b in "ugriz"]
        result = get_cutout(catalog, images, bands)
        np.save("frame-r-001000-1-0027.npy", result)


if __name__ == "__main__":
    main()

