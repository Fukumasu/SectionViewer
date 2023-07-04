import sys
import sectionviewer as sv

if len(sys.argv) > 1:
    sv.launch(file_path=sys.argv[1])
else:
    sv.launch()