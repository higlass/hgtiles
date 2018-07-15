from setuptools import setup

setup(
    name='hgtiles',
    version='0.2.9',
    description='Tile loading for higlass-server',
    author='Peter Kerpedjiev',
    author_email='pkerpedjiev@gmail.com',
    install_requires=[
        'pandas>=0.19',
    ],
    url='',
    packages=['hgtiles'],
)
