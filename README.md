subtitler
=========

Introduction:
-------------
Renames subtitle files to match the video's filename, encodes the subtitles to UTF-8,
and downloads subtitles from http://www.opensubtitles.org if there isn't any subtitle
in the video's directory.

Usage:
------
```
$ python subtitler.py [video_file|directory]...
```
Valid command line arguments:
* One or more video files and/or directories containing video files (and optionally subtitle files).

Configuration:
--------------
You can configure the application through the subtitler.conf file.

### Properties: ###
* langauges=[hun|eng|...],... : Defines the subtitle languages the application will search for when downloading subtitles (Uses ISO639 codes).
* chooseSubtitle=[0|1] : Setting this property to 1 will let the user choose wich file to download if there is more than 1 subtitle found,
  setting this to 0 will download the first match.

Additional information:
-----------------------
* Directories are read recursively
* If there are multiple video files (and optionally subtitle files) in a directory then they will be matched by season and episode information
  in the filenames.
* Multiple videos whitout season and episode information in the filename, or multiple CDs for a movie is not supported in the same directory.
* Python 3.4 required
