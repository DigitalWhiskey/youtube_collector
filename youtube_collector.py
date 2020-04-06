#!/usr/bin/env/python
# coding: utf-8

#  YouTube Data API Collector
#  Mat Morrison @mediaczar
#  Last updated: 2020-03-31

''' Query the YouTube Data API for an individual channel URL or a file list of URLs.
You may also specify which 'page' you'd like to start on (useful when the script
breaks during a long data capture.)

You _must_ supply a URL or file handle at the command line.

Data collected:
* publication date
* title
* description
* duration (ISO8601 duration format - parsed with [isodate](https://pypi.python.org/pypi/isodate))
* view count
* comment count
* likes & dislikes

To run it, you'll need:

1. a very basic knowledge of Python

2. some ability to install Python libraries (for legacy reasons,
I'm using a somewhat non-standard library called
[scraperwiki](https://pypi.python.org/pypi/scraperwiki) to save the data.)

3. (to read the output) some basic knowledge of SQL and
[SQLite](https://www.sqlite.org/) (it comes as standard on OS X,
and I use the excellent [Base 2](https://menial.co.uk/base/) to manage and
query the files that this script produces.)

4. an API Key from the Google Developers site
(get it here: [Google Developer Console](https://console.developers.google.com/)) -
add to SET UP. Take care not to share this publicly.
'''

import requests
import json
import scraperwiki
import isodate
import sys
import argparse


def get_file_contents(filename):
    """ Given a filename,
        return the contents of that file
    """
    try:
        with open(filename, 'r') as f:
            # It's assumed our file contains a single line,
            # with our API key
            return f.read().strip()
    except FileNotFoundError:
        print("'%s' file not found" % filename)


def load_data(request):
    x = json.loads(requests.get(request).text)
    return x


def get_author(url):
    elements = url.split("/")
    elements = [i for i in elements if i] # remove 'None' values
    
    if len(elements) > 3:
        author = elements[3]
        print(author)

        if elements[2] == "channel":
            authortype = "id"
        elif elements[2] == "user":
            authortype = "forUsername"
        else:
            sys.exit('malformed URL: %s' % url)
            
    else:
        author = elements[2]
        authortype = "channel"
    

    return author, authortype


def build_channel_request(author, authortype):
    part = 'snippet,contentDetails,statistics,id'
    field_items = ['snippet(title, publishedAt, description)',
                   'contentDetails/relatedPlaylists/uploads',
                   'statistics(subscriberCount,videoCount,viewCount)',
                   'id']
    x = ('https://www.googleapis.com/youtube/v3/' +
         'channels?part=' + part +
         '&fields=items(' + ','.join(field_items) + ')&' +
         authortype + '=' + author +
         '&key=' + API_key)
    return x


def write_channel(json):
    channel = {}
    channel['id'] = json['items'][0]['id']
    channel['title'] = title
    channel['uploads'] = uploadsId
    channel['subscriberCount'] = json['items'][0]['statistics']['subscriberCount']
    channel['videoCount'] = json['items'][0]['statistics']['videoCount']
    channel['publishedAt'] = json['items'][0]['snippet']['publishedAt']
    channel['description'] = json['items'][0]['snippet']['description']

    scraperwiki.sqlite.save(unique_keys=['id'], table_name='channel', data=channel)


def initialise_playlist(uploadsId):
    part = 'snippet,contentDetails'
    field_items = ['snippet(title, publishedAt, description)',
                   'contentDetails(videoId, duration)',
                   'nextPageToken']
    max_results = '50'

    x = ('https://www.googleapis.com/youtube/v3/' +
         'playlistItems?playlistId=' + uploadsId +
         '&part=' + part +
         #  '&fields=items(' + ','.join(field_items) + ')' +
         '&maxResults=' + max_results +
         '&key=' + API_key)
    return x

    print('getting channel data for: %s' % url)  # log progress


def gather_channel(url):
    global title
    global uploadsId
    author, authortype = get_author(url)
    API_request = build_channel_request(author, authortype)
    channel_data = load_data(API_request)
#   verify data in case bad url
    try:
        title = channel_data['items'][0]['snippet']['title']
    except:
        print("bad URL")
        return
#   need following to get playlistId
    uploadsId = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    write_channel(channel_data)

    print('...complete')  # log progress

    # now create a list of the videos for that channel
    print('collecting uploads for: %s (playlist ID: %s)' % (title, uploadsId))     # log progress
    API_request_base = initialise_playlist(uploadsId)

    # test to see if a page has been submitted as a command line option
    if args.page:
        page_token = args.page[0]
    else:
        page_token = ''

    # loop through the playlist collecting video data
    gather_video_data(API_request_base, page_token)


def gather_video_data(API_request_base, page_token):
    global videodata
    while True:
        paging_request = API_request_base + '&pageToken=' + page_token

        if page_token == '':
            print('gathering first page of %s' % title)
        else:
            print('gathering %s page %s' % (title, page_token))

        videos = load_data(paging_request)
        vcount = 1
        videodata = {}
        videodata['channel'] = title

        for video in videos['items']:
            write_video(video)

            if vcount > 1:
                # log progress
                print('\033[1A...completed ' + str(vcount))  # cursor up
            else:
                print('...completed ' + str(vcount))
            vcount += 1

        try:
            # log progress
            print('...gathering next page of videos')
            page_token = videos['nextPageToken']
        except:
            print('...last page reached')
            page_token = ''
            break


def write_video(json):
    videodata['videoId'] = json['contentDetails']['videoId']
    videodata['title'] = json['snippet']['title']
    videodata['publishedAt'] = json['snippet']['publishedAt']
    videodata['description'] = json['snippet']['description']

    video_request = ('https://www.googleapis.com/youtube/v3/' +
                     'videos?part=statistics,contentDetails&id=' +
                     videodata['videoId'] +
                     '&key=' + API_key)

    stats_json = load_data(video_request)
    for stat in ['viewCount', 'likeCount', 'dislikeCount', 'commentCount']:
        try:
            videodata[stat] = int(stats_json['items'][0]['statistics'][stat])
        except:
            videodata[stat] = None

    duration = isodate.parse_duration(stats_json['items'][0]['contentDetails']['duration']).total_seconds()
    videodata['duration'] = duration
    scraperwiki.sqlite.save(unique_keys=['videoId'], table_name='videos', data=videodata)

# SET UP
# credentials
API_key = get_file_contents("api_key")  # obtain from Google Developer Console, store in api_key locally

# parse arguments at command line

parser = argparse.ArgumentParser(description="""Query the YouTube Data API for an individual channel URL or a file list of URLs.
You may also specify which 'page' you'd like to start on (useful when the script breaks during a long data capture.)
You *must* supply a URL or file handle at the command line.""")

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-u", "--url", nargs=1, type=str, help="url of YouTube channel")
group.add_argument("-f", "--file", nargs=1, type=str, help="file list of URLs")

parser.add_argument("-p", "--page", nargs=1, type=str, help="page code")

args = parser.parse_args()

if args.file:
    f = open(args.file[0])
    urls = [url.rstrip('\n') for url in f]
    f.close
elif args.url:
    urls = args.url


# iterate through the URLs collecting basic channel data
for url in urls:
    print("gathering %s" % url)
    gather_channel(url)
    