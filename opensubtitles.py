import os
import struct
import xmlrpc.client


class OpenSubtitles:
    _open_subtitles_server = 'http://api.opensubtitles.org/xml-rpc'
    _user_agent = 'Python Subtitler'
    _language = 'en'

    def __init__(self):
        self.xmlrpc = xmlrpc.client.ServerProxy(self._open_subtitles_server, allow_none=True)
        self.token = self.login()
        if self.token is None:
            print("Couldn't log in to OpenSubtitles.org")

    def login(self):
        data = self.xmlrpc.LogIn(None, None, self._language, self._user_agent)
        return self.safe_get_value(data, 'token')

    @staticmethod
    def safe_get_value(data, key):
        status = data.get('status').split()[0]
        return data.get(key) if '200' == status else None

    @staticmethod
    def hash(vid_name):
        try:
            long_long_format = 'q'
            byte_size = struct.calcsize(long_long_format)

            f = open(vid_name, 'rb')

            file_size = os.path.getsize(vid_name)
            vid_hash = file_size

            if file_size < 65536 * 2:
                return 'SizeError'

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
            returned_hash = '%016x' % vid_hash
            return returned_hash

        except IOError:
            return 'IOError'

    def search_subtitles(self, params):
        data = self.xmlrpc.SearchSubtitles(self.token, params)
        return self.safe_get_value(data, 'data')

    def download_subtitle(self, subtitle_ids):
        data = self.xmlrpc.DownloadSubtitles(self.token, subtitle_ids)
        return self.safe_get_value(data, 'data')
