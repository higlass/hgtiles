import base64
import clodius.hdf_tiles as hdft
import h5py
import math
import numpy as np

def tileset_info(hitile_path):
    '''
    Get the tileset info for a hitile file.

    Parameters
    ----------
    hitile_path: string
        The path to the hitile file

    Returns
    -------
    tileset_info: {'min_pos': [], 
                    'max_pos': [], 
                    'tile_size': 1024, 
                    'max_zoom': 7
                    }
    '''
    hdf_file = h5py.File(hitile_path, 'r')

    d = hdf_file['meta']

    if "min-pos" in d.attrs:
        min_pos = d.attrs['min-pos']
    else:
        min_pos = 0

    if "max-pos" in d.attrs:
        max_pos = d.attrs['max-pos']
    else:
        max_pos = d.attrs['max-length']

    return {
                "max_pos": [int(max_pos)],
                'min_pos': [int(min_pos)],
                "max_width": 2 ** math.ceil(
                    math.log(max_pos - min_pos
                    ) / math.log(2)
                ),
                "max_zoom": int(d.attrs['max-zoom']),
                "tile_size": int(d.attrs['tile-size'])
            }

def tiles(filepath, tile_ids):
    '''
    Generate tiles from a hitile file.

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
    generated_tiles = []

    for tile_id in tile_ids:
        tile_id_parts = tile_id.split('.')
        tile_position = list(map(int, tile_id_parts[1:3]))

        dense = hdft.get_data(
            h5py.File(filepath),
            tile_position[0],
            tile_position[1]
        )

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

