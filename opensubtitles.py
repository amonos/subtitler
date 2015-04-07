import os
import struct
import base64
import gzip
import xmlrpc.client


class OpenSubtitles:
    OPEN_SUBTITLES_SERVER = 'http://api.opensubtitles.org/xml-rpc'
    USER_AGENT = 'OSTestUserAgent'
    LANGUAGE = 'en'

    def __init__(self):
        self.xmlrpc = xmlrpc.client.ServerProxy(self.OPEN_SUBTITLES_SERVER, allow_none=True)
        self.token = self.login()
        if self.token is None:
            print("Couldn't log in to OpenSubtitles.org")

    @staticmethod
    def write_subtitle_file(data, file):
        """
        Unpack base64 encoded and gzip archived subtitle data and write it to disk.
        :param data:
        :param file:
        :return:
        """
        file_data = base64.b64decode(data)
        byte = gzip.decompress(file_data)

        try:
            with open(file, 'bw+') as subtitle:
                subtitle.write(byte)
        except:
            print("Couldn't write subtitle file")

    @staticmethod
    def get_from_data_or_none(data, key):
        """
        Get data from the XMLRPC response, or None if an error occured
        :param data:
        :param key:
        :return:
        """
        status = data.get('status').split()[0]
        return data.get(key) if '200' == status else None

    @staticmethod
    def hash(vid_name):
        """
        Opensubtitles' hash method for searching based on movie file
        :param vid_name:
        :return:
        """
        try:
            long_long_format = 'q'  # long long
            byte_size = struct.calcsize(long_long_format)

            f = open(vid_name, "rb")

            file_size = os.path.getsize(vid_name)
            vid_hash = file_size

            if file_size < 65536 * 2:
                return "SizeError"

            for x in range(int(65536 / byte_size)):
                buffer = f.read(byte_size)
                (l_value,) = struct.unpack(long_long_format, buffer)
                vid_hash += l_value
                vid_hash &= 0xFFFFFFFFFFFFFFFF  # to remain as 64bit number

            f.seek(max(0, file_size - 65536), 0)
            for x in range(int(65536 / byte_size)):
                buffer = f.read(byte_size)
                (l_value,) = struct.unpack(long_long_format, buffer)
                vid_hash += l_value
                vid_hash &= 0xFFFFFFFFFFFFFFFF

            f.close()
            returned_hash = "%016x" % vid_hash
            return returned_hash

        except IOError:
            return "IOError"

    def login(self):
        """
        Log in to opensubtitles as anonymous user
        :return:
        """
        data = self.xmlrpc.LogIn(None, None, self.LANGUAGE, self.USER_AGENT)
        return self.get_from_data_or_none(data, 'token')

    def search_subtitles(self, params):
        """
        Search the subtitle database
        :param params:
        :return:
        """
        data = self.xmlrpc.SearchSubtitles(self.token, params)
        return self.get_from_data_or_none(data, 'data')

    def download_subtitle(self, subtitle_ids):
        """
        Retrive the subtitles
        :param subtitle_ids:
        :return:
        """
        data = self.xmlrpc.DownloadSubtitles(self.token, subtitle_ids)
        return self.get_from_data_or_none(data, 'data')
