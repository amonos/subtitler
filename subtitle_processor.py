import base64
import gzip
import os
import re
import shutil
import sys
import time

from opensubtitles import OpenSubtitles


class SubtitleProcessor:
    _vid_match_pattern = '(.*)\.(avi|mkv|mp4)$'
    _sub_match_pattern = '(.*)\.(srt|ass)$'

    _season_episode_patterns = [
        '\s|-|_|\.|\[|\(|\{(\d{1,2})\s|-|_|\.|\]|\)|\}',
        '\s|-|_|\.|\[|\(|\{(\d{1,2})(\d{2})\s|-|_|\.|\]|\)|\}',
        '\s|-|_|\.|\[|\(|\{(\d{1,2})x(\d{2})\s|-|_|\.|\]|\)|\}',
        's(\d{1,2})e(\d{1,2})'
    ]

    _supported_encodings = ['UTF-8', 'ISO-8859-1', 'ISO-8859-2', 'ASCII']

    def __init__(self, subtitle_languages, choose_subtitle):
        self.opensubtitles = OpenSubtitles()
        self.vid_sub_dict = {}

        self.subtitle_languages = subtitle_languages
        self.choose_subtitle = choose_subtitle

    def process(self):
        videos = []
        subtitles = []

        if len(sys.argv) > 1:
            for arg in sys.argv[1:]:
                self.init_path_args(arg, videos, subtitles)
        else:
            print("Usage: {:s} [video|directory]...".format(os.path.basename(sys.argv[0])))
            sys.exit(1)

        self.pair_videos_subs(videos, subtitles)
        del videos
        del subtitles

        self.process_videos_subs()

        print("Done!")
        sys.exit(0)

    def init_path_args(self, base_path, videos, subtitles):
        if os.path.exists(base_path):
            if os.path.isdir(base_path):
                for filename in os.listdir(base_path):
                    absolute_path = os.path.join(base_path, filename)
                    self.init_path_args(absolute_path, videos, subtitles)
            elif os.path.isfile(base_path):
                self.detect_file_type(base_path, videos, subtitles)
            else:
                print("No such file or directory: {:s}".format(base_path))

    def detect_file_type(self, file, videos, subtitles):
        vid_match = re.search(self._vid_match_pattern, file, re.IGNORECASE)
        sub_match = re.search(self._sub_match_pattern, file, re.IGNORECASE)

        if vid_match:
            videos.append(file)
        elif sub_match:
            subtitles.append(file)

    def pair_videos_subs(self, videos, subtitles):
        for video in videos:
            self.vid_sub_dict[video] = []
            video_season_episode = self.get_episode(video)
            for subtitle in subtitles:
                sub_season_episode = self.get_episode(subtitle)
                if video_season_episode[0] == sub_season_episode[0] and video_season_episode[1] == sub_season_episode[1]:
                    self.vid_sub_dict[video].append(subtitle)

    def get_episode(self, filename):
        season = 0
        episode = 0

        for pattern in self._season_episode_patterns:
            input_match = re.search(pattern, filename, re.IGNORECASE)
            if input_match:
                groups = input_match.groups()
                if len(groups) == 1:
                    episode = groups[0]
                elif len(groups) == 2:
                    season = groups[0]
                    episode = groups[1]

        return [str(season), str(episode)]

    def process_videos_subs(self):
        for video, subtitles in self.vid_sub_dict.items():
            if len(subtitles) > 0:
                processed_subtitles = []
                for idx, subtitle in enumerate(subtitles):
                    self.encode_sub(subtitle)
                    renamed_subtitle = self.rename_sub(video, subtitle, idx)
                    processed_subtitles.append(renamed_subtitle)
                self.vid_sub_dict[video] = processed_subtitles
            else:
                self.download_missing_subs(video)

    def encode_sub(self, subtitle):
        for encoding in self._supported_encodings:
            try:
                with open(subtitle, encoding=encoding) as input_sub:
                    data = input_sub.read()
                    if encoding == 'UTF-8':
                        print("Encoding of subtitle {:s} is already UTF-8, skipping".format(subtitle))
                        pass

                    print("Encoding subtitle {:s} from {:s} to UTF-8".format(subtitle, encoding))
                    temp = os.path.dirname(subtitle) + '/' + str(time.time()) + '.tmp'
                    with open(temp, 'w+', encoding='UTF-8') as output:
                        output.write(data)

                    input_sub.close()
                    output.close()

                    shutil.move(temp, subtitle)
                    break
            except UnicodeDecodeError:
                pass

    def rename_sub(self, video, subtitle, index):
        vid_match = re.search(self._vid_match_pattern, video, re.IGNORECASE)
        sub_match = re.search(self._sub_match_pattern, subtitle, re.IGNORECASE)

        if vid_match and sub_match:
            vid_name = vid_match.group(1)
            sub_name = sub_match.group(1)
            sub_ext = sub_match.group(2)

            new_sub_name = vid_name + '.' + sub_ext
            if os.path.exists(new_sub_name):
                new_sub_name = vid_name + '.' + index + '.' + sub_ext

            print("Renaming subtitle: {:s} --> {:s}".format(sub_name + sub_ext, new_sub_name))
            shutil.move(subtitle, new_sub_name)
            return new_sub_name

    def download_missing_subs(self, video):
        print("Searching subtitles for video: {:s}".format(video))
        vid_hash = self.opensubtitles.hash(video)
        for lang in self.subtitle_languages:
            sub_infos = self.opensubtitles.search_subtitles([{'sublanguageid': lang, 'moviehash': vid_hash,
                                                              'moviebytesize': str(os.path.getsize(video))}])
            if sub_infos:
                sub_index = self.choose_subtitle_to_download(sub_infos, lang)
                fetched_subtitle = self.fetch_subtitle(sub_index, sub_infos)
                vid_match = re.search(self._vid_match_pattern, video, re.IGNORECASE)
                if vid_match and fetched_subtitle is not None:
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
        sub_index = 0
        if self.choose_subtitle and len(sub_infos) > 1:
            print("Language: {:s}".format(lang))
            for idx, sub_info in enumerate(sub_infos):
                print("[{:d}] {:s}".format(idx, sub_info.get('SubFileName')))

            valid_input = False
            while not valid_input:
                try:
                    sub_index_input = input("Select a subtitle: ")
                    sub_index = int(sub_index_input)
                    if (sub_index < len(sub_infos)) and (sub_index >= 0):
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

    @staticmethod
    def write_subtitle_file(data, file):
        file_data = base64.b64decode(data)
        uncompressed_sub = gzip.decompress(file_data)

        try:
            with open(file, 'bw+') as subtitle:
                subtitle.write(uncompressed_sub)
        except IOError:
            print("Couldn't write subtitle file")
