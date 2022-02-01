import os
import pickle

import numpy as np
import oiffile as oif
import tifffile as tif
from tkinter import filedialog
from tkinter import messagebox


class Data:
    def __init__(self, Hub):
        self.Hub = Hub
        dat = Hub.data
        
        if len(dat) == 0:
            messagebox.showinfo("Information",
                                    '''The project doesn't contain any data files.
Please choose data file to open.''')
            fTyp = [("OIB/TIFF files", ["*.oib", "*.tif", "*.tiff"]),
                    ("All files", "*")]
            iDir = os.path.dirname(Hub.gui.iDir)
            file = filedialog.askopenfilename(parent=Hub.gui.master, 
                                               filetypes=fTyp, 
                                               initialdir=iDir,
                                               title=Hub.gui.title)
            if len(file) == 0:
                return None
            file = file.replace("\\", "/")
            dat = [[file]]
        else:
            for i in range(len(dat)):
                dat[i][0] = os.path.abspath(str(dat[i][0])).replace("\\", "/")
        
        self.dat = dat
        
    
    def __getattr__(self, name):
        if name == "val":
            return object.__getattribute__(self, "dat")
        else:
            return object.__getattribute__(self, name)
    def __setattr__(self, name, val):
        if name == "dat":
            self.load(val)
        elif name == "val":
            self.dat = val
        else:
            object.__setattr__(self, name, val)
    
    
    def __getitem__(self, x):
        return self.dat[x]
    
    def getchload(self):
        ch_load = []
        for d in self.dat:
            ch_load += list(d[1])
        return ch_load
    
    def getchnum(self, x):
        ch_load = self.getchload()
        if isinstance(x, (tuple, list)):
            x = [int(i) for i in x]
            ch_load = np.cumsum(ch_load, dtype=np.int)
            return ch_load[x] - 1
        x = int(x)
        return np.sum(ch_load[:x], dtype=np.int)
    
    
    def load(self, dat, add=False):
        Hub = self.Hub
        
        files = [d[0] for d in dat]
        try: 
            ch_load = [d[1] for d in dat]
            dat = []
            for f, c in zip(files, ch_load):
                if np.array(c).any():
                    dat += [[f, c]]
            files = [d[0] for d in dat]
            ch_load = [d[1] for d in dat]
        except: ch_load = []
        
        for i, f in enumerate(files):
            if not os.path.isfile(f):
                messagebox.showinfo("Information",
                                    '''Couldn't find the following data file:
{0}
Please specify the file.'''.format(os.path.basename(f)))
                fTyp = [("OIB/TIFF files", ["*.oib", "*.tif", "*.tiff"]),
                        ("All files", "*")]
                iDir = os.path.dirname(Hub.gui.iDir)
                iFil = os.path.splitext(os.path.basename(f))[0]
                f = filedialog.askopenfilename(parent=Hub.gui.master, 
                                              filetypes=fTyp, 
                                              initialdir=iDir, 
                                              initialfile=iFil,
                                              title="Specify {0}".format(os.path.basename(f)))
                if len(f) == 0:
                    return 0
                f = f.replace("\\", "/")
                files[i] = f
            
        
        boxes = []    
        for i, f in enumerate(files):
                
            if f[-4:] == ".oib":
                boxes += [oif.imread(f)]
                
                try:
                    with oif.OifFile(f) as oib:
                        axes = oib.axes
                        shape = oib.shape
                        data = oib.mainfile
                    shape = dict(np.append(np.array(list(axes))[:,None], np.array(shape)[:,None], axis=1))
                    axes = dict(np.append(np.array(list(axes))[::-1][:,None], np.arange(len(axes))[:,None], axis=1))
        
                    pxs = axes.copy()
                    try:
                        pxs["C"] = 0
                    except:
                        pass
                    for ax in ["Z", "Y", "X"]:
                        ax_data = data['Axis {0} Parameters Common'.format(axes[ax])]
                        px = abs((ax_data["EndPosition"] - ax_data["StartPosition"])/float(shape[ax]))
                        if ax_data["UnitName"] == "nm":
                            px /= 1000
                        pxs[ax] = px
                    Hub.geometry["xy_oib"] = (pxs["X"] + pxs["Y"])/2
                    Hub.geometry["z_oib"] = pxs["Z"]
                except:
                    pass
    
            elif f[-4:] == ".tif" or f[-5:] == ".tiff":
                boxes += [tif.imread(f)]
            else:
                try:
                    with open(f, "rb") as g:
                        boxes += [pickle.load(g)]
                except:
                    messagebox.showerror("Error", 
                                         "File type '{0}' is not supported.".format(os.path.splitext(f)[1]))
                    return 0
            
        boxes = [boxes[i][None] if boxes[i].ndim == 3 else boxes[i] for i in range(len(boxes))]
        
        if len(boxes) != len(ch_load):
            ch_load = [tuple([1]*len(b)) for b in boxes]
        else:
            ch_load = [ch_load[i] if len(ch_load[i]) == len(boxes[i]) else tuple([1]*len(boxes[i]))
                       for i in range(len(ch_load))]
        
        box = boxes[0][np.array(ch_load[0], dtype=np.bool)]
        del boxes[0]
        n = 1
        if box.dtype != np.uint16:
            box = box.astype(np.uint16)
        while len(boxes) > 0:
            b = boxes[0][np.array(ch_load[n], dtype=np.bool)]
            if b.dtype != np.uint16:
                b = b.astype(np.uint16)
            try: box = np.append(box, b, axis=0)
            except:
                messagebox.showerror("Failed to load data",
                                     "Width, height and depth must be exactly the same.")
                return 0
            del b, boxes[0]
            n += 1
        
        if add:
            try:
                Hub.box = np.append(Hub.box, box, axis=0)
                Hub.ch_show = np.append(Hub.ch_show, np.ones(len(box), np.bool))
            except:
                messagebox.showerror("Failed to load data",
                                     "Width, height and depth must be exactly the same.")
                return 0
        else:
            Hub.box = box
            Hub.ch_show = np.ones(len(box), np.bool)
        
        dat = [[files[i], ch_load[i]] for i in range(len(files))]
        
        if add: object.__setattr__(self, "dat", tuple(list(self.dat) + dat))
        else: object.__setattr__(self, "dat", tuple(dat))
        
        Hub.geometry["shape"] = box.shape
        
        return len(box)
    
    
    def load_from_path(self, path):
        Hub = self.Hub
        
        if not os.path.isfile(path):
            messagebox.showinfo("Information",
                                '''Couldn't find the following data file:
{0}
Please specify the file.'''.format(os.path.basename(path)))
            fTyp = [("OIB/TIFF files", ["*.oib", "*.tif", "*.tiff"]),
                    ("All files", "*")]
            iDir = os.path.dirname(Hub.gui.iDir)
            iFil = os.path.splitext(os.path.basename(path))[0]
            path = filedialog.askopenfilename(parent=Hub.gui.master, 
                                              filetypes=fTyp, 
                                              initialdir=iDir, 
                                              initialfile=iFil,
                                              title="Specify {0}".format(os.path.basename(path)))
            if len(path) == 0:
                return
            path = path.replace("\\", "/")
            
        
        if path[-4:] == ".oib":
            box = oif.imread(path)

        elif path[-4:] == ".tif" or path[-5:] == ".tiff":
            box = tif.imread(path)
        else:
            try:
                with open(path, "rb") as f:
                    box = pickle.load(f)
            except:
                messagebox.showerror("Error", 
                                     "File type '{0}' is not supported.".format(os.path.splitext(path)[1]))
                return
            
        box = box[None] if box.ndim == 3 else box
        if box[0].shape != self.Hub.box[0].shape:
            messagebox.showerror("Failed to load data",
                                 "Width, height and depth must be exactly the same.")
            return
        
        return box
    
    
    def reload(self, dat):
        data = self.dat
        files = [os.path.apspath(str(d[0])).replace('\\', '/') for d in data]
        ch_load = [d[1] for d in data]
        data = []
        for f, c in zip(files, ch_load):
            if np.array(c).any():
                data += [[f, c]]
        data = tuple(data)
        
        files = [os.path.apspath(str(d[0])).replace('\\', '/') for d in dat]
        ch_load = [d[1] for d in dat]
        dat0 = []
        for f, c in zip(files, ch_load):
            if np.array(c).any():
                dat0 += [[f, c]]
        dat0 = tuple(dat0)
        
        if dat0 == data:
            return False
        self.dat = dat0
        if self.dat == data:
            raise
        return True
