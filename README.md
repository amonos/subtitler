subtitler
=========

Introduction:
-------------
Renames subtitle files to match the video's filename, encodes the subtitles to UTF-8,
and downloads subtitles from http://www.opensubtitles.org if there isn't any subtitle
files in the commandline arguments.

Usage:
------
```
$ python subtitler.py [file|directory]...
```

Configuration:
--------------
You can configure the application throught the subtitler.conf file.

### Properties: ###
* langauges=[hun|eng|...],... : Defines the subtitle languages the application will search for when downloading subtitles (Uses ISO639 codes).
* chooseSubtitle=[0|1] : Setting this property to 1 will let the user choose wich file to download if there is more than 1 subtitle found,
  setting this to 0 will download the first match.

Additional information:
-----------------------
If there are multiple videos (and/or subtitles) on the input then they will be matched by
season/episode information in the filenames.

Multiple videos whitout season/episode information in the filename, or multiple CDs for a movie is not supported.

Python 3 required
