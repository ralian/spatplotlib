from distutils.core import setup

desc = 'Spatial plotting with Leaflet and Matplotlib. Forked from parts of both mplleaflet and mplexporter.'

with open('AUTHORS.md') as f:
    authors = f.read()

setup(name='spatplotlib',
    version='1.0.0',
    description=desc,
    long_description = desc + "\n\n" + authors,
    author='Will Bowers',
    author_email='wbowers314@gmail.com',
    url='https://github.com/ralian/spatplotlib',
    packages=['spatplotlib'],
    #package_dir = {'': 'spatplotlib'},
    license = 'BSD 3-clause'
    )
