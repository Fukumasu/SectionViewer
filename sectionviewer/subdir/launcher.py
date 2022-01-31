import sys
from sectionviewer import sectionviewer

app = sectionviewer.SectionViewer(sys.argv[1:])
app.mainloop()
