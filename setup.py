from setuptools import setup
from setuptools.command.build_ext import build_ext as _build_ext

install_requires = [
    'cython',
    'numpy',
    'pysam',
    'h5py',
    'pandas',
    'slugid',
    'numpy',
    'scipy==1.0.1',
    'cooler',
    'pybbi==0.1.3',
]

setup(
    name='hgtiles',
    version='0.2.13',
    description='Tile loading for higlass-server',
    author='Peter Kerpedjiev',
    author_email='pkerpedjiev@gmail.com',
    url='',
    install_requires=install_requires,
    setup_requires=['numpy'],
    packages=['hgtiles']
)
