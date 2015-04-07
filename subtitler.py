import configparser
import sys
import os
import re
import time
import shutil

from opensubtitles import OpenSubtitles


class Subtitler:

    def __init__(self):
        self.cp = configparser.ConfigParser()
        self.subtitle_downloader_languages = None
        self.choose_subtitle = None
        self.parse_config()

    def parse_config(self):
        self.cp.read('subtitler.conf', encoding='UTF-8')
        languages = self.cp['SubtitleDownloader']['languages']
        self.subtitle_downloader_languages = languages.split(',')
        self.choose_subtitle = int(self.cp['SubtitleDownloader']['chooseSubtitle'])

    def download_subtitle(self, video, language):
        """
        Download subtitle from http://www.opensubtitles.org
        :param video:
        :param language:
        :return:
        """
        opensubtitles = OpenSubtitles()
        print("Searching subtitles for video: {:s}".format(video))
        vid_hash = opensubtitles.hash(video)
        sub_infos = opensubtitles.search_subtitles([{'sublanguageid': language, 'moviehash': vid_hash, 'moviebytesize': str(os.path.getsize(video))}])
        if sub_infos:
            sub_index = 0
            if self.choose_subtitle and len(sub_infos) > 1:
                print("Language: {:s}".format(language))
                for sub_info in sub_infos:
                    print("[{:d}] {:s}".format(sub_infos.index(sub_info), sub_info.get('SubFileName')))

                sub_index_input = input("Select a subtitle: ")
                valid_input = False
                while not valid_input:
                    try:
                        sub_index = int(sub_index_input)
                        valid_input = True
                    except:
                        valid_input = False

            print("Downloading subtitle: {:s}".format(sub_infos[sub_index].get('SubFileName')))
            subtitles = opensubtitles.download_subtitle([sub_infos[sub_index].get('IDSubtitleFile')])
            if subtitles:
                subtitle = subtitles[0].get('data')

                vid_match = re.search('(.*)\.(avi|mkv|mp4)$', video, re.IGNORECASE)
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

    def load_input(self, base_path, videos, subtitles):
        """
        Load video and subtitle files recursively, process them
        on a per directory basis
        :param base_path:
        :param videos:
        :param subtitles:
        :return:
        """
        if os.path.exists(base_path) and os.path.isdir(base_path):
            for file in os.listdir(base_path):
                abs_file = os.path.join(base_path, file)
                if os.path.isdir(abs_file):
                    self.load_input(abs_file, videos, subtitles)
                else:
                    self.detect_file_type(abs_file, videos, subtitles)
        elif os.path.exists(base_path) and os.path.isfile(base_path):
            self.detect_file_type(base_path, videos, subtitles)
        else:
            print("No such file or directory: {:s}".format(base_path))

        self.process_input(videos, subtitles)
        videos.clear()
        subtitles.clear()

    def process_input(self, videos, subtitles):
        """
        Process the video and subtitle files
        :param videos:
        :param subtitles:
        :return:
        """
        if len(videos) == 0:
            pass
        elif len(videos) == 1:
            if len(subtitles) == 0:
                # One video, no subtitles, download subtitles
                self.fetch_subtitles(videos, subtitles)
            elif len(subtitles) == 1:
                # One video, one subtitle, doesn't need to check season / episode
                self.encode_sub(subtitles[0])
                self.rename_sub(videos[0], subtitles[0])
            else:
                # One video, multiple subtitles, look for matching subtitle based on season / episode
                self.rename_subtitles(videos, subtitles)
        else:
            if len(subtitles) == 0:
                # Multiple videos, no subtitles, download subtitles
                self.fetch_subtitles(videos, subtitles)
            else:
                # Multiple videos, multiple subtitles, look for matching subtitles based on season / episode
                self.rename_subtitles(videos, subtitles)

    @staticmethod
    def rename_subtitles(videos, subtitles):
        """
        Rename existing subtitle files
        :param videos:
        :param subtitles:
        :return:
        """
        for video in videos:
            vid_season_ep = Subtitler.get_episode(video)
            for subtitle in subtitles:
                sub_season_ep = Subtitler.get_episode(subtitle)
                if vid_season_ep[0] == sub_season_ep[0] and vid_season_ep[1] == sub_season_ep[1]:
                    Subtitler.encode_sub(subtitle)
                    Subtitler.rename_sub(video, subtitle)

    @staticmethod
    def detect_file_type(file, videos, subtitles):
        """
        Put the file into the video or subtitle list based on it's extension.
        :param file:
        :param videos:
        :param subtitles:
        :return:
        """
        vid_match = re.search('(.*)\.(avi|mkv|mp4)$', file, re.IGNORECASE)
        sub_match = re.search('(.*)\.(srt|ass)$', file, re.IGNORECASE)

        if vid_match:
            videos.append(file)

        if sub_match:
            subtitles.append(file)

    @staticmethod
    def get_episode(input_file):
        """
        Extract season / episode number from filename.
        :param input_file:
        :return:
        """
        season = 0
        episode = 0

        input_match = re.search('(\s|-|_|\.|\[|\()(\d{1,2})(\s|-|_|\.|\]|\))', input_file, re.IGNORECASE)
        if input_match:
            episode = input_match.group(2)
        input_match = re.search('(\s|-|_|\.|\[|\()(\d{1,2})(\d{2})(\s|-|_|\.|\]|\))', input_file, re.IGNORECASE)
        if input_match:
            season = input_match.group(2)
            episode = input_match.group(3)
        input_match = re.search('(\s|-|_|\.|\[|\()(\d{1,2})x(\d{2})(\s|-|_|\.|\]|\))', input_file, re.IGNORECASE)
        if input_match:
            season = input_match.group(2)
            episode = input_match.group(3)
        input_match = re.search('s(\d{1,2})e(\d{1,2})', input_file, re.IGNORECASE)
        if input_match:
            season = input_match.group(1)
            episode = input_match.group(2)

        return [str(season), str(episode)]

    @staticmethod
    def rename_sub(video, subtitle):
        """
        Rename subtitle file to match video file's name.
        :param video:
        :param subtitle:
        :return:
        """
        vid_match = re.search('(.*)\.(avi|mkv|mp4)$', video, re.IGNORECASE)
        sub_match = re.search('(.*)\.(srt|ass)$', subtitle, re.IGNORECASE)

        if vid_match and sub_match:
            vid_name = vid_match.group(1)
            sub_name = sub_match.group(1)
            sub_ext = sub_match.group(2)

            new_sub_name = vid_name + '.' + sub_ext
            print("Renaming subtitle: {:s} --> {:s}".format(sub_name + sub_ext, new_sub_name))
            shutil.move(subtitle, new_sub_name)

    @staticmethod
    def encode_sub(subtitle):
        """
        Encode subtitle file to UTF-8.
        :param subtitle:
        :return:
        """
        temp = os.path.dirname(subtitle) + '/' + str(time.time()) + '.tmp'
        try:
            with open(subtitle, encoding='UTF-8') as input_sub:
                data = input_sub.read()
        except:
            with open(subtitle, encoding='ISO-8859-1') as input_sub:
                data = input_sub.read()

        print("Encoding subtitle {:s} to UTF-8".format(subtitle))
        with open(temp, 'w+', encoding='UTF-8') as output:
            output.write(data)

        input_sub.close()
        output.close()

        shutil.move(temp, subtitle)

    def fetch_subtitles(self, videos, subtitles):
        """
        Try to download subtitles for the video file
        :param videos:
        :param subtitles:
        :return:
        """
        for video in videos:
            languages = self.subtitle_downloader_languages
            if languages is not None:
                for lang in languages:
                    subtitles.append(self.download_subtitle(video, lang))

        if len(subtitles) == 0:
            print("No subtitles found!\n")
            sys.exit(1)

        for subtitle in subtitles:
            if subtitle is not None:
                Subtitler.encode_sub(subtitle)
        subtitles.clear()

    def main(self):
        videos = []
        subtitles = []

        arg_num = len(sys.argv)

        if arg_num > 1:
            for arg in sys.argv:
                self.load_input(arg, videos, subtitles)
        else:
            print("Usage: {:s} [video|directory]...".format(os.path.basename(sys.argv[0])))
            sys.exit(1)

        self.process_input(videos, subtitles)

        print("Done!")
        sys.exit(0)

if __name__ == '__main__':
    subtitler = Subtitler()
    subtitler.main()
