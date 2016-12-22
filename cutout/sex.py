import os
import pandas as pd
import re
import shutil
import subprocess


def run_sex(filename, remove=True):
    """
    Runs SExtractor.
    """

    write_default_conv()
    write_default_param()
    write_default_sex()

    config_file = filename.replace(".fits", ".sex")
    catalog_name = filename.replace(".fits", ".cat")

    with open("default.sex", "r") as default_sex:
        with open(config_file, "w") as outfile:
            for line in default_sex:
                 line = re.sub(
                     r"^CATALOG_NAME\s+temp.cat",
                     "CATALOG_NAME     {}".format(catalog_name),
                     line
                 )
                 outfile.write(line)
    
    subprocess.call(["sex", "-c", config_file, filename])

    with open(catalog_name) as f:
        column_names = [line.split()[2] for line in f if line.startswith('#')]

    catalog = pd.read_csv(
        catalog_name,
        comment="#",
        sep="\s+",
        names=column_names
    )

    catalog["FILE"] = filename

    if remove:
        os.remove(config_file)
        os.remove(catalog_name)

    return catalog


def write_default_conv(filename="default.conv"):

    default_conv = (
        "CONV NORM\n"
        "# 3x3 ``all-ground'' convolution mask with FWHM = 2 pixels.\n"
        "1 2 1\n"
        "2 4 2\n"
        "1 2 1\n"
    ).format()

    with open(filename, "w") as f:
        f.write(default_conv)

    return None


def write_default_param(filename="default.param"):

    default_param = (
        "XMIN_IMAGE               Minimum x-coordinate among detected pixels                [pixel]\n"
        "YMIN_IMAGE               Minimum y-coordinate among detected pixels                [pixel]\n"
        "XMAX_IMAGE               Maximum x-coordinate among detected pixels                [pixel]\n"
        "YMAX_IMAGE               Maximum y-coordinate among detected pixels                [pixel]\n"
        "XPEAK_IMAGE              x-coordinate of the brightest pixel                       [pixel]\n"
        "YPEAK_IMAGE              y-coordinate of the brightest pixel                       [pixel]\n"
    ).format()

    with open(filename, "w") as f:
        f.write(default_param)

    return None


