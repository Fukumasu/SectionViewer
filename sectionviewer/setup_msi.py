import os
import shutil
import subprocess
import sys
from cx_Freeze import setup, Executable

import info

mDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(mDir)

with open("exe_path.txt", "w") as f:
    f.write("")
    
code = """
import os
import sys
import subprocess

def main():

    mDir = r"{0}"
    os.chdir(mDir)
    with open("exe_path.txt", "r") as f:
        epath = f.read()
    epath0 = os.path.abspath(sys.argv[0])
    if epath != epath0:
        with open("exe_path.txt", "w") as f:
            f.write(epath0)
        return
    
    command = "../../../python sectionviewer.py"
    if len(sys.argv) > 1:
        command += " " + sys.argv[1]
    subprocess.run(command, shell=True)
    
if __name__ == '__main__':
    main()
"""
    
code = code.format(mDir)
with open("executable.py", "w") as f:
    f.write(code)

icon = "img/SectionViewer.ico"

build_exe_options = {"packages": ["os"], 
                     "excludes": ["asyncio",
                                  "concurrent",
                                  "distutils",
                                  "email",
                                  "html",
                                  "http",
                                  "logging",
                                  "multiprocessing",
                                  "pydoc_data",
                                  "tkinter",
                                  "unicodedata",
                                  "unittest",
                                  "urllib",
                                  "xml"]}

extensions = [{"extension": "secv",
               "verb": "open",
               "executable": "SectionViewer.exe",
               "context": "Edit with SectionViewer",
               "argument": '"%1"'},
              {"extension": "stac",
               "verb": "open",
               "executable": "SectionViewer.exe",
               "context": "Edit with SectionViewer",
               "argument": '"%1"'},
              {"extension": "oib",
               "verb": "view",
               "executable": "SectionViewer.exe",
               "context": "View with SectionViewer",
               "argument": '"%1"'},
              {"extension": "tif",
               "verb": "view",
               "executable": "SectionViewer.exe",
               "context": "View with SectionViewer",
               "argument": '"%1"'}]

msi_data = {"CustomAction": [("EXECUTE_EXE", 18, "SectionViewer.exe", None)],
            "InstallUISequence": [("EXECUTE_EXE", None, 10000)]}

bdist_msi_options = {"add_to_path": False,
                     "data": msi_data,
                     "install_icon": icon,
                     "target_name": "SectionViewer.msi",
                     "upgrade_code": info.upgrade_code,
                     "extensions": extensions}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
      name = "SectionViewer",
      version = info.version,
      author = info.author,
      url = info.url,
      description = "SectionViewer app launcher",
      options = {"build_exe": build_exe_options,
                 "bdist_msi": bdist_msi_options},
      executables = [Executable(script="executable.py",
                                base=base,
                                icon=icon,
                                target_name="SectionViewer",
                                shortcut_name="SectionViewer",
                                shortcut_dir="ProgramMenuFolder")])

shutil.rmtree("build")
subprocess.run("dist\\SectionViewer.msi", shell=True)
shutil.rmtree("dist")
