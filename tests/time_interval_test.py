import hgtiles.time_interval as hgti
import os.path as op

def test_tileset_info():
    filename = op.join('data', 'sample_htime.json')

    print(hgti.tileset_info(filename))
