from cx_Freeze import setup, Executable


base = None

executables = [Executable('subtitler.py', base=base)]

options = {
    'build_exe': {
    }
}

setup(name='subtitler', version='1.0', description='OpenSubtitles downloader', executables=executables, requires=['core'])
