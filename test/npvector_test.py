import numpy as np
import hgtiles.npvector as hgnv

def test_npvector():
    array = np.array(range(100))
    print('ts:', hgnv.tileset_info(array))
    assert('max_width' in hgnv.tileset_info(array))

    tile = hgnv.tiles(array, 0, 0)
    print('tile:', tile)

