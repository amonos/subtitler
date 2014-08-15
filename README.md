subtitler
=========

Introduction:
-------------
Renames subtitle files to match the video's filename, encodes the subtitles to UTF-8,
and downloads hungarian and english subtitles from http://www.opensubtitles.org if
there isn't any subtitle files in the commandline arguments.

Usage:
------
python subtitler.py &lt;video1.mkv&gt; &lt;sub1.srt&gt; &lt;video2.mp4&gt; &lt;sub2.ass&gt; &lt;video3.avi&gt; &lt;sub3.srt&gt;

or

python subtitler.py &lt;/path/to/video/files&gt;

Additional information:
-----------------------
If there are multiple video (and subtitle) files in the arguments (or the input directory)
then they will be matched by season/episode number (eg.: series), or episode number
(eg.: animes).

Multiple videos whitout season/episode in the filename, or multiple CDs for a movie is not supported.
