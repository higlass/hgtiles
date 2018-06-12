import collections as col
import sqlite3

def list_items(db_file, start, end, max_entries=None):
    '''
    List the entries between start and end

    Parameters
    ----------
    db_file: str
        The filename of the sqlite db file
    start_pos: int
        The start position from where to retrieve data
    end_pos: int
        The end position to get data
    max_entries: int
        The maximum number of results to return
    '''

    conn = sqlite3.connect(db_file)

    c = conn.cursor()

    # some large number because we want to extract all entries
    zoom = 100000

    query = '''
    SELECT startPos, endPos, chrOffset, importance, fields, uid
    FROM intervals,position_index
    WHERE
        intervals.id=position_index.id AND
        zoomLevel <= {} AND
        rEndPos >= {} AND
        rStartPos <= {}
    '''.format(zoom, start, end)

    if max_entries is not None:
        query += ' LIMIT {}'.format(max_entries)

    rows = c.execute(query).fetchall()

    new_rows = []

    for r in rows:
        try:
            uid = r[5].decode('utf-8')
        except AttributeError:
            uid = r[5]

        new_rows += [
            # add the position offset to the returned values
            {'xStart': r[0],
             'xEnd': r[1],
             'chrOffset': r[2],
             'importance': r[3],
             'uid': uid,
             'fields': r[4].split('\t')}]
    conn.close()

    return new_rows
