import os
import pickle
import platform

import numpy as np
import oiffile as oif
import tifffile as tif

from . import utils as ut

pf = platform.system()

def load(path):
    return SectionViewer(path)

class Data:
    def __init__(self, hub, val):
        _val = []
        for v in val:
            _val += [[os.path.abspath(str(v[0])).replace("\\", "/"), tuple(v[1])]]
        object.__setattr__(self, "_val" , _val)
        object.__setattr__(self, "_hub" , hub)
        tuple.__init__(self)
    def __str__(self):
        data_files = self._val
        ch_load = [str(l)[1:-1] for l in self.channels_to_load()]
        data_files = [d[0] for d in data_files]
        m = max([len(d) for d in data_files])
        text = "([" + data_files[0] + ", " + \
                    " "*(m-len(data_files[0])) + \
                        "(" + ch_load[0] + ")]"
        for i in range(1, len(data_files)):
            text += ",\n [" + data_files[i] + ", " + \
                        " "*(m-len(data_files[i])) + \
                            "(" + ch_load[i] + ")]"
        text += ")"
        return text
    def __getitem__(self, x):
        if type(x) == int:
            item = self._val[x]
            return [item[0], tuple(np.where(item[1])[0])]
        else:
            item = self._val[x]
            return tuple([[it[0], tuple(np.where(it[1])[0])] for it in item])
    def __setattr__(self, name, value):
        pass
    def __delattr__(self, name):
        pass
    def __len__(self):
        return len(self._val)
    def files_to_load(self):
        return [d[0] for d in self._val]
    def channels_to_load(self):
        return [list(np.where(d[1])[0]) for d in self._val]
        
class Geometry(dict):
    def __init__(self, hub, val):
        _val = {}
        if not 'res_xy' in val:
            val['res_xy'] = None
        if not 'res_z' in val:
            val['res_z'] = None
        if 'xy_oib' in val:
            _val['xy_oib'] = val['xy_oib']
        if 'z_oib' in val:
            _val['z_oib'] = val['z_oib']
        _val['res_xy'] = val['res_xy'] if val['res_xy'] == None else float(val['res_xy'])
        _val['res_z'] = val['res_z'] if val['res_z'] == None else float(val['res_z'])
        _val['im_size'] = (int(val['im_size'][0]), int(val['im_size'][1]))
        _val['exp_rate'] = float(val['exp_rate'])
        _val['bar_len'] = val['bar_len'] if val['bar_len'] == None else float(val['bar_len'])
        _val['shape'] = (int(val['shape'][0]), int(val['shape'][1]), 
                         int(val['shape'][2]), int(val['shape'][3]))
        try:
            ratio = _val['res_z']/_val['res_xy']
        except:
            ratio = 1.
        object.__setattr__(self, "_val" , _val)
        object.__setattr__(self, "_hub" , hub)
        object.__setattr__(self, "_ratio", ratio)
        dict.__init__(self, _val)
    def __getitem__(self, k):
        if k in ['xy_oib', 'z_oib']:
            raise KeyError(k)
        return self._val[k]
    def __setitem__(self, k, v):
        if k == "shape":
            raise AttributeError("attribute 'shape' of 'secvfile.Geometry' objects is not writable")
        self.__getitem__(k)
        val = dict(self._val)
        val[k] = v
        self.__init__(self._hub, val)
    def __getattr__(self, name):
        if name in ['xy_oib', 'z_oib']:
            raise AttributeError("attribute '{0}' doesn't exist".format(name))
        try:
            return self[name]
        except:
            raise AttributeError("attribute '{0}' doesn't exist".format(name))
    def __setattr__(self, name, value):
        pass
    def __delattr__(self, name):
        pass
    def __str__(self):
         strs = [str(self._val["shape"]),
                 "{0:<15}".format(str(self._val["res_xy"])[:15]),
                 "{0:<15}".format(str(self._val["res_z"])[:15]),
                 "{0:<15}".format(str(self._val["im_size"])[:15]),
                 "{0:<15}".format(str(self._val["exp_rate"])[:15]),
                 "{0:<15}".format(str(self._val["bar_len"])[:15])]
         text = "   shape:  {0}  # px (CZYX)\n".format(strs[0])
         m = len(text) - 40
         text += "  res_xy:  {0}".format(strs[1]) + " "*m + "  # um/px\n"
         text += "   res_z:  {0}".format(strs[2]) + " "*m + "  # um/px\n"
         text += " im_size:  {0}".format(strs[3]) + " "*m + "  # px\n"
         text += "exp_rate:  {0}\n".format(strs[4])
         text += " bar_len:  {0}".format(strs[5]) + " "*m + "  # um"
         return text
        
