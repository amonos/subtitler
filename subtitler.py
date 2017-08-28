import configparser

from core.subtitle_processor import SubtitleProcessor


class Subtitler:
    _default_config_file = 'subtitler.conf'
    _config_category = 'SubtitleDownloader'
    _config_languages = 'languages'
    _config_choose_subtitle = 'chooseSubtitle'
    _default_language = 'eng'

    def __init__(self):
        self.config_parser = configparser.ConfigParser()
        self.subtitle_languages = None
        self.choose_subtitle = None
        self.parse_config()

    def parse_config(self):
        self.config_parser.read(self._default_config_file, encoding='UTF-8')
        languages = self.config_parser[self._config_category][self._config_languages]
        if languages is None:
            languages = self._default_language
        self.subtitle_languages = languages.split(',')
        self.choose_subtitle = int(self.config_parser[self._config_category][self._config_choose_subtitle])

if __name__ == '__main__':
    main = Subtitler()
    processor = SubtitleProcessor(main.subtitle_languages, main.choose_subtitle)
    processor.process()
