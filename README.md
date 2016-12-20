# Image cutout for SDSS (and other photometric surveys)

Moved from [dl4astro](https://github.com/EdwardJKim/dl4astro/tree/master/scripts) into a separate package.

## Installation

Clone repository and run `setup.py`:
```shell
$ git clone https://github.com/edwardjkim/image-cutout
$ cd image-cutout
$ sudo python3 setup.py install
```

This package also requires [Montage](http://montage.ipac.caltech.edu/) and [SExtractor](http://www.astromatic.net/software/sextractor).
You can either use Docker or install the packages.

### Docker

To build the Docker image, run
```shell
$ docker build -t <image name> docker
```
and create a container with
```shell
$ docker run -d --name <container name> -p 8888:8888 -e "PASSWORD=YourPassword" -v /mnt/volume:/home/jovyan/work/shared <image name>
```
You can now access the notebook server at http://<your ip address>:8888.

If you can't use Docker, install Montage and SExtractor.
For example, on XSEDE Stampede, you can do the following.

### Montage

```shell
$ mkdir $HOME/montage
$ cd $HOME/montage
$ wget http://montage.ipac.caltech.edu/download/Montage_v4.0.tar.gz && \
$ tar xvzf Montage_v4.0.tar.gz
$ cd montage
$ make
$ export PATH=$PATH:$HOME/montage/bin
```

### FFTW (for SExtractor)

```shell
$ cd $HOME
$ wget http://www.fftw.org/fftw-3.3.5.tar.gz
$ tar xvzf fftw-3.3.5.tar.gz
$ ./configure --enable-threads --enable-float --prefix=$HOME/lib/fftw
$ make
$ make install
```

### Atlas (for SExtractor)

```shell
$ cd $HOME
$ wget http://www.netlib.org/lapack/lapack-3.6.1.tgz
$ wget http://downloads.sourceforge.net/project/math-atlas/Stable/3.10.3/atlas3.10.3.tar.bz2
$ mv ATLAS ATLAS3.10.3
$ cd ATLAS3.10.3
$ mkdir Linux_C2D64SSE3
$ cd Linux_C2D64SSE3
$ ../configure --prefix=$HOME/lib/atlas --with-netlib-lapack-tarfile=$HOME/lapack-3.6.1.tgz
$ make build
$ make install
```

### SExtractor

```shell
$ cd $HOME
$ http://www.astromatic.net/download/sextractor/sextractor-2.19.5.tar.gz
$ tar xvzf sextractor-2.19.5.tar.gz
$ cd sextractor-2.19.5
$ ./configure --prefix=$HOME/lib/sextractor \
  --with-fftw-libdir=$HOME/lib/fftw/lib \
  --with-fftw-incdir=$HOME/lib/fftw/include \
  --with-atlas-libdir=$HOME/lib/atlas/lib \
  --with-atlas-incdir=$HOME/lib/atlas/include
$ make
$ make install
$ export PATH=$PATH:$HOME/lib/sextractor/bin
```
