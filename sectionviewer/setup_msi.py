import os
import shutil
import subprocess
import sys
from cx_Freeze import setup, Executable

import info

path = os.path.dirname(os.path.abspath(__file__))
path = path.replace("\\", "/")
os.chdir(path)

with open("executable.txt", "r") as f:
    code = f.read()
code = code.format(path)
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
bdist_msi_options = {"add_to_path": True,
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

proc = subprocess.Popen("echo %Path%", stdout=subprocess.PIPE, shell=True)
epath = proc.communicate()[0].decode("utf-8")
epath = epath.split(";")[-1]
epath = epath.replace("\\", "/") + "/SectionViewer.exe"
epath = epath.replace("\n", "").replace("\r", "")
with open("epath.txt", "w") as f:
    f.write(epath)
