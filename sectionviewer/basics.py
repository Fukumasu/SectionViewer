from typing import Union
import numpy as np

sf = 5
geometry_key_patterns = [
    ['res_xy', 'X_px_size'],
    ['res_xy', 'Y_px_size'],
    ['res_z', 'Z_px_size'],
    ['exp_rate', 'expansion_rate'],
    ['im_size', 'image_size'],
    ['bar_len', 'scale_bar_length']
    ]
gkp = dict(geometry_key_patterns)

class FrozenList(list):
    def __setitem__(self, *args):
        raise ValueError('cannon replace items')
    def __imul__(self, *args):
        raise ValueError('cannon change length')
    def __iadd__(self, *args):
        raise ValueError('cannon change length')
    def __delitem__(self, *args):
        raise ValueError('cannon delete items')
    def __setattr__(self, name, value):
        self.__getattribute__(name)
        raise AttributeError('cannot change attributes in {0}'.format(type(self)))
    def __delattr__(self, name):
        raise AttributeError('cannot delete attributes in {0}'.format(type(self)))
    def append(self, obj):
        raise AttributeError("'{0}' object has no attribute 'append'".format(type(self)))
    def clear(self):
        raise AttributeError("'{0}' object has no attribute 'clear'".format(type(self)))
    def extend(self, obj):
        raise AttributeError("'{0}' object has no attribute 'extend'".format(type(self)))
    def pop(self, x):
        raise AttributeError("'{0}' object has no attribute 'pop'".format(type(self)))
        
class FrozenDict(dict):
    def __setitem__(self, k, v):
        if k in self:
            raise ValueError('cannon replace items')
        else:
            raise ValueError('cannon add items')
    def __delitem__(self, *args):
        raise ValueError('cannot delete items')
    def __setattr__(self, name, value):
        self.__getattribute__(name)
        raise AttributeError('cannot change attributes in {0}'.format(type(self)))
    def __delattr__(self, name):
        raise AttributeError('cannot delete attributes in {0}'.format(type(self)))
        
class FrozenArray(np.ndarray):
    def __new__(cls, obj):
        if type(obj) == np.ndarray:
            self = obj.view(cls)
        else:
            self = np.asarray(obj).view(cls)
        return self
    def __setitem__(self, *args):
        raise ValueError('cannot change array elements')
    def __setattr__(self, name, value):
        self.__getattribute__(name)
        raise AttributeError('cannot change attributes in {0}'.format(type(self)))
    def __delattr__(self, name):
        raise AttributeError('cannot delete attributes in {0}'.format(type(self)))
        
class Channel(FrozenList):
    def __init__(self, ch: list = None):
        if ch is None:
            ch = [None, None, None]
        ch = list(ch)[:4]
        ch[0] = str(ch[0]) if ch[0] is not None else None
        ch[1] = Color(ch[1])
        ch[2] = VRange(ch[2:])
        ch = ch[:3]
        super().__init__(ch)
        
    def __setitem__(self, k, v):
        if k == 0:
            v = str(v) if v is not None else None
        elif k == 1:
            v = Color(v)
        elif k == 2:
            v = VRange(v)
        else:
            raise IndexError('index has to be one of (0, 1, 2)')
        list.__setitem__(self, k, v)
    
    def _issame(self, other):
        return [self[i] == other[i] for i in range(3)]
    
    def _format(self) -> list:
        return [str(self[0]), [self[1][0], self[1][1], self[1][2]], self[2][0], self[2][1]]

class Point(FrozenList):
    def __init__(self, pt: list = None):
        if pt is None:
            pt = [None, None, None]
        pt = list(pt)[:3]
        pt[0] = str(pt[0]) if pt[0] is not None else None
        pt[1] = Color(pt[1])
        pt[2] = Coordinate(pt[2])
        super().__init__(pt)
    
    def __setitem__(self, k, v):
        if k == 0:
            v = str(v) if v is not None else None
        elif k == 1:
            v = Color(v)
        elif k == 2:
            v = Coordinate(v)
        else:
            raise IndexError('index has to be one of (0, 1, 2)')
        list.__setitem__(self, k, v)
        
    def _issame(self, other):
        return [self[i] == other[i] for i in range(3)]
    
    def _format(self) -> list:
        return [str(self[0]), [self[1][0], self[1][1], self[1][2]], 
                [self[2][0], self[2][1], self[2][2]]]
        
        
