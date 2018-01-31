def bigwig_tsinfo(bwpath):
    '''
    Get the tileset info for a bigWig file

    Parameters
    ----------
    tileset: tilesets.models.Tileset object
        The tileset that the tile ids should be retrieved from

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


def bigwig_tiles(bwpath, tile_ids):
    '''
    Generate tiles from a bigwig file.

    Parameters
    ----------
    tileset: tilesets.models.Tileset object
        The tileset that the tile ids should be retrieved from
    tile_ids: [str,...]
        A list of tile_ids (e.g. xyx.0.0) identifying the tiles
        to be retrieved

    Returns
    -------
    tile_list: [(tile_id, tile_data),...]
        A list of tile_id, tile_data tuples
    '''
    import base64
    TILE_SIZE = 1024
    generated_tiles = []
    for tile_id in tile_ids:
        tile_id_parts = tile_id.split('.')
        tile_position = list(map(int, tile_id_parts[1:3]))
        zoom_level = tile_position[0]
        tile_pos = tile_position[1]
        
        # this doesn't combine multiple consequetive ids, which
        # would speed things up
        max_depth = tilesets.bigwig_tiles.get_quadtree_depth(tilesets.bigwig_tiles.get_chromsizes(bwpath))
        tile_size = TILE_SIZE * 2 ** (max_depth - zoom_level)
        start_pos = tile_pos * tile_size
        end_pos = start_pos + tile_size
        dense = tilesets.bigwig_tiles.get_bigwig_tile(bwpath, zoom_level, start_pos, end_pos)

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

