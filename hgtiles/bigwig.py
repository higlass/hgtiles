import bbi
import cooler
import functools as ft
import logging
import numpy as np
import pandas as pd
import re
import time

TILE_SIZE = 1024

logger = logging.getLogger(__name__)

def get_quadtree_depth(chromsizes):
    tile_size_bp = TILE_SIZE
    min_tile_cover = np.ceil(sum(chromsizes) / tile_size_bp)
    return int(np.ceil(np.log2(min_tile_cover)))

def get_zoom_resolutions(chromsizes):
    return [2**x for x in range(get_quadtree_depth(chromsizes) + 1)][::-1]

def natsort_key(s, _NS_REGEX=re.compile(r'(\d+)', re.U)):
        return tuple([int(x) if x.isdigit() else x
                             for x in _NS_REGEX.split(s) if x])

def natcmp(x, y):
    if x.find('_') >= 0:
        x_parts = x.split('_')
        if y.find('_') >= 0:
            # chr_1 vs chr_2
            y_parts = y.split('_')

            return natcmp(x_parts[1], y_parts[1])
        else:
            # chr_1 vs chr1
            # chr1 comes first
            return 1
    if y.find('_') >= 0:
        # chr1 vs chr_1
        # y comes second
        return -1

    _NS_REGEX=re.compile(r'(\d+)', re.U)
    x_parts = tuple([int(a) if a.isdigit() else a
                             for a in _NS_REGEX.split(x) if a])
    y_parts = tuple([int(a) if a.isdigit() else a
                             for a in _NS_REGEX.split(y) if a])

    if x == 'chrM':
        # chrM goes at the end of the non alternate contigs
        return 1
    if y == 'chrM':
        return -1

    if x_parts < y_parts:
        return -1
    elif y_parts > x_parts:
        return 1
    else:
        return 0

def natsorted(iterable):
    return sorted(iterable, key=ft.cmp_to_key(natcmp))

def get_chromsizes(bwpath):
    """
    TODO: replace this with negspy
    
    Also, return NaNs from any missing chromosomes in bbi.fetch
    
    """
    chromsizes = bbi.chromsizes(bwpath)
    chromosomes = natsorted(chromsizes.keys())
    print("chromosomes", chromosomes)
    chrom_series = pd.Series(chromsizes)[chromosomes]
    return chrom_series

def abs2genomic(chromsizes, start_pos, end_pos):
    abs_chrom_offsets = np.r_[0, np.cumsum(chromsizes.values)]
    cid_lo, cid_hi = np.searchsorted(abs_chrom_offsets,
                                     [start_pos, end_pos],
                                     side='right') - 1
    rel_pos_lo = start_pos - abs_chrom_offsets[cid_lo]
    rel_pos_hi = end_pos - abs_chrom_offsets[cid_hi]
    start = rel_pos_lo
    for cid in range(cid_lo, cid_hi):
        yield cid, start, chromsizes[cid]
        start = 0
    yield cid_hi, start, rel_pos_hi

def tileset_info(bwpath):
    '''
    Get the tileset info for a bigWig file

    Parameters
    ----------
    bwpath: string
        The path to the bigwig file from which to retrieve data

    Returns
    -------
    tileset_info: {'min_pos': [], 
                    'max_pos': [], 
                    'tile_size': 1024, 
                    'max_zoom': 7
                    }
    '''
    TILE_SIZE = 1024
    chromsizes = bbi.chromsizes(bwpath)
    chromosomes = cooler.util.natsorted(chromsizes.keys())
    chromsizes = pd.Series(chromsizes)[chromosomes]
    min_tile_cover = np.ceil(sum(chromsizes) / TILE_SIZE)
    max_zoom = int(np.ceil(np.log2(min_tile_cover)))
    tileset_info = {
        'min_pos': [0],
        'max_pos': [TILE_SIZE * 2 ** max_zoom],
        'max_width': TILE_SIZE * 2 ** max_zoom,
        'tile_size': TILE_SIZE,
        'max_zoom': max_zoom
    }
    return tileset_info

