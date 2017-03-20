import base64
import configparser
import gzip
import os
import re
import shutil
import sys
import time

from opensubtitles import OpenSubtitles


class Subtitler:
    VID_MATCH_PATTERN = '(.*)\.(avi|mkv|mp4)$'
    SUB_MATCH_PATTERN = '(.*)\.(srt|ass)$'

    def __init__(self):
        self.opensubtitles = OpenSubtitles()
        self.cp = configparser.ConfigParser()
        self.subtitle_languages = None
        self.choose_subtitle = None

        self.vid_sub_dict = {}

        self.parse_config()

    def parse_config(self):
        self.cp.read('subtitler.conf', encoding='UTF-8')
        languages = self.cp['SubtitleDownloader']['languages']
        if languages is None:
            languages = 'eng'
        self.subtitle_languages = languages.split(',')
        self.choose_subtitle = int(self.cp['SubtitleDownloader']['chooseSubtitle'])

    def main(self):
        videos = []
        subtitles = []

        if len(sys.argv) > 1:
            for arg in sys.argv[1:]:
                self.init_path_args(arg, videos, subtitles)
        else:
            print("Usage: {:s} [video|directory]...".format(os.path.basename(sys.argv[0])))
            sys.exit(1)

        self.match_videos_subs(videos, subtitles)
        del videos
        del subtitles

        self.process_videos_subs()

        print("Done!")
        sys.exit(0)

    def init_path_args(self, base_path, videos, subtitles):
        if os.path.exists(base_path) and os.path.isdir(base_path):
            for filename in os.listdir(base_path):
                absolute_path = os.path.join(base_path, filename)
                if os.path.isdir(absolute_path):
                    self.init_path_args(absolute_path, videos, subtitles)
                else:
                    self.detect_file_type(absolute_path, videos, subtitles)
        elif os.path.exists(base_path) and os.path.isfile(base_path):
            self.detect_file_type(base_path)
        else:
            print("No such file or directory: {:s}".format(base_path))

    @staticmethod
    def detect_file_type(file, videos, subtitles):
        vid_match = re.search(Subtitler.VID_MATCH_PATTERN, file, re.IGNORECASE)
        sub_match = re.search(Subtitler.SUB_MATCH_PATTERN, file, re.IGNORECASE)

        if vid_match:
            videos.append(file)
        elif sub_match:
            subtitles.append(file)

    def match_videos_subs(self, videos, subtitles):
        for video in videos:
            self.vid_sub_dict[video] = []
            video_season_episode = self.get_episode(video)
            for subtitle in subtitles:
                sub_season_episode = self.get_episode(subtitle)
                if video_season_episode[0] == sub_season_episode[0] and video_season_episode[1] == sub_season_episode[1]:
                    self.vid_sub_dict[video].append(subtitle)
                    break

    @staticmethod
    def get_episode(filename):
        season = 0
        episode = 0

        input_match = re.search('(\s|-|_|\.|\[|\()(\d{1,2})(\s|-|_|\.|\]|\))', filename, re.IGNORECASE)
        if input_match:
            episode = input_match.group(2)
        input_match = re.search('(\s|-|_|\.|\[|\()(\d{1,2})(\d{2})(\s|-|_|\.|\]|\))', filename, re.IGNORECASE)
        if input_match:
            season = input_match.group(2)
            episode = input_match.group(3)
        input_match = re.search('(\s|-|_|\.|\[|\()(\d{1,2})x(\d{2})(\s|-|_|\.|\]|\))', filename, re.IGNORECASE)
        if input_match:
            season = input_match.group(2)
            episode = input_match.group(3)
        input_match = re.search('s(\d{1,2})e(\d{1,2})', filename, re.IGNORECASE)
        if input_match:
            season = input_match.group(1)
            episode = input_match.group(2)

        return [str(season), str(episode)]

    def process_videos_subs(self):
        for video, subtitles in self.vid_sub_dict.items():
            if len(subtitles) == 0:
                self.download_missing_subs(video)
            else:
                processed_subtitles = []
                for subtitle in subtitles:
                    self.encode_sub(subtitle)
                    renamed_subtitle = self.rename_sub(video, subtitle)
                    processed_subtitles.append(renamed_subtitle)
                self.vid_sub_dict[video] = processed_subtitles

    def download_missing_subs(self, video):
        print("Searching subtitles for video: {:s}".format(video))
        vid_hash = self.opensubtitles.hash(video)
        for lang in self.subtitle_languages:
            sub_infos = self.opensubtitles.search_subtitles([{'sublanguageid': lang, 'moviehash': vid_hash,
                                                              'moviebytesize': str(os.path.getsize(video))}])
            if sub_infos:
                sub_index = self.choose_subtitle_to_download(sub_infos, lang)
                fetched_subtitle = self.fetch_subtitle(sub_index, sub_infos)
                vid_match = re.search(self.VID_MATCH_PATTERN, video, re.IGNORECASE)
                if vid_match:
                    vid_name = vid_match.group(1)

                    sub_file_name = vid_name + '.' + lang + '.srt'
                    print("Writing subtitle to file: {:s}".format(sub_file_name))
                    self.write_subtitle_file(fetched_subtitle, sub_file_name)
                    self.encode_sub(sub_file_name)
                    self.vid_sub_dict[video].append(sub_file_name)
                else:
                    print("Couldn't download subtitle for video {:s} with language {:s}".format(video, lang))
            else:
                print("No subtitles found for video {:s} with language {:s}".format(video, lang))

    def choose_subtitle_to_download(self, sub_infos, lang):
        if self.choose_subtitle and len(sub_infos) > 1:
            print("Language: {:s}".format(lang))
            for sub_info in sub_infos:
                print("[{:d}] {:s}".format(sub_infos.index(sub_info), sub_info.get('SubFileName')))

        sub_index = 0
        valid_input = False
        while not valid_input:
            try:
                sub_index_input = input("Select a subtitle: ")
                sub_index = int(sub_index_input)
                if sub_index < len(sub_infos):
                    valid_input = True
            except ValueError:
                pass
        return sub_index

    def fetch_subtitle(self, sub_index, sub_infos):
        print("Downloading subtitle: {:s}".format(sub_infos[sub_index].get('SubFileName')))
        fetched_subtitles = self.opensubtitles.download_subtitle([sub_infos[sub_index].get('IDSubtitleFile')])
        if fetched_subtitles:
            fetched_subtitle = fetched_subtitles[0].get('data')
            return fetched_subtitle
        else:
            return None

    def rename_sub(self, video, subtitle):
        vid_match = re.search(self.VID_MATCH_PATTERN, video, re.IGNORECASE)
        sub_match = re.search(self.SUB_MATCH_PATTERN, subtitle, re.IGNORECASE)

        if vid_match and sub_match:
            vid_name = vid_match.group(1)
            sub_name = sub_match.group(1)
            sub_ext = sub_match.group(2)

            new_sub_name = vid_name + '.' + sub_ext
            print("Renaming subtitle: {:s} --> {:s}".format(sub_name + sub_ext, new_sub_name))
            shutil.move(subtitle, new_sub_name)
            return new_sub_name

    @staticmethod
    def write_subtitle_file(data, file):
        file_data = base64.b64decode(data)
        byte = gzip.decompress(file_data)

        try:
            with open(file, 'bw+') as subtitle:
                subtitle.write(byte)
        except IOError:
            print("Couldn't write subtitle file")

    @staticmethod
    def encode_sub(subtitle):
        temp = os.path.dirname(subtitle) + '/' + str(time.time()) + '.tmp'
        try:
            with open(subtitle, encoding='UTF-8') as input_sub:
                data = input_sub.read()
        except IOError:
            with open(subtitle, encoding='ISO-8859-1') as input_sub:
                data = input_sub.read()

        print("Encoding subtitle {:s} to UTF-8".format(subtitle))
        with open(temp, 'w+', encoding='UTF-8') as output:
            output.write(data)

        input_sub.close()
        output.close()

        shutil.move(temp, subtitle)


if __name__ == '__main__':
    subtitler = Subtitler()
    subtitler.main()
