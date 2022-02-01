import os
import sys
import subprocess

def main():

    pDir = "c:/users/kazuu/anaconda3/envs/secview/lib/site-packages/sectionviewer"
    eDir = os.path.join(pDir, "epath.txt")
    with open(eDir, "r") as f:
        epath = f.read()
    epath0 = sys.argv[0].replace("\\", "/")
    if epath != epath0:
        with open(eDir, "w") as f:
            f.write(epath0)
        return
    
    eDir = pDir
    eDir = os.path.join(eDir, "subdir/launcher.py")
    if len(sys.argv) > 1:
        eDir += " " + sys.argv[1]
    for _ in range(3):
        pDir = os.path.split(pDir)[0]
    pDir = os.path.join(pDir, "python")
    pDir = pDir + " " + eDir
    subprocess.run(pDir, shell=True)
    
if __name__ == '__main__':
    main()