class Snapshot(FrozenDict):
    def __init__(self, metadata: dict):
        for k in list(metadata.keys()):
            if k not in ['name', 'files', 'geometry', 
                         'position', 'channels', 'points']:
                dict.__delitem__(metadata, k)
        if not 'name' in metadata:
            dict.__setitem__(metadata, 'name', None)
        for k in list(metadata['geometry'].keys()):
            if k in gkp:
                metadata['geometry'][gkp[k]] = metadata['geometry'][k]
                del metadata['geometry'][k]
        super().__init__(metadata)
    
    def __getattribute(self, name):
        if name in self:
            return self[name]
        return super().__getattribute__(name)
    
    def __setitem__(self, k, v):
        if k not in self:
            raise KeyError(k)
        if k == 'name' and type(v) != str:
            v = str(v)
        elif k == 'files' and type(v) != dict:
            if hasattr(v, '_format'):
                v = v._format()
            else:
                v = dict(v)
        elif k == 'geometry' and type(v) != dict:
            if hasattr(v, '_format'):
                v = v._format()
            else:
                v = dict(v)
        elif k == 'position' and type(v) != list:
            if hasattr(v, '_format'):
                v = v._format()
            elif hasattr(v, 'tolist'):
                v = v.tolist()
            else:
                v = list(v)
        elif k == 'channels' and type(v) != list:
            if hasattr(v, '_format'):
                v = v._format()
            else:
                v = list(v)
        elif k == 'points' and type(v) != list:
            if hasattr(v, '_format'):
                v = v._format()
            else:
                v = list(v)
        dict.__setitem__(self, k, v)
    
    def _issame(self, other):
        res = {}
        for k in self.keys():
            res[k] = self[k] == other[k]
        return res
    
    def _format(self) -> dict:
        res = {}
        res['name'] = self['name']
        res['files'] = dict(self['files'])
        res['geometry'] = dict(self['geometry'])
        res['position'] = self['position'].copy()
        res['channels'] = [[c[0], [c[1][0], c[1][1], c[1][2]], 
                            c[2], c[3]] for c in self['channels']]
        res['points'] = [[p[0], [p[1][0], p[1][1], p[1][2]],
                          [p[2][0], p[2][1], p[2][2]]] for p in self['points']]
        return res

