from setuptools import setup

install_requires = [
    'cython',
    'numpy',
    'pysam',
    'h5py',
    'pandas',
    'slugid',
    'cooler',
    'pybbi==0.1.1'
]

setup(
    name='hgtiles',
    version='0.2.12',
    description='Tile loading for higlass-server',
    author='Peter Kerpedjiev',
    author_email='pkerpedjiev@gmail.com',
    url='',
    install_requires=install_requires,
    dependency_links=[
        'git+ssh://git@github.com/nvictus/pybbi.git@v0.1.1#egg=pybbi-0.1.1'
    ],
    packages=['hgtiles'],
)
