import sys
import os
import re
import time
import shutil

from opensubtitles import OpenSubtitles


class Subtitler:

    @staticmethod
    def download_subtitle(video, language):
        opensubtitles = OpenSubtitles()
        print("Searching subtitles for video: {:s}".format(video))
        vid_hash = opensubtitles.hash(video)
        sub_infos = opensubtitles.search_subtitles([{'sublanguageid': language, 'moviehash': vid_hash, 'moviebytesize': str(os.path.getsize(video))}])
        if sub_infos:
            print("Downloading subtitle: {:s}".format(sub_infos[0].get('SubFileName')))
            subtitles = opensubtitles.download_subtitle([sub_infos[0].get('IDSubtitleFile')])
            if subtitles:
                subtitle = subtitles[0].get('data')

                vid_match = re.search('(.*)\.(avi|mkv|mp4)$', video)
                if vid_match:
                    vid_name = vid_match.group(1)

                    sub_file = vid_name + '.' + language + '.srt'
                    print("Writing subtitle to file: {:s}".format(sub_file))
                    opensubtitles.write_subtitle_file(subtitle, sub_file)
                    return sub_file
                else:
                    print("Couldn't download subtitle for video {:s} with language {:s}".format(video, language))
                    return None
        else:
            print("No subtitles found for video {:s} with language {:s}".format(video, language))
            return None

    @staticmethod
    def get_episode(input_file):
        season = 0
        episode = 0

        input_match = re.search('(\s|-|_|\.|\[|\()(\d{1,2})(\s|-|_|\.|\]|\))', input_file)
        if input_match:
            episode = input_match.group(2)
        input_match = re.search('(\s|-|_|\.|\[|\()(\d{1,2})(\d{2})(\s|-|_|\.|\]|\))', input_file)
        if input_match:
            season = input_match.group(2)
            episode = input_match.group(3)
        input_match = re.search('s(\d{1,2})e(\d{1,2})', input_file)
        if input_match:
            season = input_match.group(1)
            episode = input_match.group(2)

        return [str(season), str(episode)]

    @staticmethod
    def rename_sub(video, subtitle):
        vid_match = re.search('(.*)\.(avi|mkv|mp4)$', video)
        sub_match = re.search('(.*)\.(srt|ass)$', subtitle)

        if vid_match and sub_match:
            vid_name = vid_match.group(1)
            sub_name = sub_match.group(1)
            sub_ext = sub_match.group(2)

            new_sub_name = vid_name + '.' + sub_ext
            print("Renaming subtitle: {:s} --> {:s}".format(sub_name + sub_ext, new_sub_name))
            shutil.move(subtitle, new_sub_name)

    @staticmethod
    def encode_sub(subtitle):
        temp = str(time.time()) + '.tmp'
        try:
            with open(subtitle, encoding='UTF-8') as input_sub:
                data = input_sub.read()
        except:
            with open(subtitle, encoding='ISO-8859-1') as input_sub:
                data = input_sub.read()

        print("Encoding subtitle {:s} to UTF-8".format(subtitle))
        with open(temp, 'w+') as output:
            # Removes BOM from UTF-8 file
            if data.startswith(u'\ufeff'):
                data = data[1:]
            output.write(data)

        input_sub.close()
        output.close()

        shutil.move(temp, subtitle)

    def main(self):
        arg_num = len(sys.argv)

        files = []
        videos = []
        subtitles = []

        working_dir = ''

        if arg_num > 2:
            for arg in sys.argv:
                files.append(arg)

            working_dir_matcher = re.search(r'(.*)(/|\\).*$', sys.argv[1])
            if working_dir_matcher:
                working_dir = working_dir_matcher.group(1)
        elif arg_num == 2:
            working_dir = sys.argv[1]

            if not (os.path.exists(working_dir) or os.path.isdir(working_dir)):
                print("Single argument must be a directory.\n")
                sys.exit(1)

            files = os.listdir(working_dir)

        for file in files:
            vid_match = re.search('(.*)\.(avi|mkv|mp4)$', file)
            sub_match = re.search('(.*)\.(srt|ass)$', file)

            if vid_match:
                videos.append(file)

            if sub_match:
                subtitles.append(file)

        if len(videos) == 0:
            print("No videos found!\n")
            sys.exit(1)

        os.chdir(working_dir)

        if len(videos) == 1:
            if len(subtitles) == 0:
                for video in videos:
                    subtitles.append(self.download_subtitle(video, 'hun'))
                    subtitles.append(self.download_subtitle(video, 'eng'))

                if len(subtitles) == 0:
                    print("No subtitles found!\n")
                    sys.exit(1)

                for subtitle in subtitles:
                    if subtitle is not None:
                        self.encode_sub(subtitle)
            elif len(subtitles) == 1:
                self.encode_sub(subtitles[0])
                self.rename_sub(videos[0], subtitles[0])

        else:
            if len(subtitles) == 0:
                for video in videos:
                    subtitles.append(self.download_subtitle(video, 'hun'))
                    subtitles.append(self.download_subtitle(video, 'eng'))

                    if len(subtitles) == 0:
                        print("No subtitles found!\n")
                        sys.exit(1)

                    for subtitle in subtitles:
                        if subtitle is not None:
                            self.encode_sub(subtitle)

                    subtitles.clear()
            else:
                for video in videos:
                    vid_season_ep = self.get_episode(video)
                    for subtitle in subtitles:
                        sub_season_ep = self.get_episode(subtitle)
                        if vid_season_ep[0] == sub_season_ep[0] and vid_season_ep[1] == sub_season_ep[1]:
                            self.encode_sub(subtitle)
                            self.rename_sub(video, subtitle)

        print("Done!")
        sys.exit(0)

if __name__ == '__main__':
    subtitler = Subtitler()
    subtitler.main()