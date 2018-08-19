import hgtiles.cooler as hgco
import json
import os.path as op

def test_cooler_info():
    filename = op.join('data', 'Dixon2012-J1-NcoI-R1-filtered.100kb.multires.cool')

    info = hgco.tileset_info(filename)

    filename = op.join('data', 'hic-resolutions.cool')
    print(hgco.tileset_info(filename))
