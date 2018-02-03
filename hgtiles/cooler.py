import base64
import collections as col
import cooler.contrib.higlass as cch
import hgtiles.utils as hgut
import h5py
import itertools as it
import numpy as np

global mats
mats = {}

def make_tiles(hdf_for_resolution, resolution, x_pos, y_pos, transform_type='default', x_width=1, y_width=1):
    '''
    Generate tiles for a given location. This function retrieves tiles for
    a rectangular region of width x_width and height y_width

    Parameters
    ---------
    hdf_for_resolution: h5py.File
        An HDF group containing the cooler for the given resolution
    x_pos: int
        The starting x position
    y_pos: int
        The starting y position
    cooler_file: string
        The filename of the cooler file to get the data from
    x_width: int 
        The number of tiles to retrieve along the x dimension
    y_width: int
        The number of tiles to retrieve along the y dimension

    Returns
    -------
    data_by_tilepos: {(x_pos, y_pos) : np.array}
        A dictionary of tile data indexed by tile positions
    '''
    BINS_PER_TILE = 256

    tile_size = resolution * BINS_PER_TILE

    start1 = x_pos * tile_size
    end1 = (x_pos + x_width) * tile_size
    start2 = y_pos * tile_size
    end2 = (y_pos + y_width) * tile_size

    '''
    print("transform_type:", transform_type);
    print('start1:', start1, end1)
    print('start2:', start2, end2)
    '''

    data = cch.get_data(
        hdf_for_resolution, start1, end1 - 1, start2, end2 - 1, 
        transform_type
    )

    #print("data:", data)

    #print("x_width:", x_width)
    #print("y_width:", y_width)
    # split out the individual tiles
    data_by_tilepos = {}

    for x_offset in range(0, x_width):
        for y_offset in range(0, y_width):

            start1 = (x_pos + x_offset) * tile_size
            end1 = (x_pos + x_offset+ 1) * tile_size
            start2 = (y_pos + y_offset) * tile_size
            end2 = (y_pos + y_offset + 1) * tile_size

            '''
            print("resolution:", resolution)
            print("tile_size", tile_size)
            print("x_pos:", x_pos, "x_offset", x_offset)
            print("start1", start1, 'end1', end1)
            print("start2", start2, 'end2', end2)
            '''

            df = data[data['genome_start1'] >= start1]
            df = df[df['genome_start1'] < end1]

            df = df[df['genome_start2'] >= start2]
            df = df[df['genome_start2'] < end2]

            binsize = resolution

            j = (df['genome_start1'].values - start1) // binsize
            i = (df['genome_start2'].values - start2) // binsize

            if 'balanced' in df:
                v = np.nan_to_num(df['balanced'].values)
            else:
                v = np.nan_to_num(df['count'].values)

            out = np.zeros(65536, dtype=np.float32)  # 256^2
            index = [int(x) for x in (i * 256) + j]

            if len(v):
                out[index] = v

            data_by_tilepos[(x_pos + x_offset, y_pos + y_offset)] = out

    return data_by_tilepos

def bin_tiles_by_zoom_level_and_transform(tile_ids):
    '''
    Place these tiles into separate lists according to their
    zoom level and transform type

    Parameters
    ----------
    tile_ids: [str,...]
        A list of tile_ids (e.g. xyx.0.0.1) identifying the tiles
        to be retrieved

    Returns
    -------
    tile_lists: {(zoomLevel, transformType): [tile_id, tile_id]}
        A dictionary of tile ids
    '''
    tile_id_lists = col.defaultdict(set)

    for tile_id in tile_ids:
        tile_id_parts = tile_id.split('.')
        tile_position = list(map(int, tile_id_parts[1:4]))
        zoom_level = tile_position[0]

        transform_method = get_transform_type(tile_id)


        tile_id_lists[(zoom_level, transform_method)].add(tile_id)

    return tile_id_lists

def get_transform_type(tile_id):
    '''
    Get the transform type specified in the tile id.
    Parameters
    ----------
    cooler_tile_id: str
        A tile id for a 2D tile (cooler)
    Returns
    -------
    transform_type: str
        The transform type requested for this tile
    '''
    tile_id_parts = tile_id.split('.')

    if len(tile_id_parts) > 4:
        transform_method = tile_id_parts[4]
    else:
        transform_method = 'default'

    return transform_method


