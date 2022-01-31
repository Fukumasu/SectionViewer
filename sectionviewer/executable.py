
import os
import sys
import subprocess

pDir = ""
eDir = pDir
eDir = os.path.join(eDir, "subdir/launcher.py")
if len(sys.argv) > 1:
    eDir += " " + sys.argv[1]
for _ in range(3):
    pDir = os.path.split(pDir)[0]
pDir = os.path.join(pDir, "python")
pDir = pDir + " " + eDir
subprocess.run(pDir, shell=True)
