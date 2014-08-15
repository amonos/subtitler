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
If there are multiple video (and subtitle) files in the arguments (or the input directory)
then they will be matched by season/episode number (eg.: series), or episode number
(eg.: animes).

Multiple videos whitout season/episode in the filename, or multiple CDs for a movie is not supported.

Python 3 required
