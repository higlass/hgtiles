from setuptools import setup, find_packages

setup(
    name='hgtiles',
    version='0.2.2',
    description='Tile loading for higlass-server',
    author='Peter Kerpedjiev',
    author_email='pkerpedjiev@gmail.com',
    install_requires=[
        'pandas>=0.19',
    ],
    url='',
    packages=['hgtiles'],
)
