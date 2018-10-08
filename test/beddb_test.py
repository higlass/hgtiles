import hgtiles.beddb as hgbe
import json
import os.path as op

def test_list_items():
    filename = op.join('data', 'gene_annotations.short.db')

    ret = hgbe.list_items(filename, 0, 100000000, max_entries=100)
    # print('ret:', ret)
