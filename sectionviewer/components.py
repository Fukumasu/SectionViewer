import os

from .basics import FrozenList, FrozenDict, FrozenArray
from .basics import Channel, Point, Snapshot, Coordinate
from .basics import sf, auto_color
from typing import Union
import cv2
import numpy as np
        

class DataArray(FrozenArray):
    def __array_ufunc__(self, ufunc, method, *args, **kwargs):
        args_ = []
        for arg in args:
            arg = np.array(arg) if isinstance(arg, DataArray) else arg
            args_ += [arg]
        out = getattr(ufunc, method)(*args_, **kwargs)
        if out is NotImplemented:
            return NotImplemented
        return out
    
    def copy(self):
        return np.array(self, dtype = self.dtype)


class CUI():
    def __init__(self, metadata):
        object.__setattr__(self, 'metadata', metadata)
        
    def __getattribute__(self, name: str):
        if name == 'metadata':
            return object.__getattribute__(self, name)
        metadata = self.metadata
        if name in metadata:
            return metadata[name]
        return object.__getattribute__(self, name)
    
    def __setattr__(self, name, value):
        if name in self.metadata:
            self.metadata[name] = value
            return
        self.__getattribute__(name)
        if name == 'metadata':
            object.__setattr__(self, name, value)
            value = MetadataDict(self)
            object.__setattr__(self, name, value)
            return
        raise AttributeError('cannot change attributes in {0}'.format(type(self)))


class MetadataDict(FrozenDict):
    def __init__(self, cui = None, metadata = None):
        if metadata is None:
            metadata = {}
        if cui is None:
            cui = CUI(metadata)
        object.__setattr__(self, 'cui', cui)
        metadata = cui.metadata
        if 'files' in metadata:
            if 'points' in metadata:
                Coordinate._data_shape = metadata['files']['shape']
            metadata['files'] = FileDict(cui)
        if 'geometry' in metadata:
            metadata['geometry'] = GeometryDict(cui)
        if 'display' in metadata:
            metadata['display'] = DisplayDict(cui)
        if 'position' in metadata:
            metadata['position'] = PositionArray(cui)
        if 'channels' in metadata:
            metadata['channels'] = ChannelList(cui)
        if 'points' in metadata:
            metadata['points'] = PointList(cui)
        if 'snapshots' in metadata:
            metadata['snapshots'] = SnapshotList(cui)
        
        super().__init__(metadata)
        
    def __getattribute__(self, name: str):
        if name in self:
            return self[name]
        return super().__getattribute__(name)
    
    def __setitem__(self, k, v):
        if k not in self:
            raise KeyError(k)
        v0 = self[k]
        dict.__setitem__(self, k, v)
        try:
            if k == 'files' and type(v) != FileDict:
                dict.__setitem__(self, k, FileDict(self.cui))
            elif k == 'geometry' and type(v) != GeometryDict:
                dict.__setitem__(self, k, GeometryDict(self.cui))
            elif k == 'display' and type(v) != DisplayDict:
                dict.__setitem__(self, k, DisplayDict(self.cui))
            elif k == 'position' and type(v) != PositionArray:
                dict.__setitem__(self, k, PositionArray(self.cui))
            elif k == 'channels' and type(v) != ChannelList:
                dict.__setitem__(self, k, ChannelList(self.cui))
            elif k == 'points' and type(v) != PointList:
                dict.__setitem__(self, k, PointList(self.cui))
            elif k == 'snapshots' and type(v) != SnapshotList:
                dict.__setitem__(self, k, SnapshotList(self.cui))
        except Exception as e:
            dict.__setitem__(self, k, v0)
            raise e
            
    def __str__(self):
        if 'secv_path' in self.files:
            file_name = self.files['secv_path']
        elif 'stac_path' in self.files:
            file_name = self.files['stac_path']
        if file_name is not None:
            file_name = os.path.basename(file_name)
            text = '< SectionViewer metadata from {0} >\n'.format(file_name)
        else:
            text = '< SectionViewer metadata >\n'
        text += 'Files: ... , Geometry: ... , Display: ... , Position: ... ,\n'
        text += 'Channels: ... , Points: ... , Snapshots: ...'
        return text
            
    def copy(self):
        return MetadataDict(metadata = self._format())
    
    def _locate_difference(self, other) -> list:
        issame = {}
        for k in self:
            issame[k] = self[k]._issame(other[k])
        def search(ks: list, obj) -> list:
            typ = type(obj)
            if not hasattr(obj, '__iter__'):
                if not obj:
                    return [ks]
            elif typ == list:
                res = []
                for i in range(len(obj)):
                    re = search(ks + [i], obj[i])
                    if re is not None:
                        res += re
                return res
            else:
                res = []
                for k in obj:
                    re = search(ks + [k], obj[k])
                    if re is not None:
                        res += re
                return res
        res = search([], issame)
        return res
        
    def _format(self) -> dict:
        meta = {}
        for k in self:
            meta[k] = self[k]._format()
        return meta
    
    
