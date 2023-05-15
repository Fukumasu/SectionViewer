import os
import pathlib
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
            messagebox.showerror('Error: No data files in SECV',
                                 'Please choose a data file to open.',
                                 parent=Hub.gui.master)
            filetypes = [('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff']),
                         ('All files', '*')]
            initialdir = Hub.gui.file_dir
            file = filedialog.askopenfilename(parent=Hub.gui.master, 
                                              filetypes=filetypes, 
                                              initialdir=initialdir,
                                              title=Hub.gui.title)
            if len(file) == 0:
                return None
            file = file.replace('\\', '/')
            dat = [[file]]
        else:
            for i in range(len(dat)):
                dat[i][0] = os.path.abspath(str(dat[i][0])).replace('\\', '/')
        
        self.dat = dat
        
    
    def __getattr__(self, name):
        if name == 'val':
            return object.__getattribute__(self, 'dat')
        else:
            return object.__getattribute__(self, name)
    def __setattr__(self, name, val):
        if name == 'dat':
            self.load(val)
        elif name == 'val':
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
            relat = [d[2] for d in dat]
        except:
            relat = [None]*len(files)
        try: 
            ch_load = [d[1] for d in dat]
            dat = []
            for f, c, r in zip(files, ch_load, relat):
                if np.array(c).any():
                    dat += [[f, c, r]]
            files = [d[0] for d in dat]
            ch_load = [d[1] for d in dat]
            relat = [d[2] for d in dat]
        except: ch_load = []
        
        if Hub.secv_name is not None:
            for i, r in enumerate(relat):
                if r is not None:
                    p = pathlib.Path(os.path.join(Hub.secv_name, r))
                    relat[i] = str(p.resolve()).replace('\\', '/')
        for i in range(len(relat)):
            if relat[i] is None:
                relat[i] = ''
        
        changed = False
        for i, f in enumerate(files):
            if not os.path.isfile(f):
                if os.path.isfile(relat[i]):
                    files[i] = relat[i]
                    f = relat[i]
                    changed = True
            if not os.path.isfile(f):
                if self.Hub.secv_name == None:
                    raise FileNotFoundError('[Errno 2] No such file or directory: ' + f)
                messagebox.showinfo('Information',
                                    '''The following file path seems to have been changed:
{0}
Please specify the file again.'''.format(f), parent=self.Hub.gui.master)
                filetypes = [('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff']),
                             ('All files', '*')]
                initialdir = Hub.gui.file_dir
                initialfile = os.path.splitext(os.path.basename(f))[0]
                f1 = filedialog.askopenfilename(parent=Hub.gui.master, 
                                               filetypes=filetypes, 
                                               initialdir=initialdir, 
                                               initialfile=initialfile,
                                               title='Find {0}'.format(os.path.basename(f)))
                if len(f1) == 0:
                    raise FileNotFoundError('[Errno 2] No such file or directory: ' + f)
                f = f1.replace('\\', '/')
                files[i] = f
                changed = True
        
        if changed and not add and hasattr(self, 'dat'):
            dat = [[files[i], ch_load[i]] for i in range(len(files))]
            if self.dat == tuple(dat):
                return 0
        
        boxes = []    
        for i, f in enumerate(files):
                
            if f[-4:] == '.oib':
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
                        pxs['C'] = 0
                    except:
                        pass
                    for ax in ['Z', 'Y', 'X']:
                        ax_data = data['Axis {0} Parameters Common'.format(axes[ax])]
                        px = abs((ax_data['EndPosition'] - ax_data['StartPosition'])/float(shape[ax]))
                        if ax_data['UnitName'] == 'nm':
                            px /= 1000
                        pxs[ax] = px
                    Hub.geometry['xy_oib'] = (pxs['X'] + pxs['Y'])/2
                    Hub.geometry['z_oib'] = pxs['Z']
                except:
                    pass
    
            elif f[-4:] == '.tif' or f[-5:] == '.tiff':
                boxes += [tif.imread(f)]
            else:
                try:
                    with open(f, 'rb') as g:
                        boxes += [pickle.load(g)]
                except:
                    messagebox.showerror('Error', 
                                         "File type '{0}' is not supported.".format(os.path.splitext(f)[1]),
                                         parent=self.Hub.gui.master)
                    return 0
            
        boxes = [boxes[i][None] if boxes[i].ndim == 3 else boxes[i] for i in range(len(boxes))]
        
        if len(boxes) != len(ch_load):
            ch_load = [tuple([1]*len(b)) for b in boxes]
        else:
            ch_load = [ch_load[i] if len(ch_load[i]) == len(boxes[i]) else tuple([1]*len(boxes[i]))
                       for i in range(len(ch_load))]
        
        box = boxes[0][np.array(ch_load[0], dtype=bool)]
        del boxes[0]
        n = 1
        if box.dtype != np.uint16:
            box = box.astype(np.uint16)
        while len(boxes) > 0:
            b = boxes[0][np.array(ch_load[n], dtype=bool)]
            if b.dtype != np.uint16:
                b = b.astype(np.uint16)
            try: box = np.append(box, b, axis=0)
            except:
                messagebox.showerror('Failed to load data',
                                     'Width, height and depth must be exactly the same.',
                                     parent=self.Hub.gui.master)
                return 0
            del b, boxes[0]
            n += 1
        
        if add:
            try:
                Hub.box = np.append(Hub.box, box, axis=0)
                Hub.ch_show = np.append(Hub.ch_show, np.ones(len(box), dtype=bool))
            except:
                messagebox.showerror('Failed to load data',
                                     'Width, height and depth must be exactly the same.',
                                     parent=self.Hub.gui.master)
                return 0
        else:
            Hub.box = box
            Hub.ch_show = np.ones(len(box), dtype=bool)
        
        dat = [[files[i], ch_load[i]] for i in range(len(files))]
        
        if add: object.__setattr__(self, 'dat', tuple(list(self.dat) + dat))
        else: object.__setattr__(self, 'dat', tuple(dat))
        
        return len(box)
    
    
    def load_from_path(self, path):
        Hub = self.Hub
        
        if not os.path.isfile(path):
            messagebox.showinfo('Information',
                                    '''The following file path seems to have been changed:
{0}
Please specify the file again.'''.format(path), parent=self.Hub.gui.master)
            filetypes = [('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff']),
                         ('All files', '*')]
            initialdir = Hub.gui.file_dir
            initialfile = os.path.splitext(os.path.basename(path))[0]
            path = filedialog.askopenfilename(parent=Hub.gui.master, 
                                              filetypes=filetypes, 
                                              initialdir=initialdir, 
                                              initialfile=initialfile,
                                              title='Find {0}'.format(os.path.basename(path)))
            if len(path) == 0:
                return
            path = path.replace('\\', '/')
            
        
        if path[-4:] == '.oib':
            box = oif.imread(path)

        elif path[-4:] == '.tif' or path[-5:] == '.tiff':
            box = tif.imread(path)
        else:
            try:
                with open(path, 'rb') as f:
                    box = pickle.load(f)
            except:
                messagebox.showerror('Error', 
                                     "File type '{0}' is not supported.".format(os.path.splitext(path)[1]),
                                     parent=Hub.gui.master)
                return
            
        box = box[None] if box.ndim == 3 else box
        if box[0].shape != self.Hub.box[0].shape:
            messagebox.showerror('Failed to load data',
                                 'Width, height and depth must be exactly the same.',
                                 parent=Hub.gui.master)
            return
        
        return box
    
    
    def reload(self, dat):
        data = self.dat
        files = [os.path.abspath(str(d[0])).replace('\\', '/') for d in data]
        ch_load = [d[1] for d in data]
        data = []
        for f, c in zip(files, ch_load):
            if np.array(c).any():
                data += [[f, c]]
        data = tuple(data)
        
        files = [os.path.abspath(str(d[0])).replace('\\', '/') for d in dat]
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
            return False
        return True
