import os
import sys
from cutout.fetch_sdss import single_field_image
from cutout.utils import align_images


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
            "frame-i-001000-1-0027.fits",
            "frame-z-001000-1-0027.fits"
        ]
        align_images(images, "frame-r-001000-1-0027.fits")


if __name__ == "__main__":
    main()