class FileDict(FrozenDict):
    def __init__(self, cui):
        object.__setattr__(self, 'cui', cui)
        mf = cui.files
        if 'paths' in mf:
            paths = mf['paths']
            mf['paths'] = tuple([os.path.abspath(p).replace('\\', '/') for p in paths])
        if 'secv_path' in mf:
            if mf['secv_path'] is not None:
                mf['secv_path'] = mf['secv_path'].replace('\\', '/')
        elif 'stac_path' in mf:
            if mf['stac_path'] is not None:
                mf['stac_path'] = mf['stac_path'].replace('\\', '/')
        if 'original_secv_path' in mf:
            if mf['original_secv_path'] is not None:
                mf['original_secv_path'] = mf['original_secv_path'].replace('\\', '/')
        super().__init__(mf)
        
    def __setitem__(self, k, v):
        if k not in self:
            raise KeyError(k)
        if k != 'paths':
            raise ValueError("cannot change item '{0}'".format(k))
        if not hasattr(v, '__iter__'):
            v = [v]
        for f in v:
            ext = os.path.splitext(f)[1]
            if ext not in ('.oir', '.oib', '.tif', '.tiff'):
                raise TypeError('File type {0} is not supported.'.format(ext))
        v = [os.path.abspath(f).replace('\\', '/') for f in v]
        if len(v) != len(np.unique(v)):
            raise ValueError('same files cannot be loaded')
        v = tuple(v)
        dict.__setitem__(self, k, v)
        
    def __str__(self):
        text = '< Files >\n'
        if 'secv_path' in self:
            text += '{ ' + "'secv path': '{0}'".format(str(self['secv_path'])) + ',\n'
        elif 'stac_path' in self:
            text += '{ ' + "'stac path': '{0}'".format(str(self['stac_path'])) + ',\n'
        text += "      'paths': " + str(self['paths']) + ' }\n'
        return text
        
    def _issame(self, other):
        res = {}
        for k in self:
            res[k] = self[k] == other[k]
        return res
    
    def _format(self) -> dict:
        return dict(self)
    
    def add(self, new_files):
        if not hasattr(new_files, '__iter__'):
            new_files = [new_files]
        for f in new_files:
            ext = os.path.splitext(f)[1]
            if ext not in ('.oir', '.oib', '.tif', '.tiff'):
                raise TypeError('File type {0} is not supported.'.format(ext))
        self['paths'] = list(self['paths']) + list(new_files)
        
    def delete(self, file_ids):
        if not hasattr(file_ids, '__iter__'):
            file_ids = [file_ids]
        file_ids = np.sort(np.unique(file_ids))
        paths = list(self['paths'])
        for i in file_ids[::-1]:
            del paths[i]
        if len(paths) == 0:
            raise ValueError('Deleting all data is not allowed')
        self['paths'] = paths
        
        
