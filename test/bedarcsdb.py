import collections as col
import hgtiles.bedarcsdb as hgbad
import os.path as op

def test_bedarcsdb_tiles():
    '''
    Retrieve a 1D tile from a 2d file
    '''
    filename = op.join('data', 'arrowhead_domains_short.txt.multires.db')

    pos = 2
    data = hgbad.tiles(filename, ["b.2.{}".format(pos)])

    filename = op.join('data', '9ae0744a-9bc1-4cd7-b7cf-c6569ed9e4aa.pcawg_consensus_1.6.161022.somatic.sv.bedpe.multires.db')

    data = hgbad.tiles(filename, ["b.4.11".format(pos)])
    print('data:', len(data[0][1][11]))
    counts = col.defaultdict(int)

    for d in data[0][1][11]:
        chr1,chr2 = sorted([d['fields'][0], d['fields'][3]])

        counts[(chr1,chr2)] += 1
    print('counts:', counts)

    data = hgbad.tiles(filename, ["b.4.10".format(pos)])
    print('data:', len(data[0][1][10]))
    counts = col.defaultdict(int)

    for i,d in enumerate(data[0][1][10]):
        chr1,chr2 = sorted([d['fields'][0], d['fields'][3]])

        counts[(chr1,chr2)] += 1
    print('counts:', counts)
    pass