def get_available_transforms(cooler):
    '''
    Get the available resolutions from a single cooler file.
    Parameters
    ----------
    cooler: h5py File
        A cooler file containing binned 2D data
    Returns
    -------
    transforms: dict
        A list of transforms available for this dataset
    '''
    transforms = set()

    f_for_zoom = cooler['bins']

    if 'weight' in f_for_zoom:
        transforms.add('weight')
    if 'KR' in f_for_zoom:
        transforms.add('KR')
    if 'VC' in f_for_zoom:
        transforms.add('VC')
    if 'VC_SQRT' in f_for_zoom:
        transforms.add('VC_SQRT')

    return transforms

def make_mats(filepath):
    '''
    Create the file handle and tileset info for a cooler 
    tileset
    '''
    f = h5py.File(filepath, 'r')

    if 'resolutions' in f:
        # this file contains raw resolutions so it'll return a different
        # sort of tileset info
        info = {"resolutions": tuple(sorted(map(int, list(f['resolutions'].keys())))) }
        mats[filepath] = [f, info]

        # see which transforms are available, a transform has to be
        # available at every available resolution in order for it to
        # be provided as an option
        available_transforms_per_resolution = {}

        for resolution in info['resolutions']:
            available_transforms_per_resolution[resolution] = get_available_transforms(f['resolutions'][str(resolution)])

        all_available_transforms = set.intersection(*available_transforms_per_resolution.values())

        info['transforms'] = [transform_descriptions[t] for t in all_available_transforms]

        # get the genome size
        resolution = list(f['resolutions'].keys())[0]
        genome_length = int(sum(f['resolutions'][resolution]['chroms']['length']))
        
        info['max_pos'] = [genome_length, genome_length]
        info['min_pos'] = [1,1]
        return (f, info)

    info = cch.get_info(filepath)

    info["min_pos"] = [int(m) for m in info["min_pos"]]
    info["max_pos"] = [int(m) for m in info["max_pos"]]
    info["max_zoom"] = int(info["max_zoom"])
    info["max_width"] = int(info["max_width"])

    if "transforms" in info:
        info["transforms"] = list(info["transforms"])

    mats[filepath] = [f, info]
    return (f, info)


def tileset_info(filepath):
    '''
    Get the tileset info for a cooler file

    Parameters:
    -----------

    filepath: str
        The location of the cooler file
    '''
    if filepath in mats:
        return mats[filepath][1]
    else:
        (f, info) = make_mats(filepath)

        return info

def format_cooler_tile(tile_data_array):
    '''
    Format raw cooler cooler data into a more structured tile
    containing either float16 or float32 data along with a 
    dtype to differentiate between the two.
    Parameters
    ----------
    tile_data_array: np.array
        An array containing a flattened 256x256 chunk of data
    Returns
    -------
    tile_data: {'dense': str, 'dtype': str}
        The tile data reformatted to use float16 or float32 as the
        datatype. The dtype indicates which format is chosen.
    '''

    tile_data = {}

    min_dense = float(np.min(tile_data_array))
    max_dense = float(np.max(tile_data_array))

    tile_data["min_value"] = min_dense
    tile_data["max_value"] = max_dense

    min_f16 = np.finfo('float16').min
    max_f16 = np.finfo('float16').max

    if (
        max_dense > min_f16 and max_dense < max_f16 and
        min_dense > min_f16 and min_dense < max_f16
    ):
        tile_data['dense'] = base64.b64encode(tile_data_array.astype('float16')).decode('latin-1')
        tile_data['dtype'] = 'float16'
    else:
        tile_data['dense'] = base64.b64encode(tile_data_array.astype('float32')).decode('latin-1')
        tile_data['dtype'] = 'float32'

    return tile_data