class GeometryDict(FrozenDict):
    def __init__(self, cui):
        object.__setattr__(self, 'cui', cui)
        super().__init__(cui.geometry)
        
        keys = ['image_size', 'expansion_rate', 
                'X_px_size', 'Y_px_size', 'Z_px_size', 
                'scale_bar_length']
        for k in list(self.keys()):
            if k not in keys:
                dict.__delitem__(self, k)
        for k in keys:
            if k not in self:
                dict.__setitem__(self, k, None)
        if 'secv_path' in cui.files:
            for k in ['X_px_size', 'Y_px_size', 'Z_px_size']:
                if self[k] is None:
                    self[k] = cui.files[k + '_in_files']
        self._update_px_size()
        if self['image_size'] is None:
            self['image_size'] = cui.files['shape'][-1:-3:-1]
        if self['expansion_rate'] is None:
            self['expansion_rate'] = 1.
        self._update_scale_bar_length()
        if self['scale_bar_length'] is None:
            self._auto_scale_bar_length()
            
    def __setitem__(self, k, v):
        if 'files' not in self.cui.metadata:
            if k != 'scale_bar_length':
                return
        if k not in self:
            raise KeyError(k)
        if v is None:
            return
        if k == 'image_size':
            v = (int(v[0]), int(v[1]))
        else:
            v = float(v)
                
        dict.__setitem__(self, k, v)
        if 'px' in k:
            self._update_px_size()
        elif k == 'scale_bar_length':
            self._update_scale_bar_length()
        elif k == 'expansion_rate':
            self._auto_scale_bar_length()
        if k in ['image_size', 'expansion_rate']:
            if type(self.cui.position) == PositionArray:
                self.cui.position._update_depth()
                
    def __str__(self):
        m = np.amax([len(k) for k in self]) + 1
        text = ''
        for k in self:
            text += ' '*(m - len(k)) + "'" + k + "': "
            text += str(self[k])
            text += ',\n'
        m = [len(str(self[k])) for k in self]
        m = np.amax(m) - m[-1] + 2
        text = '< Geometry >\n{' + text[1:-2] + ' '*m + '}\n'
        return text
    
    def reset_px_sizes(self):
        if 'secv_path' in self.cui.files:
            for k in ['X_px_size', 'Y_px_size', 'Z_px_size']:
                self[k] = self.cui.files[k + '_in_files']
    
    def _update_px_size(self):
        xs = self['X_px_size']
        ys = self['Y_px_size']
        zs = self['Z_px_size']
        ss = [s for s in [zs, ys, xs] if s is not None]
        if len(ss) > 0:
            min_px_size = min(ss)
            anisotropy = DataArray([s/min_px_size if s is not None else 1.
                                    for s in [zs, ys, xs]])
        else: 
            min_px_size = None
            anisotropy = DataArray([1.,1.,1.])
        dict.__setattr__(self, '_min_px_size', min_px_size)
        if 'position' in self.cui.metadata:
            if type(self.cui.position) == PositionArray:
                object.__setattr__(self.cui.position, '_anisotropy', anisotropy)
            else:
                PositionArray._anisotropy = anisotropy
    
    def _update_scale_bar_length(self) -> None:
        if self._min_px_size is None:
            scale_bar_px = 0
        else:
            scale_bar_px = self['scale_bar_length']
            scale_bar_px *= self['expansion_rate'] / self._min_px_size
            scale_bar_px = int(scale_bar_px)
        object.__setattr__(self, '_scale_bar_px', scale_bar_px)
        
    def _auto_scale_bar_length(self) -> None:
        if self._min_px_size is not None:
            a = self._min_px_size / self['expansion_rate']
            scale_bar_length = round(80*a, -int(np.log10(80*a)))
        else: 
            scale_bar_length = 0
        self['scale_bar_length'] = scale_bar_length
                
    def _issame(self, other):
        res = {}
        for k in self:
            if type(self[k]) == float:
                res[k] = abs(self[k] - other[k]) < 10**(-sf)
            else:
                res[k] = self[k] == other[k]
            if not res[k]:
                if self[k] is None and other[k] is None:
                    res[k] = True
        return res
    
    def _format(self) -> dict:
        return dict(self)
    
    
class DisplayDict(FrozenDict):
    defaults = {
        'thickness': 1,
        'zoom': 1.,
        'axis': True,
        'scale_bar': True,
        'points': True,
        'dock': True,
        'white_back': False,
        'guide': True,
        'sideview': False,
        'center': None,
        'window_size': None,
        'shown_channels': None,
        'point_focus': -1,
        'index': 0
        }
    def __init__(self, cui):
        object.__setattr__(self, 'cui', cui)
        object.__setattr__(self, '_shown_points_ids', [])
        object.__setattr__(self, '_shown_points_coors', [])
        object.__setattr__(self, '_skeleton_points', [])
        
        if 'secv_path' in cui.files:
            keys = ['thickness', 'zoom', 'axis', 'scale_bar', 'points',
                    'dock', 'white_back', 'guide', 'sideview', 'center',
                    'window_size', 'shown_channels', 'point_focus']
        else:
            keys = ['zoom', 'scale_bar', 'dock', 'white_back', 'center',
                    'window_size', 'shown_channels', 'index']
        md = cui.display
        for k in list(md.keys()):
            if k not in keys:
                del md[k]
        for k in keys:
            if k not in md:
                md[k] = None
        for k in md:
            if md[k] is None:
                md[k] = self.defaults[k]
        if md['shown_channels'] is None:
            ch_show = tuple([True] * np.sum(cui.files['channel_nums']))
            md['shown_channels'] = ch_show
        super().__init__(md)
        for k in md:
            self[k] = md[k]
        
    def __setitem__(self, k, v):
        if k not in self:
            raise KeyError(k)
        if v is None:
            return
        if k == 'shown_channels':
            if len(v) != np.sum(self.cui.files['channel_nums']):
                raise ValueError("length of 'shown_channels' must be "
                                 "the same with channel number")
            v = tuple([bool(v[i]) for i in range(len(v))])
        elif k in ('center', 'window_size'):
            v = (int(v[0]), int(v[1]))
        elif k in ['thickness', 'point_focus']:
            v = int(v)
        elif k == 'zoom':
            v = float(v)
        elif k == 'index':
            v = int(v) % self.cui.files['shape'][0]
        else:
            v = bool(v)
        dict.__setitem__(self, k, v)
        
    def __str__(self):
        m = np.amax([len(k) for k in self]) + 1
        text = ''
        for k in self:
            text += ' '*(m - len(k)) + "'" + k + "': "
            text += str(self[k])
            text += ',\n'
        m = [len(str(self[k])) for k in self]
        m = np.amax(m) - m[-1] + 2
        text = '< Display >\n{' + text[1:-2] + ' '*m + '}\n'
        return text
    
    def getshown(self) -> np.ndarray:
        shown_ch = np.where(self['shown_channels'])[0].astype(int)
        return shown_ch
    
    def _issame(self, other):
        res = {}
        for k in self:
            if type(self[k]) == float:
                res[k] = abs(self[k] - other[k]) < 10**(-sf)
            else:
                res[k] = self[k] == other[k]
        return res
    
    def _format(self) -> dict:
        return dict(self)
        
        
