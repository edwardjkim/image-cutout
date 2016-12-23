from setuptools import setup


setup(
    name='cutout',
    version='0.1.0',
    packages=['cutout'],
    entry_points={
        'console_scripts': [
            'cutout = cutout.__main__:main'
        ]
    },
    install_requires=[
        'requests',
        'astropy',
        'montage-wrapper'
    ]
)
