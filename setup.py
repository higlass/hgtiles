from setuptools import setup

install_requires = [
    'cython',
    'numpy',
    'pysam',
    'h5py',
    'pandas',
    'slugid',
    'scipy',
    'cooler',
    'pybbi==0.1.3'
]

setup(
    name='hgtiles',
    version='0.2.12',
    description='Tile loading for higlass-server',
    author='Peter Kerpedjiev',
    author_email='pkerpedjiev@gmail.com',
    url='',
    install_requires=install_requires,
    packages=['hgtiles']
)
