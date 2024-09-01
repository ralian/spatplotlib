from setuptools import setup, find_packages

with open('AUTHORS.md') as f:
    authors = f.read()

description = "Fork of both mplleaflet and mplexporter: Build Matplotlib plots inside leaflet maps."
long_description = description + "\n\n" + authors
NAME = "spatplot"
AUTHOR = "Will Bowers"
AUTHOR_EMAIL = "wbowers314@gmail.com"
MAINTAINER = "Will Bowers"
MAINTAINER_EMAIL = "wbowers314@gmail.com"
DOWNLOAD_URL = 'http://github.com/jwass/mplleaflet'
LICENSE = 'BSD 3-clause'
VERSION = '1.0.0'

setup(
    name=NAME,
    version=VERSION,
    description=description,
    long_description=long_description,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    url=DOWNLOAD_URL,
    download_url=DOWNLOAD_URL,
    license=LICENSE,
    packages=find_packages(),
    package_data={'': ['*.html']}, # Include the templates
    install_requires=[
        "matplotlib",
    ],
)