import os
import shutil
import subprocess
import sys
from cx_Freeze import setup, Executable

import info

svdir = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
os.chdir(svdir)
    
code = '''
import os
import sys
import subprocess

def main():

    svdir = '{0}'
    with open(os.path.join(svdir, 'exe_path.txt'), 'r') as f:
        epath = f.read()
    epath0 = os.path.abspath(sys.argv[0]).replace('\\\\', '/')
    if epath != epath0:
        with open(os.path.join(svdir, 'exe_path.txt'), 'w') as f:
            f.write(epath0)
    if 'from_msi' in sys.argv[1:]:
        return
    
    command = os.path.split(svdir)[0]
    for _ in range(2):
        command = os.path.split(command)[0]
    command += '/python ' + svdir + '/subdir/launcher.py'
    if len(sys.argv) > 1:
        command += ' ' + sys.argv[1]
    subprocess.run(command, shell=True)
    
if __name__ == '__main__':
    main()
'''
    
code = code.format(svdir)
with open('executable.py', 'w') as f:
    f.write(code)

icon = 'img/icon.ico'

build_exe_options = {'packages': ['os'], 
                     'excludes': ['asyncio',
                                  'concurrent',
                                  'distutils',
                                  'email',
                                  'html',
                                  'http',
                                  'logging',
                                  'multiprocessing',
                                  'pydoc_data',
                                  'tkinter',
                                  'unicodedata',
                                  'unittest',
                                  'urllib',
                                  'xml']}

msi_data = {'CustomAction': [('EXECUTE_EXE', 18, info.name + '.exe', 'from_msi')],
            'InstallUISequence': [('EXECUTE_EXE', None, 10000)]}

bdist_msi_options = {'add_to_path': False,
                     'data': msi_data,
                     'install_icon': icon,
                     'target_name': 'SectionViewer.msi',
                     'upgrade_code': info.upgrade_code,
                     'extensions': info.extensions}

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

setup(
      name = info.name,
      description = info.description,
      version = info.version,
      author = info.author,
      url = info.url,
      options = {'build_exe': build_exe_options,
                 'bdist_msi': bdist_msi_options},
      executables = [Executable(script='executable.py',
                                base=base,
                                icon=icon,
                                target_name=info.name,
                                shortcut_name=info.name,
                                shortcut_dir='ProgramMenuFolder')])

shutil.rmtree('build')
subprocess.run('dist\\' + bdist_msi_options['target_name'], shell=True)
shutil.rmtree('dist')
