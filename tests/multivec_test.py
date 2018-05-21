import os.path as op
import hgtiles.multivec as hgmu

def test_multivec():
    filename = op.join('data', 'all.KL.bed.multires.mv5')

    print(hgmu.tileset_info(filename))

