import os
import sys
import numpy as np
from cutout.sdss import sdss_fields, single_field_image, read_match_csv
from cutout.utils import align_images
from cutout.sex import run_sex
from cutout.create import (
    get_cutout,
    sequential_sex, parallel_sex,
    sequential_match, parallel_match
)


def main(args=None):

    if args is None:
        args = sys.argv[1:]

    # check for subcommand
    if len(args) == 0:
        sys.stderr.write(
            "Usage: cutout <subcommand>\n"
            "Valid subcommands are: sequential, parallel, fetch, align, extract\n"
        )
        return 1

    if args[0] == "parallel" and args[1] == "match":
        if len(args[2:]) == 0:
            sys.stderr.write(
                "Usage: cutout sequential match <CSV file>\n"
            )
        parallel_match(args[2])

    elif args[0] == "sequential" and len(args[1:]) == 0:
        sys.stderr.write(
            "Usage: cutout sequential <subcommand>\n"
            "Valid subcommands are: match, sex\n"
        )
   
    elif args[0] == "parallel":
        if os.path.exists("fetch.csv"):
            df = sdss_fields("fetch.csv")
            parallel_sex(df)


    elif args[0] == "sequential" and args[1] == "match":
        if len(args[2:]) == 0:
            sys.stderr.write(
                "Usage: cutout sequential match <CSV file>\n"
            )
        sequential_match(args[2])

    elif args[0] == "sequential":
        if os.path.exists("fetch.csv"):
            df = sdss_fields("fetch.csv")
            sequential_sex(df)

    elif args[0] == "fetch":
        if os.path.exists("fetch.csv"):
            df = sdss_fields("fetch.csv")
        elif len(args[1:]) == 0:
            sys.stderr.write("Need a list of fields in a CSV file\n")
            return 1
        else:
            df = sdss_fields(args[1])

        for idx, row in df.iterrows():
            single_field_image(
                row["rerun"], row["run"], row["camcol"], row["field"]
            )
   
    elif args[0] == "align":
        images = [
            "frame-u-001000-1-0027.fits",
            "frame-g-001000-1-0027.fits",
            "frame-r-001000-1-0027.fits",
            "frame-i-001000-1-0027.fits",
            "frame-z-001000-1-0027.fits"
        ]
        align_images(images, "frame-r-001000-1-0027.fits")

    elif args[0] == "extract":
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

    else:
        sys.stderr.write(
            "Usage: cutout <subcommand>\n"
            "Valid subcommands are: fetch, align, extract\n"
        )
        return 1

if __name__ == "__main__":
    main()

