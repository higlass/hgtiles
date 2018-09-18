import hgtiles.format as hgfo
import pandas as pd

import numpy as np
import pandas as pd
import h5py

def csv_to_points(csv_file, output_file):
    '''
    Convert a csv file containing points to a numpy array 
    of [[x,y]] values.

    Parameters:
    -----------
    csv_file: string 
        The filename of the data file 

    '''
    df = pd.read_table(csv_file, delimiter=',')

    print("dataframe", df.head(), df.columns.values)
    
    min_x = df['x'].min()
    max_x = df['x'].max()
    min_y = df['y'].min()
    max_y = df['y'].max()
    
    width = max_x - min_x
    height = max_y - min_y
    
    max_width = min(width, height)
    max_zoom = 30
    
    with h5py.File(output_file, 'w') as f_out:
        dataset = f_out.create_dataset('values', (len(df), 2), compression='gzip', dtype=np.float32)
        dataset[:] = df.reindex(columns=['x','y']).as_matrix()
        
        dataset.attrs['min_x'] = min_x
        dataset.attrs['max_x'] = max_x
        dataset.attrs['min_y'] = min_y
        dataset.attrs['max_y'] = max_y
        dataset.attrs['max_zoom'] = max_zoom
        dataset.attrs['max_width'] = max_width

    
    info = {
        'min_pos': [min_x, min_y],
        'max_pos': [min_y, max_y],
        'max_zoom': max_zoom,
        'max_width': max_width
    }
    
    return df.reindex(columns=['x', 'y'])

def tileset_info(points_file):
    '''
    Calculate the extent, etc...
    '''
    print("points file:", points_file)

    with h5py.File(points_file, 'r') as f_in:
        dset = f_in['values']
        
        return {
            'min_pos': [float(dset.attrs['min_x']), float(dset.attrs['min_y'])],
            'max_pos': [float(dset.attrs['max_y']), float(dset.attrs['max_y'])],
            'max_width': float(dset.attrs['max_width']),
            'max_zoom': int(dset.attrs['max_zoom']),
            'mirror_tiles': 'false'
        }

def tile_bounds(points_file, z, x, y):
    '''
    Get the boundaries of a tile
    
    Parameters:
    -----------
    tileset_info: { min_pos, max_pos, max_width}
        Information about the bounds of this tileset
    '''
    tsinfo = tileset_info(points_file)
    tile_width = tsinfo['max_width'] / 2 ** z
    print("tile_width:", tile_width)

        
    x_start = tsinfo['min_pos'][0] + tile_width * x
    x_end = tsinfo['min_pos'][0] + tile_width * (x+1)
    y_start = tsinfo['min_pos'][1] + tile_width * y
    y_end = tsinfo['min_pos'][1] + tile_width * (y+1)
    
    return (x_start, x_end, y_start, y_end)
    
def filter_points(data, extent):
    '''
    Filter points that are within the extent
    
    Parameters:
    -----------
    data: [[]]
        A 2D numpy array containing x,y values
        
    extent: [x_start, x_end, y_start, y_end]
        The region we want to return points within
        
    Returns
    -------
    data: [[]]
        A 2D numpy array containing x,y values
    '''
    # print("extent:", extent)
    # print("data.shape", data.shape, data[:,0])

    print("data:", data[:10])

    data = data[data[:,0] > extent[0]]
    data = data[data[:,0] < extent[1]]
    
    data = data[data[:,1] > extent[2]]
    data = data[data[:,1] < extent[3]]
        
    print("extent:", extent, "len(data):", len(data))

    return data

def density_tiles(points_file, z, x, y):
    with h5py.File(points_file, 'r') as f:
        filtered_points = filter_points(f['values'][:], 
                                        tile_bounds(points_file, z, x, y))
        dt = np.histogram2d(filtered_points[:,0], 
                              filtered_points[:,1], bins=256)[0].T
        dt[dt  == 0.] = np.nan
        return dt

def tiles(points_file, z, x, y):
    return hgfo.format_dense_tile(
        density_tiles(points_file, z, x, y).flatten(),
    )
