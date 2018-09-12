import collections as col
import json
import os
import os.path as op
import random
import sqlite3
import sys

def csv_to_hg(csv_file, output_file, delimiter=','):
    conn = sqlite3.connect(output_file)

    conn.execute('''
    CREATE TABLE data_info (
        minX NUMBER,
        maxX NUMBER,
        minY NUMBER,
        maxY NUMBER,
        maxZoom INT,
        numPoints INT,
        maxWidth NUMBER )
    ''')

    conn.execute('''
        CREATE TABLE points
        (
            id int PRIMARY KEY,
            x NUMBER,
            y NUMBER,
            importance NUMBER,
            data TEXT
        )
        ''')
    
    conn.execute('''
    CREATE INDEX points_importance ON points ( importance )
    ''')
    
    conn.execute('''
        CREATE VIRTUAL TABLE points_index USING rtree(
            id, 
            minX, maxX,
            minY, maxY,
            minZ, maxZ
        )
        ''')

    min_x, min_y = sys.maxsize, sys.maxsize
    max_x, max_y = -sys.maxsize, -sys.maxsize
    points = []
    
    # go through the file once to calculate the extent
    with open(csv_file, 'r') as f:
        # skip the header
        f.readline()
        
        for i,line in enumerate(f):
            parts = line.strip().split(delimiter)
            #print("parts:", parts)
            x = float(parts[0])
            y = float(parts[1])
            point = {
                'uid': i,
                'pos': [x, y],
                'importance': random.random(),
                'data': parts[2]
            }
            
            min_x = x if x < min_x else min_x
            max_x = x if x > max_x else max_x
            min_y = y if y < min_y else min_y
            max_y = y if y > max_y else max_y
            
            points += [point]
            
    extent = [min_x, min_y, max_x, max_y]
    
    width = extent[2] - extent[0]
    height = extent[3] - extent[1]
    
    max_width = max(width, height)
    max_zoom = 20
    max_per_tile = 100
    tile_counts = col.defaultdict(int)
    
    # go through and assign zoom levels to each point

    counter = 0
    sorted_points = sorted(points, key=lambda x: -x['importance'])
    for point in sorted_points:
        curr_zoom = 0
        
        while curr_zoom <= max_zoom:
            tile_width = max_width / 2 ** curr_zoom
            x,y = point['pos']
            
            tile_x, tile_y = (int((x - min_x) // tile_width), 
                              int((y - min_y) // tile_width))
            #print("tile_x:", tile_x, "tile_y:", tile_y)

            
            if tile_counts[(curr_zoom, tile_x, tile_y)] < max_per_tile:
                # there's space in this tile, so add this point
                tile_counts[(curr_zoom, tile_x, tile_y)] += 1
                point['zoom'] = curr_zoom
                conn.execute(
                '''
                INSERT INTO points
                VALUES (?,?,?,?,?)
                ''', (
                    counter,
                    point['pos'][0],
                    point['pos'][1],
                    point['importance'],
                    json.dumps(point)
                ))
                
                #if curr_zoom == 2 and tile_x == 0 and tile_y == 1:
                #    print("hi", i, curr_zoom, x, y, tile_x, tile_y)                
                conn.execute(
                'INSERT INTO points_index VALUES(?,?,?,?,?,?,?)',
                (counter, x, x, y, y, counter, counter))
                
                counter += 1
                break

            # not enough space so go onto the next zoom level
            curr_zoom += 1
                
    max_zoom = 30
    num_points = counter 

    conn.execute('''
    INSERT INTO data_info
    VALUES (?,?,?,?,?,?,?)
    ''',
    (extent[0], extent[1],
        extent[2], extent[3],
        max_zoom, num_points, max_width))

    conn.commit()
    conn.close()
    
    return {
        "data": sorted_points,
        "conn": conn,
        "extent": extent,
        "min_pos": [extent[0], extent[1]],
        "max_pos": [extent[2], extent[3]],
        "max_width": max_width,
        "max_zoom": max_zoom, # arbitrary large value
        "num_points": counter
    }
    return conn

def tileset_info(db_file):
    conn = sqlite3.connect(db_file)
    
    row = conn.execute('''
        SELECT * from data_info
        ''').fetchone()

    return {
        'min_pos': [row[0], row[1]],
        'max_pos': [row[2], row[3]],
        'max_zoom': row[4],
        'num_points': row[5],
        'max_width': row[6] 
    }
    

def tiles(filename, z, x, y, max_points=40):
    hg_points = tileset_info(filename)
    conn = sqlite3.connect(filename)

    area_width = hg_points['max_width'] / 2 ** z
    extent = hg_points['min_pos'] + hg_points['max_pos']
    
    min_x = extent[0] + area_width * x
    max_x = extent[0] + area_width * (x+1)
    min_y = extent[1] + area_width * y
    max_y = extent[1] + area_width * (y+1)
    min_z = -1
    
    
    print("minx", min_x, min_y, max_x, max_y)

    points_to_return = []
    
    while len(points_to_return) < max_points and z < hg_points['max_zoom']:
        max_z = 30 * 2 ** (z+1)

        #print("max_z:", max_z)

        query = '''
        SELECT x,y,importance,data 
        FROM points, points_index
        WHERE 
            points.id = points_index.id AND
            maxX >= {} AND
            maxY >= {} AND
            maxZ >= {} AND
            minX < {} AND
            minY < {} AND
            minZ < {}
        ORDER BY
            importance
        DESC
        LIMIT {}'''.format(min_x, min_y, min_z, max_x, max_y, max_z, max_points)
        #print("query:", query)

        c = conn.cursor()
        points_to_return = [json.loads(r[3]) for r in c.execute(query).fetchall()]
        #print("len:", len(points_to_return))
        #print("z:", z)
        z += 1
        z *= 2
        
    return points_to_return