class Color(FrozenDict):
    def __new__(cls,
                bgr: list = None,
                hsl: list = None):
        if bgr is None and hsl is None:
            return None
        if hasattr(bgr, '__iter__'):
            if len(bgr) == 3:
                return super().__new__(cls)
        if hasattr(hsl, '__iter__'):
            if len(hsl) == 3:
                return super().__new__(cls)
        return None
    
    def __init__(self, 
                 bgr: list = None,
                 hsl: list = None):
        if hasattr(bgr, '__iter__'):
            if len(bgr) != 3:
                bgr = None
        if hasattr(hsl, '__iter__'):
           if len(hsl) != 3:
               hsl = None
        if bgr is None and hsl is None:
            raise ValueError('Either bgr or hsl has to be given as 3-length iterable.')
        color = {}
        if bgr is not None:
            bgr = list(bgr)
            color['bgr'] = BGR(bgr, self)
            hsl = self._bgr2hsl(bgr)
            color['hsl'] = HSL(hsl, self)
        else:
            hsl = list(hsl)
            color['hsl'] = HSL(hsl, self)
            bgr = self._hsl2bgr(hsl)
            color['bgr'] = BGR(bgr, self)
        super().__init__(color)
        
    def __getitem__(self, k):
        if type(k) == int:
            return self['bgr'][k]
        return super().__getitem__(k)
    
    def __setitem__(self, k, v: list):
        if type(k) == int:
            self['bgr'][k] = v
        elif k not in self:
            raise KeyError(k)
        elif k == 'bgr':
            dict.__setitem__(self, k, BGR(v, self))
            v = self._bgr2hsl(v)
            dict.__setitem__(self, 'hsl', HSL(v, self))
        else:
            dict.__setitem__(self, k, HSL(v, self))
            v = self._hsl2bgr(v)
            dict.__setitem__(self, 'bgr', BGR(v, self))
            
    def __iter__(self):
        return list.__iter__(self['bgr'])
    
    def __str__(self):
        return str(self['bgr'])
    
    def __repr__(self):
        return repr(self['bgr'])
    
    def __len__(self):
        return 3
    
    def __eq__(self, other):
        return self['bgr'] == other['bgr']
    
    def _reflect(self, key):
        v = self[key]
        if key == 'bgr':
            v = self._bgr2hsl(v)
            dict.__setitem__(self, 'hsl', HSL(v, self))
        else:
            v = self._hsl2bgr(v)
            dict.__setitem__(self, 'bgr', BGR(v, self))
            
    def _bgr2hsl(self, bgr: list) -> list:
        m = np.argmin(bgr)
        M = np.argmax(bgr)
        if m == M:
            return [0.,0.,bgr[m]/255*100]
        h = 60*(bgr[(m+1)%3] - bgr[(m-1)%3])/(bgr[M] - bgr[m]) + [60, 300, 180][m]
        s = 100*(bgr[M] - bgr[m])/(255 - abs(bgr[M] + bgr[m] - 255))
        l = (bgr[M] + bgr[m])*(10/51)
        return [h,s,l]
    
    def _hsl2bgr(self, hsl: list) -> list:
        d = hsl[1]*(100 - abs(2*hsl[2] - 100))*255/20000
        if d == 0:
            return [round(hsl[2]*255/100)]*3
        l = hsl[2]*255/100
        M = l + d
        m = l - d
        n = m + (M-m)*(1 - np.abs(1 - (hsl[0]%120)/60))
        if (hsl[0]//60)%2 == 0:
            bgr = [m, n ,M]
        else:
            bgr = [m, M, n]
        a = int(hsl[0]//120)
        bgr = [round(bgr[a%3]), round(bgr[(a+1)%3]), round(bgr[(a+2)%3])]
        return bgr
    
    
class BGR(FrozenList):
    def __init__(self, bgr: list, color: Color):
        bgr = list(bgr)
        assert len(bgr) == 3
        for i in range(3):
            if bgr[i] is None:
                bgr[i] = 255
            bgr[i] = int(bgr[i])
            bgr[i] = max(0, min(bgr[i], 255))
        super().__init__(bgr)
        object.__setattr__(self, 'color', color)
        
    def __setitem__(self, 
                    k: Union[int, slice], 
                    v: Union[int, list]):
        if hasattr(v, '__iter__'):
            for i in range(len(v)):
                v[i] = int(v[i])
                v[i] = max(0, min(v[i], 255))
        else:
            v = int(v)
            v = max(0, min(v, 255))
        list.__setitem__(self, k, v)
        self.color._reflect('bgr')
        
        
class HSL(FrozenList):
    def __init__(self, hsl: list, color: Color):
        hsl = list(hsl)
        assert len(hsl) == 3
        if hsl[0] is None:
            hsl[0] = 0
        hsl[0] = float(hsl[0])
        hsl[0] = max(0., min(hsl[0], 359.9))
        for i in range(1,3):
            if hsl[i] is None:
                hsl[i] = 100.
            hsl[i] = float(hsl[i])
            hsl[i] = max(0., min(hsl[i], 100.))
        super().__init__(hsl)
        object.__setattr__(self, 'color', color)
        
    def __setitem__(self, 
                    k: Union[int, slice], 
                    v: Union[float, list]):
        hsl = list(self)
        hsl[k] = v
        hsl[0] = min(max(0., float(hsl[0])), 359.9)
        for i in range(1,3):
            hsl[i] = min(max(0., float(hsl[i])), 100.)
        list.__setitem__(self, k, hsl[k])
        self.color._reflect('hsl')
        

def auto_color(units: list, ids: list, offset: int = 120):
    num_new = len(ids)
    fix = [i for i in range(len(units)) if i not in ids]
    
    if len(fix) == 0:
        if num_new == 1:
            units[0][1] = Color(bgr = [255, 255, 255])
            return
    
    if len(fix) > 0:
        
        hues_fix = np.array([units[i][1]['hsl'] for i in fix])
        hues_fix = hues_fix[(hues_fix[:,1] > 50) * 
                            (np.abs(hues_fix[:,2] - 50) < 25), 0]
        
    else: hues_fix = []
    
    if len(hues_fix) == 0:
        
        hues_new = np.linspace(offset, offset+360, num_new, endpoint=False)%360
        
    else:
        
        hues_fix = np.sort(hues_fix).astype(int)
        intvs = hues_fix[1:] - hues_fix[:-1]
        intvs = np.append(intvs, 360 - np.sum(intvs))
        nums = np.ones(len(intvs), int)
        for _ in range(num_new):
            n = np.argmax(intvs)
            intvs[n] *= nums[n]/(nums[n] + 1)
            nums[n] += 1
        hues_new = np.zeros(num_new)
        
        n = 0
        for i in range(0, len(hues_fix)-1):
            hues_new[n: n + nums[i] - 1] = \
                np.linspace(hues_fix[i], hues_fix[i+1], 
                            nums[i], endpoint=False)[1:]
            n += nums[i] - 1
        hues_new[n:] = \
            np.linspace(hues_fix[-1], hues_fix[0] + 360,
                        nums[-1], endpoint=False)[1:]%360
            
    news = np.append(hues_new[:,None], np.zeros([num_new, 2]), axis=1)
    news[:,1] = 100
    news[:,2] = 50
    
    n = 0
    for i in range(len(units)):
        if i not in fix:
            units[i][1] = Color(hsl = news[n])
            n += 1
            
            
class VRange(FrozenList):
    def __init__(self, vrange: list = None):
        if vrange is None:
            vrange = [0, 65535]
        if len(vrange) < 2:
            while hasattr(vrange[0], '__iter__'):
                vrange = vrange[0]
            if len(vrange) < 2:
                vrange += [None]
        if vrange[0] is None:
            vrange[0] = 0
        if vrange[1] is None:
            vrange[1] = 65535
        vrange[0] = max(0, min(vrange[0], 65534))
        vrange[1] = max(1, min(vrange[1], 65535))
        if not vrange[0] < vrange[1]:
            vrange[0] = vrange[1] - 1
        super().__init__(vrange[:2])
        
    def __setitem__(self, k, v: int):
        v = int(v)
        if k == 0:
            v = max(0, min(self[1] - 1, v))
            list.__setitem__(self, k, v)
        else:
            v = max(self[0] + 1, min(v, 65535))
            list.__setitem__(self, k, v)
            
    def __getitem__(self, k):
        if type(k) == str:
            return {'vmin': self[0], 'vmax': self[1]}[k]
        return super().__getitem__(k)
            
            
class Coordinate(FrozenList):
    def __new__(cls, coordinate: list = None):
        if cls._data_shape is None:
            raise ValueError('data shape has to be given to Coordinate class at first')
        return super().__new__(cls)
        
    def __init__(self, coordinate: list = None, **kargs):
        object.__setattr__(self, 'data_shape', self._data_shape)
        if coordinate is None:
            coordinate = [0., 0., 0.]
        for i in range(3):
            if coordinate[i] is None:
                coordinate[i] = 0.
        cr = [float(c) for c in coordinate[:3]]
        for i in range(3):
            if not -self.data_shape[i]//2 <= cr[i] \
                < self.data_shape[i] + self.data_shape[i]//2:
                raise CoordinateError('trying to set coordinate out of data array')
        super().__init__(cr)
        
    def __setitem__(self, k, v):
        cr = list(self)
        cr[k] = v
        for i in range(3):
            if not -self.data_shape[i]//2 <= cr[i] \
                < self.data_shape[i] + self.data_shape[i]//2:
                raise CoordinateError('trying to set coordinate out of data array')
        list.__setitem__(self, k, v)
        
    def __eq__(self, other):
        return [abs(self[i] - other[i]) < 10**(-sf) 
                for i in range(len(self))]
            
        
class CoordinateError(Exception):
    pass