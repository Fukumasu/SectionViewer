import time

import numpy as np

from . import utils as ut


class Position:
    def __init__(self, Hub):
        self.Hub = Hub
        pos = Hub.position
        
        dc, dz, dy, dx = Hub.geometry['shape']
        ratio = Hub.ratio
        
        try:
            pos = np.float64(pos)
            pos[0] -= np.array([dz, dy, dx])//2
            pos[:,0] *= ratio
            pos[2] /= np.linalg.norm(pos[2])
            pos[1] = pos[1] - pos[2]*np.inner(pos[1], pos[2])
            pos[1] /= np.linalg.norm(pos[1])
            pos = pos.tolist()
        except:
            pos = [[0.,0.,0.], [0.,1.,0.], [0.,0.,1.]]
        
        self.pos = pos
        self.angs = {'l':[32,256,2], 'h':[-32,-256,-2], 'i':[-32,-256,-2],
                     'n':[32,256,2], 'j':[4,1,0], 'k':[-4,-1,0],
                     'down':[-4,-1,0], 'up':[4,1,0], 'left':[4,1,0],'right':[-4,-1,0]}
        self.byhand = False
        
        self.pre_updt_time = 0
    
    
    def __getattr__(self, name):
        if name == 'val':
            return object.__getattribute__(self, 'pos')
        else:
            return object.__getattribute__(self, name)
    def __setattr__(self, name, val):
        if name == 'val':
            object.__setattr__(self, 'pos', val)
        else:
            object.__setattr__(self, name, val)
    
    def __getitem__(self, x):
        return self.pos[x]
    
    def asarray(self):
        return np.array(self.pos)
    
    def key_pressed(self, key, n):
        if key in self.angs:
            ang = self.angs[key][n]
            if ang:
                self.set_pos(key, ang)
                
    def key_release(self, event):
        self.post_calc = False
        key = event.keysym
        if key in self.angs or key in ['z', 'y']:
            self.apply()
            self.post_calc = False
        
    def clicked(self, click):
        la, lb = self.Hub.geometry['im_size']
        v = click - np.array([la//2, lb//2])
        v = v*np.array([1, la/lb])
        if np.linalg.norm(v) > la/6:
            key = int(np.angle(v[0] + 1j*v[1])/np.pi*6)
            key = ['l',0,'n','n',0,'h','h',0,'i','i',0][key]
            if key != 0:
                ang = self.angs[key][2]
                self.set_pos(key, ang, branch=0)
        
    def set_pos(self, key, ang, branch=None):
        pos = np.array(self.pos)
        op, ny, nx = pos.copy()
        nz = np.cross(ny, nx)
        if key in ['l', 'h']:
            theta = np.pi/ang
            pos[2] = np.cos(theta)*nx + np.sin(theta)*nz
            if branch == None: branch = 1
        elif key in ['i', 'n']:
            phi = np.pi/ang
            pos[1] = np.cos(phi)*ny + np.sin(phi)*nz
            if branch == None: branch = 2
        elif key in ['j', 'k']:
            pos[0] += ang*nz
            if branch == None: branch = 3
        elif key in ['down', 'up']:
            pos[0] += ang*ny
            if branch == None: branch = 4
        elif key in ['left', 'right']:
            pos[0] += ang*nx
            if branch == None: branch = 5
        else:
            return
        self.new(pos, branch)
        return True
    
    def scale(self, v):
        if self.byhand:
            pos = np.array(self.pos)
            op, ny, nx = pos
            nz = -np.cross(ny, nx)
            op[:] = self.Hub.scale_orient + self.Hub.gui.depth.get()*nz
            self.new(pos, 6)
    def scale_clicked(self, event):
        self.Hub.gui.master.focus_set()
        self.byhand = True
    def scale_released(self, event):
        self.byhand = False
        
    
    def new(self, new, branch):
        pos = self.pos
        new = np.array(new)
        new[2] /= np.linalg.norm(new[2])
        new[1] = new[1] - new[2]*np.inner(new[1], new[2])
        new[1] /= np.linalg.norm(new[1])
        new = new.tolist()
        if np.average((np.array(pos)-np.array(new))**2) < 10e-8:
            return
        Hub = self.Hub
        idx, hist = Hub.hidx, Hub.history
        if idx == -1 and hist[-1][1][0] == branch and Hub.hidx_saved != -1 and branch != 0:
            hist[-1][1][2] = new
        else:
            if idx != -1:
                hist[idx:] = hist[idx:idx+1]
            hist += [[self, [branch, pos, new]]]
            if Hub.hidx_saved > idx:
                Hub.hidx_saved = -1 - len(hist)
            else: 
                Hub.hidx_saved -= idx + 2
            Hub.hidx = -1
        
        gui = Hub.gui
        gui.edit_menu.entryconfig('Undo', state='normal')
        gui.edit_menu.entryconfig('Redo', state='disable')
        gui.master.title('*' + gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.pos = new
        
        dz, dy, dx = Hub.box[0].shape
        m, n = Hub.frame[0].shape
        pos_ = np.array(new)
        pos_[:,0] /= Hub.ratio
        pos_[0] += np.array([dz, dy, dx])//2
        pos_[1:] /= Hub.geometry['exp_rate']
        
        if not ut.calc_exist(pos_, np.array(Hub.frame[0].shape)//2,
                             dz-1, dy-1, dx-1, m, n):
            self.pos = pos
            hist[-1][1][2] = pos
            if hist[-1][1][1] == pos:
                del hist[-1]
                Hub.hidx_saved += 1
            if len(hist) == 1:
                gui.edit_menu.entryconfig('Undo', state='disable')
            if Hub.hidx == Hub.hidx_saved:
                gui.master.title(gui.title if Hub.hidx != Hub.hidx_saved else gui.title)
        
        self.apply()
        
    
    def apply(self):
        Hub = self.Hub
        gui = Hub.gui
        Hub.calc_frame()
        if gui.g_on.get():
            if gui.guide_mode == 'guide':
                Hub.calc_guide()
            else:
                Hub.calc_sideview()
    
            
    def undo(self, arg):
        self.pos = arg[1]
        self.apply()
        
    def redo(self, arg):
        self.pos = arg[2]
        self.apply()
            
    def reload(self, pos):
        Hub = self.Hub
        dc, dz, dy, dx = Hub.box.shape
        ratio = Hub.ratio
        try:
            pos = np.float64(pos)
            pos[0] -= np.array([dz, dy, dx])//2
            pos[:,0] *= ratio
            pos[2] /= np.linalg.norm(pos[2])
            pos[1] = pos[1] - pos[2]*np.inner(pos[1], pos[2])
            pos[1] /= np.linalg.norm(pos[1])
            pos = pos.tolist()
        except:
            pos = [[0.,0.,0.], [0.,1.,0.], [0.,0.,1.]]
        
        if self.pos == pos:
            return False
        self.pos = pos
        return True
        