class PositionArray(DataArray):
    def __new__(cls, cui):
        mp = cui.position
        if mp is None:
            mp = np.array([[0.,0.,0.], [0.,1.,0.], [0.,0.,1.]])
            mp /= cls._anisotropy
            mp[0] += np.array(cui.files['shape'])//2
        else:
            mp = np.float64(mp)
        self = np.asarray(mp, dtype=float).view(cls)
        assert self.shape == (3,3)
        return self
    
    def __init__(self, cui):
        object.__setattr__(self, 'cui', cui)
        
        sz, sy, sx = self.cui.files['shape']
        sz, sy, sx = sz - 1, sy - 1, sx - 1
        peaks = np.array([[ 0,  0, 0], [ 0,  0, sx], 
                          [ 0, sy, 0], [ 0, sy, sx],
                          [sz,  0, 0], [sz,  0, sx], 
                          [sz, sy, 0], [sz, sy, sx]], dtype=float)
        object.__setattr__(self, 'peaks', peaks)
        self._normalize()
        
    def __setitem__(self, k, v):
        v0 = self[k]
        np.ndarray.__setitem__(self, k, v)
        try:
            self._normalize()
        except RuntimeError as e:
            np.ndarray.__setitem__(self, k, v0)
            raise e
            
    def __str__(self):
        if self.shape != (3, 3):
            return super().__str__()
        pos = self.base
        text = pos.__repr__()
        text = text.split('\n')
        text = [text[i][6:-1] for i in range(3)]
        l = len(text[0])//3 - 1
        text[0] = text[0] + '   # center'
        text[1] = text[1] + '   # vertical'
        text[2] = text[2] + '  # horizontal'
        text = ['#  Z' + ' '*l + 'Y' + ' '*l + 'X' + ' '*l + '(px)'] + text
        text = '< Position >\n' + '\n'.join(text) + '\n'
        return text
            
    def reset(self):
        while self.shape != (3, 3):
            self = self.base
        mp = np.array([[0.,0.,0.], [0.,1.,0.], [0.,0.,1.]])
        mp /= self._anisotropy
        mp[0] += np.array(self.cui.files['shape'])//2
        self[:] = mp
        
    def shift(self, amount, axis):
        if axis not in (0, 1, 2):
            raise ValueError("'axis' has to be one of (0, 1, 2)")
        while self.shape != (3, 3):
            self = self.base
        op = self[0]
        nv = self.basis[axis]
        op[:] = op + nv * amount
        
    def rotate(self, angle, axis):
        while self.shape != (3, 3):
            self = self.base
        angle = angle / 180 * np.pi
        ny, nx = self[1:]
        if axis == 0:
            ny1 =  np.sin(angle) * nx + np.cos(angle) * ny
            nx1 =  np.cos(angle) * nx - np.sin(angle) * ny
            self[1:] = ny1, nx1
            return
        nz = self.basis[0]
        if axis == 1:
            nv = nx
        elif axis == 2:
            nv = ny
        else:
            raise ValueError("'axis' has to be one of (0, 1, 2)")
        nv[:] = np.cos(angle) * nv + np.sin(angle) * nz
        
    def _normalize(self):
        while self.shape != (3,3):
            self = self.base
            if self is None:
                raise RuntimeError("couldn't normalize axes in position")
        op, ny, nx = np.array(self)
        sz, sy, sx = self.cui.files['shape']
        nx *= self._anisotropy
        ny *= self._anisotropy
        nx /= np.linalg.norm(nx)
        ny = ny - nx * np.inner(ny, nx)
        ny /= np.linalg.norm(ny)
        nz = -np.cross(ny, nx)
        nx /= self._anisotropy
        ny /= self._anisotropy
        nz /= self._anisotropy
        basis = DataArray([nz, ny, nx])
        object.__setattr__(self, 'basis', basis)
        np.ndarray.__setitem__(self, slice(None), DataArray([op, ny, nx]))
        self._update_depth()
        
    def _update_depth(self):
        op, ny, nx = np.array(self)
        basis = self.basis
        exp_rate = self.cui.geometry['expansion_rate']
        iw, ih = self.cui.geometry['image_size']
        peaks = np.linalg.solve(basis.T / exp_rate, (self.peaks - op).T).T
        peaks[:,1:] += ih//2, iw//2
        iw, ih = iw - 1, ih - 1
        to, from_ = 0, 0
        mx = np.argmax(peaks[:, 0])
        mn = 7 - mx
        if 0 <= peaks[mx, 1] <= ih and 0 <= peaks[mx, 2] <= iw:
            to = peaks[mx, 0]
        if 0 <= peaks[mn, 1] <= ih and 0 <= peaks[mn, 2] <= iw:
            from_ = peaks[mn, 0]
        edges = peaks[[[0,1], [0,2], [0,4], [1,3], [1,5], [2,3], 
                       [2,6], [3,7], [4,5], [4,6], [5,7], [6,7]]]
        ts = np.array([[0, 0], [ih, iw]])[:,None] - edges[:, 1, 1:]
        n = edges[:, 0, 1:] - edges[:, 1, 1:]
        ts[:,n != 0] /= n[n != 0]
        ts[:,n == 0] = -1
        cand = np.where((0 <= ts) * (ts <= 1))
        ts = ts[cand[0], cand[1], cand[2], None]
        edges = edges[cand[1]]
        ps = edges[:, 0] * ts + edges[:, 1] * (1 - ts)
        a = ps[np.arange(len(ps)), 2 - cand[2]]
        a = (0 <= a) * (a <= np.array([iw, ih])[cand[2]])
        ps = ps[a, 0]
        if len(ps) > 0:
            to, from_ = max(to, np.amax(ps)), min(from_, np.amin(ps))
        faces = peaks[[[0,1,2], [0,1,4], [0,2,4], [1,3,5], [2,3,6], [4,5,6]]]
        A = np.array([
            [faces[:,1,1] - faces[:,0,1], faces[:,2,1] - faces[:,0,1]],
            [faces[:,1,2] - faces[:,0,2], faces[:,2,2] - faces[:,0,2]]
            ]).transpose(2, 0, 1)
        a = np.linalg.matrix_rank(A) == 2
        A, faces = A[a], faces[a]
        b = np.tile(-faces[:, 0, 1:, None], 4)
        b[:, 0, 2:] += ih
        b[:, 1, 1::2] += iw
        sts = np.linalg.solve(A, b)
        cand = np.where(np.prod((0 <= sts) * (sts <= 1), axis = 1, dtype = bool))
        sts = sts[cand[0], :, cand[1]]
        faces = faces[cand[0], :, 0]
        ps = faces[:, 0] * (1 - sts[:, 0] - sts[:, 1])
        ps += faces[:, 1] * sts[:, 0] + faces[:, 2] * sts[:, 1]
        if len(ps) > 0:
            to, from_ = max(to, np.amax(ps)), min(from_, np.amin(ps))
        from_ = min(0, int(from_ / exp_rate) + 10)
        to = max(0, int(to / exp_rate) - 9)
        object.__setattr__(self, 'depth_range', [from_, to])
        
    def _issame(self, other):
        res = np.linalg.norm(np.array(self) - np.array(other), axis = 1)
        res = res < 10**(-sf)
        return res.tolist()
    
    def _format(self) -> list:
        return self.tolist()
        
        