def add_transform_type(tile_id):
    '''
    Add a transform type to a cooler tile id if it's not already
    present.

    Parameters
    ----------
    tile_id: str
        A tile id (e.g. xyz.0.1.0)

    Returns
    -------
    new_tile_id: str
        A formatted tile id, potentially with an added transform_type
    '''
    tile_id_parts = tile_id.split('.')
    tileset_uuid = tile_id_parts[0]
    tile_position = tile_id_parts[1:4]

    transform_type = get_transform_type(tile_id)
    new_tile_id = ".".join([tileset_uuid] + tile_position + [transform_type])
    return new_tile_id

def tiles(filepath, tile_ids):
    '''
    '''
    transform_id_to_original_id = {}

    new_tile_ids = []

    for tile_id in tile_ids:
        new_tile_id = add_transform_type(tile_id)
        transform_id_to_original_id[new_tile_id] = tile_id
        new_tile_ids += [new_tile_id]

    generated_tiles = generate_tiles(filepath, new_tile_ids)
    
    tiles_to_return = []
    for tile_id, tile_value in generated_tiles:
        if tile_id in transform_id_to_original_id:
            original_tile_id = transform_id_to_original_id[tile_id]

            tiles_to_return += [(original_tile_id, tile_value)]

    return tiles_to_return


def generate_tiles(filepath, tile_ids):
    '''
    Generate tiles from a cooler file.
    Parameters
    ----------
    tileset: tilesets.models.Tileset object
        The tileset that the tile ids should be retrieved from
    tile_ids: [str,...]
        A list of tile_ids (e.g. xyx.0.0.1) identifying the tiles
        to be retrieved
    Returns
    -------
    generated_tiles: [(tile_id, tile_data),...]
        A list of tile_id, tile_data tuples
    '''
    BINS_PER_TILE = 256

    if filepath not in mats:
        # check if this tileset is open
        make_mats(filepath)

    tileset_file_and_info = mats[filepath]

    tile_ids_by_zoom_and_transform = bin_tiles_by_zoom_level_and_transform(tile_ids).values()
    partitioned_tile_ids = list(it.chain(*[hgut.partition_by_adjacent_tiles(t) 
        for t in tile_ids_by_zoom_and_transform]))

    generated_tiles = []

    for tile_group in partitioned_tile_ids:
        zoom_level = int(tile_group[0].split('.')[1])
        tileset_id = tile_group[0].split('.')[0]
        transform_type = get_transform_type(tile_group[0])
        tileset_info = tileset_file_and_info[1]
        tileset_file = tileset_file_and_info[0]

        if 'resolutions' in tileset_info:
            sorted_resolutions = sorted([int(r) for r in tileset_info['resolutions']], reverse=True)
            if zoom_level > len(sorted_resolutions):
                # this tile has too high of a zoom level specified
                continue

            resolution = sorted_resolutions[zoom_level]
            hdf_for_resolution = tileset_file['resolutions'][str(resolution)]
        else:
            if zoom_level > tileset_info['max_zoom']:
                # this tile has too high of a zoom level specified
                continue
            hdf_for_resolution = tileset_file[str(zoom_level)]
            resolution = (tileset_info['max_width'] / 2**zoom_level) / BINS_PER_TILE

        tile_positions = [[int(x) for x in t.split('.')[2:4]] for t in tile_group]

        # filter for tiles that are in bounds for this zoom level
        tile_positions = list(filter(lambda x: x[0] < tileset_info['max_pos'][0]+1, tile_positions))
        tile_positions = list(filter(lambda x: x[1] < tileset_info['max_pos'][1]+1, tile_positions))

        if len(tile_positions) == 0:
            # no in bounds tiles
            continue

        minx = min([t[0] for t in tile_positions])
        maxx = max([t[0] for t in tile_positions])

        miny = min([t[1] for t in tile_positions])
        maxy = max([t[1] for t in tile_positions])

        tile_data_by_position = make_tiles(hdf_for_resolution, 
                resolution,
                minx, miny, 
                transform_type,
                maxx-minx+1, maxy-miny+1)

        tiles = [(".".join(map(str, [tileset_id] + [zoom_level] + list(position) + [transform_type])), format_cooler_tile(tile_data))
                for (position, tile_data) in tile_data_by_position.items()]


        generated_tiles += tiles

    return generated_tiles
