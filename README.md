subtitler
=========

Introduction:

Renames subtitle files to match the video's filename, encodes the subtitles to UTF-8,
and downloads hungarian and english subtitles from http://www.opensubtitles.org if
there isn't any subtitle files in the commandline arguments.


Usage:

python subtitler.py <video1.mkv> <sub1.srt> <video2.mp4> <sub2.ass> <video3.avi> <sub3.srt>

or

python subtitler.py </path/to/video/files>


Additional information:

If there are multiple video (and subtitle) files in the arguments (or the input directory)
then they will be matched by season/episode number (eg.: series), or episode number
(eg.: animes).

Multiple videos whitout season/episode in the filename, or multiple CDs for a movie is not supported.
