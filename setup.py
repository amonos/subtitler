from cx_Freeze import setup, Executable


include_files = ['subtitler.conf']
base = None

executables = [Executable('subtitler.py', base=base)]

options = {
    'build_exe': {
        'include_files': include_files
    }
}

setup(name='subtitler', version='1.0', description='OpenSubtitles downloader', executables=executables, requires=['core'])
