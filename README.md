# HiGlass Tiles repository

This repository contains functions for serving tiles from various file formats.
The implementation of a tile API should be synchronized with the the creation
of the track for displaying the tiles. This requires implementing two functions:

```
def tileset_info(filepath):
  '''
  Return the necessary information about this tileset.
  
  This function could return, for example, the x and y bounds, available
  resolutions, available transforms, etc...
  
  It should be in the form of a dictionary.
```

And 

```
def generate_tiles(filepath, tile_ids):
  '''
  This should return a list of tiles in the form:
  
  [(tile_id, tile_value),...]
  '''
```

That's all. These functions can then be called from `higlass-server` to generate
the tiles passed to the client.
