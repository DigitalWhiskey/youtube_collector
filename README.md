# youtube_collector
Collects public metadata from YouTube channels


Query the YouTube Data API for an individual channel URL or a file list of URLs.
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
add to SET UP. Store this in a file called `api_key` in the same directory as the `youtube_collector.py` script and take care not to share this publicly.
