# -*- coding: utf-8 -*-
"""
Created on Sun Jan 30 17:46:22 2022

@author: kazuu
"""
import os
import shutil
import subprocess
import sys
from cx_Freeze import setup, Executable
from . import __version__

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
               "context": "Edit with SectionViewer"},
              {"extension": "stac",
               "verb": "open",
               "executable": "SectionViewer.exe",
               "context": "Edit with SectionViewer"},
              {"extension": "oib",
               "verb": "view",
               "executable": "SectionViewer.exe",
               "context": "View with SectionViewer"},
              {"extension": "tif",
               "verb": "view",
               "executable": "SectionViewer.exe",
               "context": "View with SectionViewer"}]
bdist_msi_options = {"add_to_path": True,
                     "install_icon": icon,
                     "target_name": "SectionViewer.msi",
                     "upgrade_code": "{6bd9a5e4-428c-4053-8956-9c452ebeefcf}",
                     "extensions": extensions}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
      name = "SectionViewer",
      version = __version__,
      author="Kazushi Fukumasu",
      url="https://github.com/Fukumasu/SectionViewer",
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
