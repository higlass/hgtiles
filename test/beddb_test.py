import hgtiles.beddb as hgbe
import os.path as op

def test_tiles():
    filename = op.join('data', '984627_PM16-00568-A_SM-9J5GB.beddb')

    tiles = hgbe.tiles(filename, ['x.15.16976'])
    print('tiles:', tiles)

    tiles = hgbe.tiles(filename, ['x.16.33952'])
    print('tiles:', tiles)

def test_tiles1():
    filename = op.join('data', '9ae0744a-9bc1-4cd7-b7cf-c6569ed9e4aa.consensus.20170119.somatic.cna.annotated.txt.beddb')

    tiles = hgbe.tiles(filename, ['x.2.2'])
    print('tiles:', len(tiles[0][1][0]))
