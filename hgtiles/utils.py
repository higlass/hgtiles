def partition_by_adjacent_tiles(tile_ids, dimension=2):
    '''
    Partition a set of tile ids into sets of adjacent tiles

    Parameters
    ----------
    tile_ids: [str,...]
        A list of tile_ids (e.g. xyx.0.0.1) identifying the tiles
        to be retrieved
    dimension: int
        The dimensionality of the tiles

    Returns
    -------
    tile_lists: [tile_ids, tile_ids]
        A list of tile lists, all of which have tiles that
        are within 1 position of another tile in the list
    '''
    tile_id_lists = []

    for tile_id in sorted(tile_ids, key=lambda x: [int(p) for p in x.split('.')[2:2+dimension]]):
        tile_id_parts = tile_id.split('.')

        # exclude the zoom level in the position
        # because the tiles should already have been partitioned
        # by zoom level
        tile_position = list(map(int, tile_id_parts[2:4]))

        added = False

        for tile_id_list in tile_id_lists:
            # iterate over each group of adjacent tiles
            has_close_tile = False

            for ct_tile_id in tile_id_list:
                ct_tile_id_parts = ct_tile_id.split('.')
                ct_tile_position = list(map(int, ct_tile_id_parts[2:2+dimension]))
                far_apart = False

                # iterate over each dimension and see if this tile is close
                for p1,p2 in zip(tile_position, ct_tile_position):
                    if abs(int(p1) - int(p2)) > 1:
                        # too far apart can't be part of the same group
                        far_apart = True

                if not far_apart:
                    # no position was too far
                    tile_id_list += [tile_id]
                    added = True
                    break

            if added:
                break
        if not added:
            tile_id_lists += [[tile_id]]

    return tile_id_lists