def get_bigwig_tile(bwpath, zoom_level, start_pos, end_pos, chromsizes=None):
    t1 = time.time()
    if chromsizes is None:
        print("here")
        chromsizes = get_chromsizes(bwpath)
    print('chromsizes:', chromsizes)
    t2 = time.time()

    # print("chromosomes time:", t2 - t1)
    resolutions = get_zoom_resolutions(chromsizes)
    binsize = resolutions[zoom_level]
   
    arrays = []
    for cid, start, end in abs2genomic(chromsizes, start_pos, end_pos):
        n_bins = int(np.ceil((end - start) / binsize))
        try:
            chrom = chromsizes.index[cid]
            clen = chromsizes.values[cid]

            t1 = time.time()
            #print("fetching:", chrom, start, end, n_bins);
            x = bbi.fetch(bwpath, chrom, start, end,
                          bins=n_bins, missing=np.nan)
            t2 = time.time()

            if t2 - t1 > 0.5:
                print("fetching:", chrom, start, end, n_bins, "fetched time: {:.2f}".format(time.time() - t1))

            # drop the very last bin if it is smaller than the binsize
            if end == clen and clen % binsize != 0:
                x = x[:-1]
        except IndexError:
            # beyond the range of the available chromosomes
            # probably means we've requested a range of absolute
            # coordinates that stretch beyond the end of the genome
            x = np.zeros(n_bins)

        arrays.append(x)

    return np.concatenate(arrays)


def tiles(bwpath, tile_ids, chromsizes_map={}):
    '''
    Generate tiles from a bigwig file.

    Parameters
    ----------
    tileset: tilesets.models.Tileset object
        The tileset that the tile ids should be retrieved from
    tile_ids: [str,...]
        A list of tile_ids (e.g. xyx.0.0) identifying the tiles
        to be retrieved
    chromsizes_map: {uid: []}
        A set of chromsizes listings corresponding to the parameters of the 
        tile_ids

    Returns
    -------
    tile_list: [(tile_id, tile_data),...]
        A list of tile_id, tile_data tuples
    '''
    import base64
    TILE_SIZE = 1024
    generated_tiles = []
    for tile_id in tile_ids:
        tile_option_parts = tile_id.split('|')[1:]
        tile_no_options = tile_id.split('|')[0]
        tile_id_parts = tile_no_options.split('.')
        tile_position = list(map(int, tile_id_parts[1:3]))

        tile_options = dict([o.split(':') for o in tile_option_parts])

        chromsizes_id = None
        if 'cos' in tile_options:
            chromsizes_id = tile_options['cos']

        print('chromsizes_id:', chromsizes_id)

        if chromsizes_id in chromsizes_map:
            chromsizes = chromsizes_map[chromsizes_id]
        else:
            chromsizes = None

        zoom_level = tile_position[0]
        tile_pos = tile_position[1]
        
        # this doesn't combine multiple consequetive ids, which
        # would speed things up
        if chromsizes is None:
            chromsizes = get_chromsizes(bwpath)

        print('chromsizes:', chromsizes)
        max_depth = get_quadtree_depth(chromsizes)
        tile_size = TILE_SIZE * 2 ** (max_depth - zoom_level)
        start_pos = tile_pos * tile_size
        end_pos = start_pos + tile_size
        dense = get_bigwig_tile(bwpath, zoom_level, start_pos, end_pos, chromsizes)

        if len(dense):
            max_dense = max(dense)
            min_dense = min(dense)
        else:
            max_dense = 0
            min_dense = 0

        min_f16 = np.finfo('float16').min
        max_f16 = np.finfo('float16').max

        has_nan = len([d for d in dense if np.isnan(d)]) > 0

        if (
            not has_nan and
            max_dense > min_f16 and max_dense < max_f16 and
            min_dense > min_f16 and min_dense < max_f16
        ):
            tile_value = {
                'dense': base64.b64encode(dense.astype('float16')).decode('utf-8'),
                'dtype': 'float16'
            }
        else:
            tile_value = {
                'dense': base64.b64encode(dense.astype('float32')).decode('utf-8'),
                'dtype': 'float32'
            }

        generated_tiles += [(tile_id, tile_value)]
    return generated_tiles

def chromsizes(filename):
    '''
    Get a list of chromosome sizes from this [presumably] bigwig
    file.

    Parameters:
    -----------
    filename: string
        The filename of the bigwig file

    Returns
    -------
    chromsizes: [(name:string, size:int), ...]
        An ordered list of chromosome names and sizes
    '''
    try:
        chrom_series = get_chromsizes(filename)
        data = []
        for chrom, size in chrom_series.iteritems():
            data.append([chrom, size])
        return data
    except Exception as ex:
        logger.error(ex)
        raise Exception('Error loading chromsizes from bigwig file: {}'.format(ex))