class Position(list):
    def __init__(self, hub, val, mode="all"):
        ratio = hub.geometry._ratio
        if mode == "all":
            _val = np.float64(val)
            _val[1:,0] *= ratio
            _val[2] /= np.linalg.norm(_val[2])
            _val[1] = _val[1] - _val[2]*np.inner(_val[1], _val[2])
            _val[1] /= np.linalg.norm(_val[1])
            _val[1:,0] /= ratio
            _val = _val.tolist()
        elif mode == "center":
            hub.position[0] = val
            _val = hub.position._val[0]
        elif mode == "vertical":
            hub.position[1] = val
            _val = hub.position._val[1]
        elif mode == "horizontal":
            hub.position[2] = val
            _val = hub.position._val[2]
        object.__setattr__(self, "_mode", mode)
        object.__setattr__(self, "_val" , _val)
        object.__setattr__(self, "_hub" , hub)
        list.__init__(self, _val)
    def __str__(self):
        if self._mode == "all":
            pos = self.asarray()
            text = pos.__repr__()
            text = text.split("\n")
            text = [text[i][6:-1] for i in range(3)]
            l = len(text[0])//3 - 1
            text[0] = text[0] + "   # center (px)"
            text[1] = text[1] + "   # vertical"
            text[2] = text[2] + "  # horizontal"
            text = ["#  Z" + " "*l + "Y" + " "*l + "X"] + text
            text = "\n".join(text)
            return text
        else:
            pos = self.asarray()
            text = " " + pos.__repr__()[6:-1]
            l = len(text)//3 - 1
            text = ["#  Z" + " "*l + "Y" + " "*l + "X"] + [text]
            text = "\n".join(text) + "   # " + self._mode
            if self._mode == "center":
                text += " (px)"
            return text
    def __setitem__(self, x, v):
        val = np.float64(self._val)
        val[x] = v
        val = val.tolist()
        self.__init__(self._hub, val, mode=self._mode)
    def __getitem__(self, x):
        if self._mode == "all":
            mode = ["center", "vertical", "horizontal"][x]
            return Position(self._hub, self._val[x], mode=mode)
        else:
            return self._val[x]
    def __setattr__(self, name, value):
        pass
    def __delattr__(self, name):
        pass
    def asarray(self):
        return np.array(self._val)