class ChannelList(FrozenList):
    def __init__(self, cui):
        object.__setattr__(self, 'cui', cui)
        self.generate(cui.channels)
                
    def __setitem__(self, i, o):
        if type(o) != Channel:
            o = Channel(o)
        list.__setitem__(self, i, o)
        
    def __str__(self):
        ch_nm = self.getnames()
        m = max([len(nm) for nm in ch_nm])
        text = '< Channels >\n'
        text += "# Name" + " "*m + " Color (BGR)      Vrange\n"
        ch_cl = self.getcolors()
        ch_vr = self.getvranges()
        text += "[['{0}'".format(ch_nm[0])
        text += " "*(m - len(ch_nm[0])) 
        text += ", [{0:>3}, {1:>3}, {2:>3}]".format(ch_cl[0][0], ch_cl[0][1], ch_cl[0][2])
        text += ", [{0:>5}, {1:>5}]]".format(ch_vr[0][0], ch_vr[0][1])
        for i in range(1, len(ch_nm)):
            text += ",\n ['{0}'".format(ch_nm[i])
            text += " "*(m - len(ch_nm[i])) 
            text += ", [{0:>3}, {1:>3}, {2:>3}]".format(ch_cl[i][0], ch_cl[i][1], ch_cl[i][2])
            text += ", [{0:>5}, {1:>5}]]".format(ch_vr[i][0], ch_vr[i][1])
        text += "]\n"
        return text
        
    def getnames(self) -> list:
        return [str(c[0]) for c in self]
    
    def getcolors(self, option: str = 'bgr') -> list:
        return [list(c[1][option]) for c in self]
    
    def getvranges(self) -> list:
        return [list(c[2]) for c in self]
    
    def getlut(self) -> np.ndarray:
        vrange = np.array(self.getvranges())
        lut = np.arange(65536)[None]
        diff = vrange[:,1] - vrange[:,0]
        lut = ((1 / diff[:,None]) * (lut - vrange[:,:1]))
        lut[lut < 0] = 0
        lut[lut > 1] = 1
        return lut
    
    def setname(self, channel_ids: Union[int, list], name: str):
        if not hasattr(channel_ids, '__iter__'):
            channel_ids = [channel_ids]
        for i in channel_ids:
            self[i][0] = name
    
    def setcolor(self, 
                  channel_ids: Union[int, list],
                  color: list,
                  as_hsl: bool = False):
        if not hasattr(channel_ids, '__iter__'):
            channel_ids = [channel_ids]
        key = 'hsl' if as_hsl else 'bgr'
        for i in channel_ids:
            self[i][1][key] = color
            
    def setvrange(self,
                   channel_ids: Union[int, list],
                   vmin: int = None,
                   vmax: int = None):
        if not hasattr(channel_ids, '__iter__'):
            channel_ids = [channel_ids]
        if vmin is not None:
            for i in channel_ids:
                self[i][2][0] = vmin
        if vmax is not None:
            for i in channel_ids:
                self[i][2][1] = vmax
                
    def auto_color(self, channel_ids: Union[int, list] = None):
        if channel_ids is None:
            channel_ids = list(range(len(self)))
        if not hasattr(channel_ids, '__iter__'):
            channel_ids = [channel_ids]
        auto_color(self, channel_ids)
        
    def copy(self):
        return [Channel(c) for c in self._format()]
    
    def generate(self, mc):
        cui = self.cui
        num = np.sum(cui.files['channel_nums'])
        if mc is None:
            mc = [None]*num
        elif len(mc) != num:
            mc = [None]*num
        for i in range(len(mc)):
            mc[i] = Channel(mc[i])
        super().__init__(mc)
        nn = 0
        for i in range(len(mc)):
            if mc[i][0] is None:
                while 'ch{0}'.format(nn) in self.getnames():
                    nn += 1
                mc[i][0] = 'ch{0}'.format(nn)
        news = [i for i in range(len(mc)) if mc[i][1] is None]
        if len(news) > 0:
            ids = [i for i in range(len(mc)) if mc[i][1] is None]
            self.auto_color(ids)
        if hasattr(cui, 'update') and 'secv_path' in cui.files:
            cui.update(level = 2, end = 3)
        if len(news) > 0:
            if hasattr(cui, 'view_frame') or hasattr(cui, 'stacks'):
                if hasattr(cui, 'view_frame'):
                    frame = cui.view_frame
                else:
                    frame = cui.stacks[cui.display['index']]
                new_frame = frame[news].reshape(len(news), -1)
                vmins = np.percentile(new_frame, 1, axis = 1)
                vmaxs = np.percentile(new_frame, 99, axis = 1)
                for i, n in enumerate(news):
                    self[n][2][0] = vmins[i]
                    self[n][2][1] = vmaxs[i]
    
    def _issame(self, other):
        if len(self) != len(other):
            return False
        res = []
        for i in range(len(self)):
            res += [self[i]._issame(other[i])]
        return res
    
    def _format(self) -> list:
        return [c._format() for c in self]
    
    
