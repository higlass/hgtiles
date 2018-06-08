import hgtiles.bed2ddb as hgb2
import os.path as op

def test_bed2ddb_x_tiles():
    '''
    Retrieve a 1D tile from a 2d file
    '''
    filename = op.join('data', 'arrowhead_domains_short.txt.multires.db')

    pos1 = 1
    pos2 = 1

    data = hgb2.get_2D_tiles(filename, 13, pos1, pos2)
    print('data_2d:', len(data[(pos1, pos2)]))
    print("d2:", data)

    pos = 1
    data = hgb2.get_1D_tiles(filename, 13, pos)
    print('data_1d:', len(data[pos]))

    pass