class Channels:
    def __init__(self, hub, val):
        object.__setattr__(self, "_hub" , hub)
        if type(val) == SuperList:
            object.__setattr__(self, '_val', val)
        else:
            val = [[str(c[0]), [max(0, min(255, int(c[1][i]))) for i in range(3)], 
                    max(0, min(65534, int(c[2]))), 
                    max(1, min(65535, max(int(c[2])+1, int(c[3]))))] for c in val]
            object.__setattr__(self, "_val" , SuperList(val))
        self._refresh()
    def __str__(self):
        ch_nm = self.getnames()
        m = max([len(nm) for nm in ch_nm])
        text = "# Name" + " "*m + " Color (BGR)      Vrange\n"
        ch_cl = self.getcolors()
        ch_vr = self.getvranges()
        text += "[['{0}'".format(ch_nm[0])
        text += " "*(m - len(ch_nm[0])) 
        text += ", [{0:>3}, {1:>3}, {2:>3}]".format(ch_cl[0][0], ch_cl[0][1], ch_cl[0][2])
        text += ", [{0:>5}, {1:>5}]]".format(ch_vr[0][0], ch_vr[0][1])
        for i in range(1, len(ch_nm)):
            text += ",\n ['{0}'".format(ch_nm[i])
            text += " "*(m - len(ch_nm[i]) - 1) 
            text += ", [{0:>3}, {1:>3}, {2:>3}]".format(ch_cl[i][0], ch_cl[i][1], ch_cl[i][2])
            text += ", [{0:>5}, {1:>5}]]".format(ch_vr[i][0], ch_vr[i][1])
        text += "]"
        return text
    def __getitem__(self, x):
        if type(x) == int:
            return Channel(self, self._val[x])
        if type(x) == str:
            w = np.where(np.array(self.getnames())==x)[0].tolist()
            if len(w) == 0:
                raise KeyError("Channel name '{0}' does not exist".format(x))
            x = w
        return Channels(self._hub, self._val[x])
    def __setitem__(self, x, v):
        if type(x) != int:
            raise TypeError("Channels object only supports item assignment with int indices")
        pre = self._val[x]
        try:
            self._val[x] = v
            self._refresh()
        except:
            self._val[x] = pre
            raise ChannelError("an invalid channel object '{0}'".format(v))
    def __setattr__(self, name, value):
        pass
    def __delattr__(self, name):
        pass
    def __len__(self):
        return len(self._val)
    def getnames(self):
        return [c[0] for c in self._val]
    def getcolors(self):
        return [[c[1][i] for i in range(3)] for c in self._val]
    def getvranges(self):
        return [[c[2], c[3]] for c in self._val]
    def _refresh(self):
        val = self._val
        _val = [[str(c[0]), [max(0, min(255, int(c[1][i]))) for i in range(3)], 
                 max(0, min(65534, int(c[2]))), 
                 max(1, min(65535, max(int(c[2])+1, int(c[3]))))] for c in val]
        for i in range(len(val)):
            val[i][0] = _val[i][0]
            val[i][1][0] = _val[i][1][0]
            val[i][1][1] = _val[i][1][1]
            val[i][1][2] = _val[i][1][2]
            val[i][2] = _val[i][2]
            val[i][3] = _val[i][3]
        object.__setattr__(self._hub, "colors", np.array(self.getcolors(), np.uint8))
        vrange = np.array(self.getvranges())
        lut = np.arange(65536)[None]
        diff = vrange[:,1] - vrange[:,0]
        lut = ((1/diff[:,None])*(lut - vrange[:,:1]))
        lut[lut<1/255] = 1/255
        lut[lut>1] = 1
        object.__setattr__(self._hub, "lut", lut)
class Channel:
    def __init__(self, sup, val):
        object.__setattr__(self, "_val" , val)
        object.__setattr__(self, "_sup" , sup)
    def __str__(self):
        return str(self._val)
    def __getitem__(self, x):
        if type(self._val[x]) == list:
            return Channel(self._sup, self._val[x])
        else:
            return self._val[x]
    def __setitem__(self, x, v):
        if type(x) != int:
            raise TypeError("Channel object only supports item assignment with int indices")
        pre = self._val[x]
        try:
            self._val[x] = v
            self._sup._refresh()
        except:
            self._val[x] = pre
            raise ChannelError("an invalid value '{0}'".format(v))
    def __setattr__(self, name, value):
        pass
    def __delattr__(self, name):
        pass
        
