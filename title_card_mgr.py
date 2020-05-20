#! /usr/bin/env python

import sys
import json
import glob
from copy import deepcopy
# This is a nominally empty playlist in Tidal's JSON format that
# has the minimun structure this script requires.
empty = {
        'items' : [{
            'item' : {
                'title' : '',
                'artists' : [],
                'album' : {
                    'title' : '',
                 },
                'copyright' : ''
            }
        }]
}
# Actual database entries, one per ID
database = {}
# Index by song name, value is an array of IDs
title_index = {}
# Index by artist, value is an array of IDs
artist_index = {}

def build_indexes():
    '''Build the song database and title and artist search indexes to
quickly locate songs by those criteria. 
'''
    global database
    global title_index
    global artist_index
    # the database is a collection of Tidal JSON format playlists
    db_files = glob.glob("./db/*.json")
    print("Loading database...", end=''),
    for fh in [open(i) for i in db_files]:
        new_file = json.load(fh)
        for i in new_file['items']:
            item = i['item']
            if item['id'] in database:
                continue
            if item['title'] in title_index:
                title_index[item['title'].lower()].append(item['id'])
            else:
                title_index[item['title'].lower()] = [item['id']]
            for artist in item['artists']:
                aname = artist['name'].lower()
                if aname in artist_index:
                    artist_index[aname].append(item['id'])
                else:
                    artist_index[aname] = [item['id']]
            database[item['id']] = item
    print("Load complete.")
    print(" Titles indexed: %i" % len(database))
    print(" Unique titles: %i" % len(title_index))
    print(" Unique artists: %i" % len(artist_index))

def get_track_by_index(search, index):
    '''Return items found given the text to search for in search,
using the index to be searched passed in index. Also prints the
entries found with that search and index combination.
'''
    ids = [index[i] for i in index if search in i]
    idl = []
    for i in ids:
        idl += i
    rtn = deepcopy(empty)
    if len(idl) > 0:
        rtn['items'] = []
    for track, i in enumerate(idl, start=1):
        rtn['items'].append({"item" :database[i]})
        print("Track %i: %s" % (track, build_title(database[i])))
        print("         %s" % build_artists(database[i]['artists']))
        print("         %s" % build_extra(database[i]))
    return rtn

def build_title(t):
    '''Returns the title of the song, optionally including version information
at the end in parentheses if present in the structure.
'''
    title = t['title']
    if 'version' in t and t['version']:
        title += " (" + t['version'] + ")"
    return title

def build_artists(a):
    '''Returns a string of all artist names, comma-separated, listed in the artist
structure of the item.
'''
    return ", ".join([i['name'] for i in a])

def build_extra(e):
    '''Returns a string containing the album name and any copyright information
of the song.
'''
    if e['copyright']:
        copyright = e['copyright'].split(',')[0]
        copyright = copyright.split(" under exclusive")[0]
        copyright = ", " + copyright
    else:
        copyright = ''
 
    return e['album']['title'] + copyright

def main(args):
    '''Main command processing loop.
'''
    build_indexes()
    if args:
        fn = args[0]
        o = json.load(open(fn))
    else:
        print("Database only mode. No initial playlist.")
        fn = None
        o = empty
    
    
    track = 0 
    while True:
        t = o['items'][track]['item']
        title = build_title(t)
        artists = build_artists(t['artists'])
        extra = build_extra(t)
        if len(extra) <= 2: extra = ''
        print("Track number: %i" % (track+1))
        print('-------')
        print(title)
        print(artists)
        print(extra)
        print('-------')
        # These are the files the OBS text components should be
        # pointing to.
        open("title.txt", "w").write(title)
        open("artists.txt", "w").write(artists)
        open("extra.txt", "w").write(extra)
        print("+ to advance track, - to back up track, number jump,")
        print("'t TEXT' to search all titles in db,")
        print("'a TEXT' to search all artists in db,")
        print("'f FILENAME' to load a playlist,")
        print("'q' to quit:")
        cmd = input("> ").lower()
        if cmd.startswith("q"): break
        if cmd.startswith("+"): track += 1
        if cmd.startswith("-"): track -= 1
        if cmd.startswith("t "):
            o = get_track_by_index(cmd[2:].strip(), title_index)
            track = 0
        if cmd.startswith("a "):
            o = get_track_by_index(cmd[2:].strip(), artist_index) 
            track = 0
        if cmd.startswith("f "):
            fnc = cmd[2:].strip()
            try:
                o = json.load(open(fnc))
                fn = fnc
                track = 0
            except OSError as e:
                print("ERROR: Couldn't open playlist %s: %s" % (fnc, e))
            except json.decoder.JSONDecodeError as e:
                print("ERROR: Couldn't parse JSON from playlist %s: %s" % (fnc, e))     
        try:
            track = int(cmd) - 1
        except ValueError: pass
        if track < 0: track = 0
        if track >= len(o['items']): track = len(o['items']) - 1
    
if __name__ == "__main__":
    main(sys.argv[1:])    
