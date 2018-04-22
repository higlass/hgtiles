import hgtiles.htime as hght
import os.path as op

def test_tileset_info():
    filename = op.join('test_data', 'sample_htime.json')

    print(hght.tileset_info(filename))