def write_default_sex(filename="default.sex"):

    default_sex = (
        "#-------------------------------- Catalog ------------------------------------\n"
        "\n"
        "CATALOG_NAME     temp.cat       # name of the output catalog\n"
        "CATALOG_TYPE     ASCII_HEAD     # NONE,ASCII,ASCII_HEAD, ASCII_SKYCAT,\n"
        "                                # ASCII_VOTABLE, FITS_1.0 or FITS_LDAC\n"
        "PARAMETERS_NAME  default.param  # name of the file containing catalog contents\n"
        " \n"
        "#------------------------------- Extraction ----------------------------------\n"
        " \n"
        "DETECT_TYPE      CCD            # CCD (linear) or PHOTO (with gamma correction)\n"
        "DETECT_MINAREA   3              # min. # of pixels above threshold\n"
        "DETECT_THRESH    1.5            # <sigmas> or <threshold>,<ZP> in mag.arcsec-2\n"
        "ANALYSIS_THRESH  1.5            # <sigmas> or <threshold>,<ZP> in mag.arcsec-2\n"
        " \n"
        "FILTER           Y              # apply filter for detection (Y or N)?\n"
        "FILTER_NAME      default.conv   # name of the file containing the filter\n"
        " \n"
        "DEBLEND_NTHRESH  32             # Number of deblending sub-thresholds\n"
        "DEBLEND_MINCONT  0.005          # Minimum contrast parameter for deblending\n"
        " \n"
        "CLEAN            Y              # Clean spurious detections? (Y or N)?\n"
        "CLEAN_PARAM      1.0            # Cleaning efficiency\n"
        " \n"
        "MASK_TYPE        CORRECT        # type of detection MASKing: can be one of\n"
        "                                # NONE, BLANK or CORRECT\n"
        "\n"
        "#------------------------------ Photometry -----------------------------------\n"
        " \n"
        "PHOT_APERTURES   5              # MAG_APER aperture diameter(s) in pixels\n"
        "PHOT_AUTOPARAMS  2.5, 3.5       # MAG_AUTO parameters: <Kron_fact>,<min_radius>\n"
        "PHOT_PETROPARAMS 2.0, 3.5       # MAG_PETRO parameters: <Petrosian_fact>,\n"
        "                                # <min_radius>\n"
        "\n"
        "SATUR_LEVEL      50000.0        # level (in ADUs) at which arises saturation\n"
        "SATUR_KEY        SATURATE       # keyword for saturation level (in ADUs)\n"
        " \n"
        "MAG_ZEROPOINT    0.0            # magnitude zero-point\n"
        "MAG_GAMMA        4.0            # gamma of emulsion (for photographic scans)\n"
        "GAIN             0.0            # detector gain in e-/ADU\n"
        "GAIN_KEY         GAIN           # keyword for detector gain in e-/ADU\n"
        "PIXEL_SCALE      1.0            # size of pixel in arcsec (0=use FITS WCS info)\n"
        " \n"
        "#------------------------- Star/Galaxy Separation ----------------------------\n"
        " \n"
        "SEEING_FWHM      1.2            # stellar FWHM in arcsec\n"
        "STARNNW_NAME     default.nnw    # Neural-Network_Weight table filename\n"
        " \n"
        "#------------------------------ Background -----------------------------------\n"
        " \n"
        "BACK_SIZE        64             # Background mesh: <size> or <width>,<height>\n"
        "BACK_FILTERSIZE  3              # Background filter: <size> or <width>,<height>\n"
        " \n"
        "BACKPHOTO_TYPE   GLOBAL         # can be GLOBAL or LOCAL\n"
        " \n"
        "#------------------------------ Check Image ----------------------------------\n"
        " \n"
        "CHECKIMAGE_TYPE  SEGMENTATION   # can be NONE, BACKGROUND, BACKGROUND_RMS,\n"
        "                                # MINIBACKGROUND, MINIBACK_RMS, -BACKGROUND,\n"
        "                                # FILTERED, OBJECTS, -OBJECTS, SEGMENTATION,\n"
        "                                # or APERTURES\n"
        "CHECKIMAGE_NAME  check.fits     # Filename for the check-image\n"
        " \n"
        "#--------------------- Memory (change with caution!) -------------------------\n"
        " \n"
        "MEMORY_OBJSTACK  3000           # number of objects in stack\n"
        "MEMORY_PIXSTACK  300000         # number of pixels in stack\n"
        "MEMORY_BUFSIZE   1024           # number of lines in buffer\n"
        " \n"
        "#----------------------------- Miscellaneous ---------------------------------\n"
        " \n"
        "VERBOSE_TYPE     QUIET          # can be QUIET, NORMAL or FULL\n"
        "HEADER_SUFFIX    .head          # Filename extension for additional headers\n"
        "WRITE_XML        N              # Write XML file (Y/N)?\n"
        "XML_NAME         sex.xml        # Filename for XML output\n"
        "\n"
        "#----------------------------- ASSOC parameters ---------------------------------\n"
        "\n"
        "ASSOC_NAME       sky.list       # name of the ASCII file to ASSOCiate, the expected pixel \n"
        "                                # coordinates list given as [id, xpos, ypos]\n"
        "ASSOC_DATA       1              # columns of the data to replicate (0=all), replicate id\n"
        "                                # of the object in the SExtractor output file\n"
        "ASSOC_PARAMS     2,3            # columns of xpos,ypos[,mag] in the expected pixel\n"
        "                                # coordinates list\n"
        "ASSOC_RADIUS     2.0            # cross-matching radius (pixels)\n"
        "ASSOC_TYPE       NEAREST        # ASSOCiation method: FIRST, NEAREST, MEAN,\n"
        "                                # MAG_MEAN, SUM, MAG_SUM, MIN or MAX\n"
        "ASSOCSELEC_TYPE  MATCHED        # ASSOC selection type: ALL, MATCHED or -MATCHED\n"
    ).format()

    with open(filename, "w") as f:
        f.write(default_sex)