class PointList(FrozenList):
    def __init__(self, cui):
        object.__setattr__(self, 'cui', cui)
        mp = cui.points
        if mp is None:
            mp = []
        for i in range(len(mp)):
            mp[i] = Point(mp[i])
        super().__init__(mp)
        nn = 0
        for i in range(len(mp)):
            if mp[i][0] is None:
                while 'p{0}'.format(nn) in self.getnames():
                    nn += 1
                mp[i][0] = 'p{0}'.format(nn)
        ids = [i for i in range(len(mp)) if mp[i][1] is None]
        self.auto_color(ids)
        
    def __setitem__(self, i, o):
        if type(o) != Point:
            o = Point(o)
        list.__setitem__(self, i, o)
        
    def __delitem__(self, i):
        list.__delitem__(self, i)
        
    def __str__(self):
        text = '< Points >\n'
        if len(self) == 0:
            return text + "[]\n"
        pt_nm = self.getnames()
        pt_cl = self.getcolors()
        cr = str(np.array(self.getcoordinates()))
        cr = cr.split("\n")
        cr[-1] = cr[-1][:-1]
        l = (len(cr[0][1:]) - 4)//3 + 1
        cr = [cr[i][1:l+1] + "," + cr[i][l+1:2*l+1] + "," + cr[i][2*l+1:] for i in range(len(cr))]
        if len(cr) == len(self):
            m = max([len(nm) for nm in pt_nm])
            text += "# Name" + " "*m + " Color (BGR)      Coordinate (ZYX px)\n"
            text += "[['{0}'".format(pt_nm[0])
            text += " "*(m - len(pt_nm[0])) 
            text += ", [{0:>3}, {1:>3}, {2:>3}]".format(pt_cl[0][0], pt_cl[0][1], pt_cl[0][2])
            text += ", {0}]".format(cr[0])
            for i in range(1,len(pt_nm)):
                text += ",\n ['{0}'".format(pt_nm[i])
                text += " "*(m - len(pt_nm[i])) 
                text += ", [{0:>3}, {1:>3}, {2:>3}]".format(pt_cl[i][0], pt_cl[i][1], pt_cl[i][2])
                text += ", {0}]".format(cr[i])
            text += "]\n"
        else:
            pt_nm = pt_nm[:3] + ["..."] + pt_nm[-3:]
            m = max([len(nm) for nm in pt_nm])
            text += "# Name" + " "*m + " Color (BGR)      Coordinate (ZYX px)\n"
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
            text = text[:-1] + "]\n"
        return text
        
    def getnames(self) -> list:
        return [str(p[0]) for p in self]
    
    def getcolors(self, option: str = 'bgr') -> list:
        return [list(p[1][option]) for p in self]
    
    def getcoordinates(self) -> list:
        return [list(p[2]) for p in self]
    
    def coorsonimage(self) -> np.ndarray:
        cui = self.cui
        coors = np.array(self.getcoordinates())
        if len(coors) > 0:
            op = cui.position[0]
            n = cui.position.basis
            coors -= op
            coors = np.linalg.solve(n.T, coors.T).T
            coors *= cui.geometry['expansion_rate']
            lx, ly = cui.geometry['image_size']
            coors[:,1:] += np.array([ly//2, lx//2])
        return coors
    
    def add(self, 
            name: str = None, 
            color: list = None, 
            coordinate: list = None
            ):
        if coordinate is None:
            coordinate = self.cui.position[0]
        pt = Point([name, color, coordinate])
        list.append(self, pt)
        if name is None:
            nn = 0
            while 'p{0}'.format(nn) in self.getnames():
                nn += 1
            self[-1][0] = 'p{0}'.format(nn)
        if color is None:
            self.auto_color(len(self) - 1)
    
    def delete(self, point_ids: Union[int, list]):
        if not hasattr(point_ids, '__iter__'):
            point_ids = [point_ids]
        point_ids = np.sort(np.unique(point_ids))[::-1]
        for i in point_ids:
            del self[i]
            
    def setname(self, point_ids: Union[int, list], name: str):
        if not hasattr(point_ids, '__iter__'):
            point_ids = [point_ids]
        for i in point_ids:
            self[i][0] = name
            
    def setcolor(self, 
                  point_ids: Union[int, list],
                  color: list,
                  as_hsl: bool = False):
        if not hasattr(point_ids, '__iter__'):
            point_ids = [point_ids]
        key = 'hsl' if as_hsl else 'bgr'
        for i in point_ids:
            self[i][1][key] = color
            
    def setcoordinate(self,
                       point_ids: Union[int, list],
                       coordinate: list):
        if not hasattr(point_ids, '__iter__'):
            point_ids = [point_ids]
        for i in point_ids:
            self[i][2] = coordinate
    
    def auto_color(self, point_ids: Union[int, list] = None):
        if point_ids is None:
            point_ids = list(range(len(self)))
        if not hasattr(point_ids, '__iter__'):
            point_ids = [point_ids]
        auto_color(self, point_ids, offset = 180)
        
    def copy(self):
        return [Point(p) for p in self._format()]
    
    def _issame(self, other):
        if len(self) != len(other):
            return False
        res = []
        for i in range(len(self)):
            res += [self[i]._issame(other[i])]
        return res
    
    def _format(self) -> list:
        return [p._format() for p in self]


class SnapshotList(FrozenList):
    def __init__(self, cui):
        object.__setattr__(self, 'cui', cui)
        ms = cui.snapshots
        for i in range(len(ms)):
            ms[i] = Snapshot(ms[i])
        super().__init__(ms)
        nn = 0
        for i in range(len(ms)):
            if ms[i]['name'] is None:
                while 'ss{0}'.format(nn) in self.getnames():
                    nn += 1
                ms[i]['name'] = 'ss{0}'.format(nn)
    
    def __setitem__(self, i, o):
        if type(o) != Snapshot:
            o = Snapshot(o)
        list.__setitem__(self, i, o)
    
    def __delitem__(self, i):
        list.__delitem__(self, i)
        
    def __str__(self):
        return '< Snapshots >\n' + str(self.getnames()) + '\n'
        
    def getnames(self) -> list:
        return [s['name'] for s in self]
    
    def getpreview(self, 
                   snapshot_id: int, 
                   size: tuple = None):
        meta = self.cui.metadata._format()
        ss = self[snapshot_id]._format()
        meta['geometry'] = ss['geometry']
        meta['position'] = ss['position']
        meta['points'] = ss['points']
        if meta['files']['paths'] == ss['files']['paths']:            
            meta['channels'] = ss['channels']
        else:
            sep = [0] + list(np.cumsum(ss['files']['channel_nums']))
            sep = sep[::-1]
            chs = ss['channels']
            for i, p in enumerate(ss.files['paths'][::-1]):
                if p not in meta.files['paths']:
                    del chs[sep[i + 1]: sep[i]]
            meta['channels'] = chs
        
        iw, ih = meta['geometry']['image_size']
        if size is None:
            iw1, ih1 = iw, ih
        else:
            iw1, ih1 = size
        gain = min(iw1/iw, ih1/ih)
        exp_rate = meta['geometry']['expansion_rate']
        meta['geometry']['expansion_rate'] = exp_rate * gain
        meta['geometry']['image_size'] = (int(iw * gain), int(ih * gain))
        meta['display']['scale_bar'] = False
        meta['display']['guide'] = True
        meta['display']['sideview'] = False
        meta['display']['window_size'] = None
        
        secv = self.cui.copy(metadata = meta)
        view_image = secv.view_image
        skeleton_image = secv.skeleton_image
        if size is not None:
            ih, iw = skeleton_image.shape[:2]
            gain = min(iw1/iw, ih1/ih)
            shift = (iw1 - iw*gain)/2, (ih1 - ih*gain)/2
            M = np.array([[gain, 0, shift[0]], [0, gain, shift[1]]], dtype = float)
            skeleton_image = cv2.warpAffine(skeleton_image, M, (iw1, ih1),
                                            borderMode = cv2.BORDER_CONSTANT, 
                                            borderValue = (240, 240, 240))
        
        return view_image, skeleton_image
    
    def copy(self):
        return [Snapshot(s) for s in self._format()]
    
    def snap(self):
        new = Snapshot(self.cui.metadata._format())
        list.append(self, new)
        if new['name'] is None:
            nn = 0
            while 'ss{0}'.format(nn) in self.getnames():
                nn += 1
            self[-1]['name'] = 'ss{0}'.format(nn)
            
    def delete(self, snapshot_ids: Union[int, list]):
        if not hasattr(snapshot_ids, '__iter__'):
            snapshot_ids = [snapshot_ids]
        snapshot_ids = np.sort(np.unique(snapshot_ids))[::-1]
        for i in snapshot_ids:
            del self[i]
            
    def overwrite(self, i: int, 
                  pos_on: bool = True,
                  chs_on: bool = True,
                  pts_on: bool = True):
        cui = self.cui
        
        meta = cui.metadata._format()
        new = self[i]._format()
        
        if pos_on:
            new['geometry'] = meta['geometry']
            new['position'] = meta['position']
        if chs_on:
            new['files'] = meta['files']
            new['channels'] = meta['channels']
        if pts_on:
            new['points'] = meta['points']
            
        self[i] = new
            
    def restore(self, i: int, 
                pos_on: bool = True,
                chs_on: bool = True,
                pts_on: bool = True):
        cui = self.cui
        new = cui.metadata._format()
        ss = self[i]._format()
        
        if pos_on:
            new['geometry'] = ss['geometry']
            new['position'] = ss['position']
        if chs_on:
            new['files'] = ss['files']
            new['channels'] = ss['channels']
        if pts_on:
            new['points'] = ss['points']
        cui.metadata = new
        
    def setname(self, snapshot_ids: Union[int, list], name: str):
        if not hasattr(snapshot_ids, '__iter__'):
            snapshot_ids = [snapshot_ids]
        for i in snapshot_ids:
            self[i]['name'] = name
    
    def _issame(self, other):
        if len(self) != len(other):
            return False
        res = []
        for i in range(len(self)):
            res += [self[i]._issame(other[i])]
        return res
    
    def _format(self) -> list:
        return [s._format() for s in self]
        
                
                
