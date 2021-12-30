# -*- coding: utf-8 -*-
"""
Created on Thu Dec 30 17:53:00 2021

@author: kazuu
"""
import os
import subprocess

def main():
    eDir = os.path.dirname(os.path.abspath(__file__))
    eDir = os.path.join(eDir, "SectionViewer-install.exe")
    
    subprocess.run(eDir, shell=True)
