subtitler
=========

Introduction:
-------------
Renames subtitle files to match the video's filename, encodes the subtitles to UTF-8,
and downloads hungarian and english subtitles from http://www.opensubtitles.org if
there isn't any subtitle files in the commandline arguments.

Usage:
------
```
$ python subtitler.py [video|subtitle|directory]...
```

Additional information:
-----------------------
If there are multiple videos (and/or subtitles) on the input then they will be matched by
season/episode information in the filenames.

Multiple videos whitout season/episode information in the filename, or multiple CDs for a movie is not supported.

Python 3 required