class Points:
    def __init__(self, hub, val):
        object.__setattr__(self, "_hub" , hub)
        if type(val) == SuperList:
            object.__setattr__(self, "_val" , val)
        else:
            dc, dz, dy, dx = hub.geometry["shape"]
            d = [dz, dy, dx]
            val = [[str(c[0]), [max(0, min(255, int(c[1][i]))) for i in range(3)], 
                   [float(max(-d[i]//2, min(d[i]+d[i]//2, float(c[2][i])))) for i in range(3)]] for c in val]
            object.__setattr__(self, "_val" , SuperList(val))
        self._refresh()
    def __str__(self):
        if len(self) == 0:
            return "[]"
        pt_nm = self.getnames()
        pt_cl = self.getcolors()
        cr = str(np.array(self.getcoordinates()))
        cr = cr.split("\n")
        cr[-1] = cr[-1][:-1]
        l = (len(cr[0][1:]) - 4)//3 + 1
        cr = [cr[i][1:l+1] + "," + cr[i][l+1:2*l+1] + "," + cr[i][2*l+1:] for i in range(len(cr))]
        if len(cr) == len(self) or len(self) == 0:
            m = max([len(nm) for nm in pt_nm])
            text = "# Name" + " "*m + " Color (BGR)      Coordinate (ZYX px)\n"
            text += "[['{0}'".format(pt_nm[0])
            text += " "*(m - len(pt_nm[0])) 
            text += ", [{0:>3}, {1:>3}, {2:>3}]".format(pt_cl[0][0], pt_cl[0][1], pt_cl[0][2])
            text += ", {0}]".format(cr[0])
            for i in range(1,len(pt_nm)):
                text += ",\n ['{0}'".format(pt_nm[i])
                text += " "*(m - len(pt_nm[i])) 
                text += ", [{0:>3}, {1:>3}, {2:>3}]".format(pt_cl[i][0], pt_cl[i][1], pt_cl[i][2])
                text += ", {0}]".format(cr[i])
            text += "]"
        else:
            pt_nm = pt_nm[:3] + ["..."] + pt_nm[-3:]
            m = max([len(nm) for nm in pt_nm])
            text = "# Name" + " "*m + " Color (BGR)      Coordinate (ZYX px)\n"
            text += "[['{0}'".format(pt_nm[0])
            text += " "*(m - len(pt_nm[0])) 
            text += ", [{0:>3}, {1:>3}, {2:>3}]".format(pt_cl[0][0], pt_cl[0][1], pt_cl[0][2])
            text += ", {0}]".format(cr[0])
            for i in range(1, 3):
                text += ",\n ['{0}'".format(pt_nm[i])
                text += " "*(m - len(pt_nm[i])) 
                text += ", [{0:>3}, {1:>3}, {2:>3}]".format(pt_cl[i][0], pt_cl[i][1], pt_cl[i][2])
                text += ", {0}]".format(cr[i])
            text += ",\n ..."
            for i in range(-3,0):
                text += "\n ['{0}'".format(pt_nm[i])
                text += " "*(m - len(pt_nm[i])) 
                text += ", [{0:>3}, {1:>3}, {2:>3}]".format(pt_cl[i][0], pt_cl[i][1], pt_cl[i][2])
                text += ", {0}],".format(cr[i])
            text = text[:-1] + "]"
        return text
    def __getitem__(self, x):
        if type(x) == int:
            return Point(self, self._val[x])
        if type(x) == str:
            w = np.where(np.array(self.getnames())==x)[0].tolist()
            if len(w) == 0:
                raise KeyError("Point name '{0}' does not exist".format(x))
            x = w
        return Points(self._hub, self._val[x])
    def __setitem__(self, x, v):
        if type(x) != int:
            raise TypeError("Points object only supports item assignment with int indices")
        pre = self._val[x]
        try:
            self._val[x] = v
            self._refresh()
        except:
            self._val[x] = pre
            raise PointError("an invalid point object '{0}'".format(v))
    def __delitem__(self, x):
        del self._val[x]
    def __setattr__(self, name, value):
        pass
    def __delattr__(self, name):
        pass
    def __len__(self):
        return len(self._val)
    def __iadd__(self, other):
        dc, dz, dy, dx = self._hub.geometry["shape"]
        d = [dz, dy, dx]
        val = [[str(c[0]), [max(0, min(255, int(c[1][i]))) for i in range(3)], 
               [float(max(-d[i]//2, min(d[i]+d[i]//2, float(c[2][i])))) for i in range(3)]] for c in other]
        self._val += val
        return self
    def _refresh(self):
        val = self._val
        dc, dz, dy, dx = self._hub.geometry["shape"]
        d = [dz, dy, dx]
        _val = [[str(c[0]), [max(0, min(255, int(c[1][i]))) for i in range(3)], 
                [float(max(-d[i]//2, min(d[i]+d[i]//2, float(c[2][i])))) for i in range(3)]] for c in val]
        for i in range(len(val)):
            val[i][0] = _val[i][0]
            val[i][1][0] = _val[i][1][0]
            val[i][1][1] = _val[i][1][1]
            val[i][1][2] = _val[i][1][2]
            val[i][2][0] = _val[i][2][0]
            val[i][2][1] = _val[i][2][1]
            val[i][2][2] = _val[i][2][2]
    def getnames(self):
        return [c[0] for c in self._val]
    def getcolors(self):
        return [[c[1][i] for i in range(3)] for c in self._val]
    def getcoordinates(self):
        return [[c[2][i] for i in range(3)] for c in self._val]
    def append(self, x):
        dc, dz, dy, dx = self._hub.geometry["shape"]
        d = [dz, dy, dx]
        val = [str(x[0]), [max(0, min(255, int(x[1][i]))) for i in range(3)], 
               [float(max(-d[i]//2, min(d[i]+d[i]//2, float(x[2][i])))) for i in range(3)]]
        self._val.append(val)
    def clear(self):
        self._val.clear()
    def extend(self, x):
        dc, dz, dy, dx = self._hub.geometry["shape"]
        d = [dz, dy, dx]
        val = [[str(c[0]), [max(0, min(255, int(c[1][i]))) for i in range(3)], 
               [float(max(-d[i]//2, min(d[i]+d[i]//2, float(c[2][i])))) for i in range(3)]] for c in x]
        self._val.extend(val)
    def pop(self, x=None):
        if x == None:
            x = len(self) - 1
        return self._val.pop(x)
    def add(self, name=None, color=None, coordinates=None):
        if name==None:
            name = "p0"
            names = self.getnames()
            i = 1
            while name in names:
                name = "p{0}".format(i)
                i += 1
        if type(color) == type(None):
            color = [0, 255, 255]
        if type(coordinates) == type(None):
            coordinates = self._hub.position[0]
        dc, dz, dy, dx = self._hub.geometry["shape"]
        d = [dz, dy, dx]
        val = [str(name), [max(0, min(255, int(color[i]))) for i in range(3)], 
               [float(max(-d[i]//2, min(d[i]+d[i]//2, float(coordinates[i])))) for i in range(3)]]
        self._val.append(val)
        
class Point:
    def __init__(self, sup, val):
        object.__setattr__(self, "_val" , val)
        object.__setattr__(self, "_sup" , sup)
    def __str__(self):
        return str(self._val)
    def __getitem__(self, x):
        if type(self._val[x]) == list:
            return Point(self._sup, self._val[x])
        else:
            return self._val[x]
    def __setitem__(self, x, v):
        if type(x) != int:
            raise TypeError("Point object only supports item assignment with int indices")
        pre = self._val[x]
        try:
            self._val[x] = v
            self._sup._refresh()
        except:
            self._val[x] = pre
            raise PointError("an invalid value '{0}'".format(v))
    def __setattr__(self, name, value):
        pass
    def __delattr__(self, name):
        pass
        
class Snapshots:
    def __init__(self, hub, val):
        if type(val) == SuperList:
            object.__setattr__(self, "_val" , val)
        else:
            _val = list(val)
            object.__setattr__(self, "_val" , SuperList(_val))
        object.__setattr__(self, "_hub" , hub)
    def __str__(self):
        return str(self.getnames())
    def __setattr__(self, name, value):
        pass
    def __delattr__(self, name):
        pass
    def __getitem__(self, x):
        if type(x) == int:
            return Snapshot(self._hub, self._val[x])
        if type(x) == str:
            w = np.where(np.array(self.getnames())==x)[0].tolist()
            if len(w) == 0:
                raise KeyError("Snapshot name '{0}' does not exist".format(x))
            x = w
        return Snapshots(self._hub, self._val[x])
    def getnames(self):
        return [s['name'] for s in self._val]
class Snapshot:
    def __init__(self, hub, val):
        object.__setattr__(self, '_val', val)
        object.__setattr__(self, '_hub', hub)
        try:
            keys = list(hub.classes.keys())
            keys.remove("snapshots")
            for k in keys:
                object.__setattr__(self, k, hub.classes[k](self, val[k]))
        except:
            raise SnapshotError("an invalid Snapshot object")
    def __setitem__(self, k, v):
        if k == 'name':
            self._val[k] = v
        else:
            raise SnapshotError("cannot change Snapshot object except name")
    def __setattr__(self, name, value):
        pass
    def __delattr__(self, name):
        pass
    def __str__(self):
        text = "     name:  " + self._val['name'] + "\n"
        text += "     data:  " + os.path.basename(self.data[0][0])
        if len(self.data) > 1:
            text += ", ..."
        text += "\n"
        gm = "( " + str(self.geometry.shape)[1:-1] + " )"
        text += " geometry:  shape: {0}, ...\n".format(gm)
        ps = "[ " + str([round(v,2) for v in self.position._val[0]])[1:-1] + " ]"
        text += " position:  {0}, ... \n".format(ps)
        ch = self.channels.getnames()
        ch = str(ch) if len(ch) <= 3 else str(ch[:3])[:-1] + ", ...]"
        ch = ch[1:-1].replace("'", "")
        text += " channels:  {0}\n".format(ch)
        pt = self.points.getnames()
        pt = str(pt) if len(pt) <= 3 else str(pt[:3])[:-1] + ", ...]"
        pt = pt[1:-1].replace("'", "")
        text += "   points:  {0}".format(pt)
        return text
    def restore(self, position=True, channels=True, points=True):
        secv = self._hub._secv
        if position:
            secv['position'] = self._val['position']
            secv['geometry'] = self._val['geometry']
        if channels:
            secv['channels'] = self._val['channels']
            secv['data'] = self._val['data']
        if points:
            secv['points'] = self._val['points']
        self._hub.__init__(secv)
    def override(self, position=True, channels=True, points=True):
        secv = self._hub._secv
        if position:
            self._val['position'] = secv['position']
            self._val['geometry'] = secv['geometry']
        if channels:
            self._val['channels'] = secv['channels']
            self._val['data'] = secv['data']
        if points:
            self._val['points'] = secv['points']
        keys = list(self._hub.classes.keys())
        keys.remove("snapshots")
        for k in keys:
            object.__setattr__(self, k, self._hub.classes[k](self, self._val[k]))

class SectionViewer(dict):
    def __init__(self, x):
        classes = {    "data": Data    ,
                   "geometry": Geometry,
                   "position": Position,
                   "channels": Channels,
                     "points": Points  ,
                   "snapshots": Snapshots}
        object.__setattr__(self, "classes", classes)
        dict.__init__(self, classes)
        if type(x) == str:
            with open(x, "rb") as st:
                secv = pickle.load(st)
            try:
                for k in classes:
                    self[k] = secv[k]
                object.__setattr__(self, "_path", x)
            except:
                ext = os.path.splitext(x)[1]
                if ext == ".secv":
                    raise SecvError("an invalid SECV file")
                else:
                    raise SecvError("not a SECV file")
        else:
            secv = x
            try:
                for k in classes:
                    self[k] = secv[k]
            except:
                raise SecvError("an invalid SECV object")
        object.__setattr__(self, "_secv", secv)
    def __setitem__(self, k, v):
        self.__getitem__(k)
        ins = self.classes[k](self, v)
        object.__setattr__(self, k, ins)
        dict.__setitem__(self, k, ins)
    def __setattr__(self, name, value):
        self.__getattribute__(name)
        self.__setitem__(name, value)
    def __delattr__(self, name):
        pass
    def __str__(self):
        text = "     data:  " + os.path.basename(self.data[0][0])
        if len(self.data) > 1:
            text += ", ..."
        text += "\n"
        gm = "( " + str(self.geometry.shape)[1:-1] + " )"
        text += " geometry:  shape: {0}, ...\n".format(gm)
        ps = "[ " + str([round(v,2) for v in self.position._val[0]])[1:-1] + " ]"
        text += " position:  {0}, ... \n".format(ps)
        ch = self.channels.getnames()
        ch = str(ch) if len(ch) <= 3 else str(ch[:3])[:-1] + ", ...]"
        ch = ch[1:-1].replace("'", "")
        text += " channels:  {0}\n".format(ch)
        pt = self.points.getnames()
        pt = str(pt) if len(pt) <= 3 else str(pt[:3])[:-1] + ", ...]"
        pt = pt[1:-1].replace("'", "")
        text += "   points:  {0}\n".format(pt)
        ss = self.snapshots.getnames()
        ss = str(ss) if len(ss) <= 3 else str(ss[:3])[:-1] + ", ...]"
        ss = ss[1:-1].replace("'", "")
        text += "snapshots:  " + ss
        return text
    def save(self, path=None):
        secv = self._secv
        if path == None:
            if hasattr(self, '_path'):
                path = self._path
            else:
                raise PathNotGivenError("must specify file path with save(path='file path')")
        secv['data'] = tuple(self.data._val)
        secv['geometry'] = self.geometry._val
        secv['position'] = self.position._val
        secv['channels'] = self.channels._val._val
        secv['points'] = self.points._val._val
        secv['snapshots'] = self.snapshots._val._val
        with open(path, "wb") as f:
            pickle.dump(secv, f, protocol=4)
    def reload(self):
        if not hasattr(self, '_path'):
            raise PathNotGivenError("file path source SECV file does not exist")
        self.__init__(self._path)
    def imread(self):
        files = self.data.files_to_load()
        channels = self.data.channels_to_load()
        boxes = []    
        for i, f in enumerate(files):
            if not os.path.isfile(f):
                import platform
                import cv2
                from PIL import Image, ImageTk
                import tkinter as tk
                from tkinter import messagebox
                from tkinter import filedialog
                
                pf = platform.system()
                
                root = tk.Tk()
                cd = os.path.dirname(os.path.abspath(__file__))
                if pf == 'Windows':
                    root.iconbitmap(cd + '/img/icon.ico')
                icon = cv2.imread(cd + '/img/resources.png')[-128:,:128]
                icon = ImageTk.PhotoImage(Image.fromarray(icon[:,:,::-1]))
                canvas = tk.Canvas(root, width=240, height=150)
                canvas.create_rectangle(0, 0, 2000, 2000, fill='#606060', width=0)
                canvas.create_image(56, 11, image=icon, anchor='nw')
                canvas.pack()
                root.geometry('+0+0')
                root.title('SectionViewer')
                
                messagebox.showinfo('Information',
                                    '''The following file path seems to have been changed:
{0}
Please specify the file again.'''.format(f), parent=root)
                filetypes = [('OIB/TIFF files', ['*.oib', '*.tif', '*.tiff']),
                             ('All files', '*')]
                initialdir = os.path.dirname(f)
                initialfile = os.path.splitext(os.path.basename(f))[0]
                f = filedialog.askopenfilename(parent=root, 
                                               filetypes=filetypes, 
                                               initialdir=initialdir, 
                                               initialfile=initialfile,
                                               title='Find {0}'.format(os.path.basename(f)))
                root.destroy()
                if len(f) == 0:
                    return
                f = f.replace('\\', '/')
                
            if os.path.splitext(f)[1] == ".oib":
                boxes += [oif.imread(f)]
            elif os.path.splitext(f)[1] in [".tif", ".tiff"]:
                boxes += [tif.imread(f)]
            elif os.path.splitext(f)[1] == ".pickle":
                with open(f, "rb") as g:
                    boxes += [pickle.load(g)]
            else:
                raise TypeError("file type '{0}' is not supported".format(os.path.splitext(f)[1]))
            
        boxes = [boxes[i][None] if boxes[i].ndim == 3 else boxes[i] for i in range(len(boxes))]
        box = boxes[0][np.array(channels[0])]
        del boxes[0]
        n = 1
        if box.dtype != np.uint16:
            box = box.astype(np.uint16)
        while len(boxes) > 0:
            b = boxes[0][np.array(channels[n])]
            if b.dtype != np.uint16:
                b = b.astype(np.uint16)
            box = np.append(box, b, axis=0)
            del b, boxes[0]
            n += 1
        object.__setattr__(self, "image", box)
    def create_section(self, channels=None, thickness=1):
        if not hasattr(self, "image"):
            raise AttributeError("Attribute 'image' not found. Call 'imread' method beforehand.")
        if channels is None:
            channels = np.arange(len(self.image))
        else:
            if not hasattr(channels, '__iter__'):
                channels = [channels]
            if False in [type(c) == int for c in channels]:
                raise TypeError('integers are required as channels')
            channels = np.int32(channels)
            channels = channels[channels>=0]
            channels = channels[channels<len(self.image)]
        if type(thickness) != int:
            raise TypeError("an integer is required as thickness")
        geo = self.geometry
        xy_rs, z_rs = geo["res_xy"], geo["res_z"]
        if None in [xy_rs, z_rs]:
            ratio = 1.
        else:
            ratio = z_rs / xy_rs
        res = np.empty([len(self.image), *geo["im_size"][::-1]], np.uint16)
        box = self.image
        dc, dz, dy, dx = box.shape
        pos = self.position.asarray()
        pos[0] -= np.array([dz, dy, dx])//2
        pos[:,0] *= ratio
        op, ny, nx = pos.copy()
        nz = -np.cross(ny, nx)
        pos[:,0] /= ratio
        nz[0] /= ratio
        pos[0] += np.array([dz, dy, dx])//2
        pos[1:] /= self.geometry["exp_rate"]
        nz /= self.geometry["exp_rate"]
        if thickness == 1:
            if not ut.calc_section(box, pos, res, np.array(res[0].shape)//2,
                                   channels):
                res[:] = 0
        else:
            start = -(thickness//2)
            stop = start + thickness
            if not ut.stack_section(box, pos, nz, start, stop, res,
                                    np.array(res[0].shape)//2, channels):
                res[:] = 0
        exp_rate = geo["exp_rate"]
        resol = xy_rs/exp_rate if xy_rs != None else None
        print("resolution: {0} um/px".format(resol))
        return res
    def create_image(self, frame=None, channels=None, thickness=1):
        if frame is None:
            frame = self.create_section(channels=channels, thickness=thickness)
        res = np.empty([*frame[0].shape, 4], np.uint8)
        ut.calc_bgr(frame, self.lut, self.colors, np.arange(len(frame)), res)
        return res
    
    
class SuperList:
    def __init__(self, val, focus=None):
        if focus is None:
            focus = [i for i in range(len(val))]
        object.__setattr__(self, '_val', val)
        object.__setattr__(self, '_focus', focus)
    def __getitem__(self, x):
        focus = self._focus
        if type(x) == int:
            return self._val[focus[x]]
        if type(x) == slice:
            focus = focus[x]
            return SuperList(self._val, focus=focus)
        else:
            focus = [focus[i] for i in x]
            return SuperList(self._val, focus=focus)
    def __setitem__(self, x, v):
        focus = self._focus
        if type(x) == int:
            self._val[focus[x]] = v
        else:
            raise TypeError("SuperList object only supports item assignment with int indices")
    def __setattr__(self, name, value):
        pass
    def __len__(self):
        return len(self._focus)
    def append(self, val):
        self._focus.append(len(self._val))
        self._val.append(val)
    def clear(self):
        self._focus.clear()
        self._val.clear()
    def extend(self, val):
        self._focus.extend([i for i in range(len(self._val), len(self._val)+len(val))])
        self._val.extend(val)
    def pop(self, x=None):
        if x is None:
            x = len(self) - 1
        val = self._val.pop(self._focus[x])
        object.setattr(self, '_focus', self._focus[:x] + self._focus[x+1:])
        return val
            
        
class SecvError(Exception):
    pass
class ChannelError(Exception):
    pass
class PointError(Exception):
    pass
class SnapshotError(Exception):
    pass
class PathNotGivenError(Exception):
    pass
        
        
