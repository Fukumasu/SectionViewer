import sys
import os
from pycrosskit.shortcuts import Shortcut

def main():
  exec_path = os.path.join(os.path.join(sys.base_prefix, "Scripts"), "SectionViewer.exe")
  icon_path = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), "img"), "SectionViewer.ico")
  Shortcut("SectionViewer", exec_path, icon_path, True, True)
