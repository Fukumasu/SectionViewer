# -*- coding: utf-8 -*-
"""
Created on Thu Jan 13 18:38:06 2022

@author: kazuu
"""
import sys
from sectionviewer import sectionviewer

app = sectionviewer.SectionViewer(sys.argv[1:])
app.mainloop()