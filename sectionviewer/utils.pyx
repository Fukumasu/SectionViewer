import cython
# from cython.parallel import prange
from libc.stdlib cimport rand, RAND_MAX
import numpy as np
cimport numpy as cnp

ctypedef cnp.uint16_t DTYPE_t
ctypedef cnp.float_t DTYPE_t2
ctypedef cnp.int64_t DTYPE_t3
ctypedef cnp.uint8_t DTYPE_t4
        
        
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef calc_exist(cnp.ndarray[DTYPE_t2, ndim=2] pos, cnp.ndarray[DTYPE_t3, ndim=1] c,
                   int dz, int dy, int dx, int m, int n):
    cdef int i, j, s, e
    cdef float z0, y0, x0, z, y, x, za, ya, xa, zb, yb, xb, zc, yc, xc
    cdef int i0 = 0
    cdef int i1 = m
    
    if pos[2,0] > 0:
        za = -pos[0,0]/pos[2,0] + c[1] + 1
        zb = -pos[1,0]/pos[2,0]
        zc = dz/pos[2,0] - 1 + za
    elif pos[2,0] < 0:
        za = dz/pos[2,0] - pos[0,0]/pos[2,0] + c[1] + 1
        zb = -pos[1,0]/pos[2,0]
        zc = -dz/pos[2,0] - 1 + za
    else:
        za = 0
        zb = 0
        zc = n
        if pos[1,0] > 0:
            i0 = min(max(i0, int(c[0] - pos[0,0]/pos[1,0] + 1)), m)
            i1 = max(min(i1, int(c[0] + (dz - pos[0,0])/pos[1,0])), i0)
            z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            while i0 < i1 and z0 // dz != 0:
                i0 += 1
                z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            while i1 > i0 and z0 // dz != 0:
                i1 -= 1
                z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            if i0 == i1:
                return False
        elif pos[1,0] < 0:
            i0 = min(max(i0, int(c[0] + (dz - pos[0,0])/pos[1,0] + 1)), m)
            i1 = max(min(i1, int(c[0] - pos[0,0]/pos[1,0])), i0)
            z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            while i0 < i1 and z0 // dz != 0:
                i0 += 1
                z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            while i1 > i0 and z0 // dz != 0:
                i1 -= 1
                z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            if i0 == i1:
                return False
        elif pos[0,0] < 0 or pos[0,0] >= dz:
            return False
    if pos[2,1] > 0:
        ya = -pos[0,1]/pos[2,1] + c[1] + 1
        yb = -pos[1,1]/pos[2,1]
        yc = dy/pos[2,1] - 1 + ya
    elif pos[2,1] < 0:
        ya = dy/pos[2,1] - pos[0,1]/pos[2,1]+ c[1] + 1
        yb = -pos[1,1]/pos[2,1]
        yc = -dy/pos[2,1] - 1 + ya
    else:
        ya = 0
        yb = 0
        yc = n
        if pos[1,1] > 0:
            i0 = min(max(i0, int(c[0] - pos[0,1]/pos[1,1] + 1)), m)
            i1 = max(min(i1, int(c[0] + (dy - pos[0,1])/pos[1,1])), i0)
            y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            while i0 < i1 and y0 // dy != 0:
                i0 += 1
                y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            while i1 > i0 and y0 // dy != 0:
                i1 -= 1
                y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            if i0 == i1:
                return False
        elif pos[1,1] < 0:
            i0 = min(max(i0, int(c[0] + (dy - pos[0,1])/pos[1,1] + 1)), m)
            i1 = max(min(i1, int(c[0] - pos[0,1]/pos[1,1])), i0)
            y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            while i0 < i1 and y0 // dy != 0:
                i0 += 1
                y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            while i1 > i0 and y0 // dy != 0:
                i1 -= 1
                y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            if i0 == i1:
                return False
        elif pos[0,1] < 0 or pos[0,1] >= dy:
            return False
    if pos[2,2] > 0:
        xa = -pos[0,2]/pos[2,2] + c[1] + 1
        xb = -pos[1,2]/pos[2,2]
        xc = dx/pos[2,2] - 1 + xa
    elif pos[2,2] < 0:
        xa = dx/pos[2,2] - pos[0,2]/pos[2,2] + c[1] + 1
        xb = -pos[1,2]/pos[2,2]
        xc = -dx/pos[2,2] - 1 + xa
    else:
        xa = 0
        xb = 0
        xc = n
        if pos[1,2] > 0:
            i0 = min(max(i0, int(c[0] - pos[0,2]/pos[1,2] + 1)), m)
            i1 = max(min(i1, int(c[0] + (dx - pos[0,2])/pos[1,2])), i0)
            x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            while i0 < i1 and x0 // dx != 0:
                i0 += 1
                x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            while i1 > i0 and x0 // dx != 0:
                i1 -= 1
                x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            if i0 == i1:
                return False
        elif pos[1,2] < 0:
            i0 = min(max(i0, int(c[0] + (dx - pos[0,2])/pos[1,2] + 1)), m)
            i1 = max(min(i1, int(c[0] - pos[0,2]/pos[1,2])), i0)
            x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            while i0 < i1 and x0 // dx != 0:
                i0 += 1
                x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            while i1 > i0 and x0 // dx != 0:
                i1 -= 1
                x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            if i0 == i1:
                return False
        elif pos[0,2] < 0 or pos[0,2] >= dx:
            return False
    
    for i in range(i0, i1):
        j = i - c[0]
        z0 = pos[0,0] + j*pos[1,0]
        y0 = pos[0,1] + j*pos[1,1]
        x0 = pos[0,2] + j*pos[1,2]
        
        s = int(min(max(za + zb*j, ya + yb*j, xa + xb*j, 0), n))
        e = int(max(min(zc + zb*j, yc + yb*j, xc + xb*j, n), s))
        
        if s == e:
            continue
        
        x = s - c[1]
        z = z0 + x*pos[2,0]
        y = y0 + x*pos[2,1]
        x = x0 + x*pos[2,2]
        while s < e and (z//dz!=0 or y//dy!=0 or x//dx!=0):
            s = s + 1
            x = s - c[1]
            z = z0 + x*pos[2,0]
            y = y0 + x*pos[2,1]
            x = x0 + x*pos[2,2]
            
        x = e - c[1] - 1
        z = z0 + x*pos[2,0]
        y = y0 + x*pos[2,1]
        x = x0 + x*pos[2,2]
        while e > s and (z//dz!=0 or y//dy!=0 or x//dx!=0):
            e = e - 1
            x = e - c[1] - 1
            z = z0 + x*pos[2,0]
            y = y0 + x*pos[2,1]
            x = x0 + x*pos[2,2]
        
        if s == e:
            continue
        return True


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef calc_section(cnp.ndarray[DTYPE_t, ndim=4] box, cnp.ndarray[DTYPE_t2, ndim=2] pos,
                   cnp.ndarray[DTYPE_t, ndim=3] res, cnp.ndarray[DTYPE_t3, ndim=1] c,
                   cnp.ndarray[DTYPE_t3, ndim=1] ch_show):
    cdef int i, j, k, l, zg1, yg1, xg1, zg2, yg2, xg2, s, e
    cdef float z0, y0, x0, z, y, x, zd1, yd1, xd1, zd2, yd2, xd2
    cdef float za, ya, xa, zb, yb, xb, zc, yc, xc
    cdef bint exist = False
    cdef int dc = box.shape[0]
    cdef int dz = box.shape[1] - 1
    cdef int dy = box.shape[2] - 1
    cdef int dx = box.shape[3] - 1
    cdef int m = res.shape[1]
    cdef int n = res.shape[2]
    
    cdef int i0 = 0
    cdef int i1 = m
    
    cdef int chs = len(ch_show)
    
    if pos[2,0] > 0:
        za = -pos[0,0]/pos[2,0] + c[1] + 1
        zb = -pos[1,0]/pos[2,0]
        zc = dz/pos[2,0] - 1 + za
    elif pos[2,0] < 0:
        za = dz/pos[2,0] - pos[0,0]/pos[2,0] + c[1] + 1
        zb = -pos[1,0]/pos[2,0]
        zc = -dz/pos[2,0] - 1 + za
    else:
        za = 0
        zb = 0
        zc = n
        if pos[1,0] > 0:
            i0 = min(max(i0, int(c[0] - pos[0,0]/pos[1,0] + 1)), m)
            i1 = max(min(i1, int(c[0] + (dz - pos[0,0])/pos[1,0])), i0)
            z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            while i0 < i1 and z0 // dz != 0:
                i0 += 1
                z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            while i1 > i0 and z0 // dz != 0:
                i1 -= 1
                z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            if i0 == i1:
                # for i in prange(m, nogil=True):
                for i in range(m):
                    for j in range(n):
                        for k in range(dc):
                            res[k,i,j] = 0
                return False
        elif pos[1,0] < 0:
            i0 = min(max(i0, int(c[0] + (dz - pos[0,0])/pos[1,0] + 1)), m)
            i1 = max(min(i1, int(c[0] - pos[0,0]/pos[1,0])), i0)
            z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            while i0 < i1 and z0 // dz != 0:
                i0 += 1
                z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            while i1 > i0 and z0 // dz != 0:
                i1 -= 1
                z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            if i0 == i1:
                # for i in prange(m, nogil=True):
                for i in range(m):
                    for j in range(n):
                        for k in range(dc):
                            res[k,i,j] = 0
                return False
        elif pos[0,0] < 0 or pos[0,0] >= dz:
            # for i in prange(m, nogil=True):
            for i in range(m):
                for j in range(n):
                    for k in range(dc):
                        res[k,i,j] = 0
            return False
    if pos[2,1] > 0:
        ya = -pos[0,1]/pos[2,1] + c[1] + 1
        yb = -pos[1,1]/pos[2,1]
        yc = dy/pos[2,1] - 1 + ya
    elif pos[2,1] < 0:
        ya = dy/pos[2,1] - pos[0,1]/pos[2,1]+ c[1] + 1
        yb = -pos[1,1]/pos[2,1]
        yc = -dy/pos[2,1] - 1 + ya
    else:
        ya = 0
        yb = 0
        yc = n
        if pos[1,1] > 0:
            i0 = min(max(i0, int(c[0] - pos[0,1]/pos[1,1] + 1)), m)
            i1 = max(min(i1, int(c[0] + (dy - pos[0,1])/pos[1,1])), i0)
            y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            while i0 < i1 and y0 // dy != 0:
                i0 += 1
                y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            while i1 > i0 and y0 // dy != 0:
                i1 -= 1
                y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            if i0 == i1:
                # for i in prange(m, nogil=True):
                for i in range(m):
                    for j in range(n):
                        for k in range(dc):
                            res[k,i,j] = 0
                return False
        elif pos[1,1] < 0:
            i0 = min(max(i0, int(c[0] + (dy - pos[0,1])/pos[1,1] + 1)), m)
            i1 = max(min(i1, int(c[0] - pos[0,1]/pos[1,1])), i0)
            y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            while i0 < i1 and y0 // dy != 0:
                i0 += 1
                y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            while i1 > i0 and y0 // dy != 0:
                i1 -= 1
                y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            if i0 == i1:
                # for i in prange(m, nogil=True):
                for i in range(m):
                    for j in range(n):
                        for k in range(dc):
                            res[k,i,j] = 0
                return False
        elif pos[0,1] < 0 or pos[0,1] >= dy:
            # for i in prange(m, nogil=True):
            for i in range(m):
                for j in range(n):
                    for k in range(dc):
                        res[k,i,j] = 0
            return False
    if pos[2,2] > 0:
        xa = -pos[0,2]/pos[2,2] + c[1] + 1
        xb = -pos[1,2]/pos[2,2]
        xc = dx/pos[2,2] - 1 + xa
    elif pos[2,2] < 0:
        xa = dx/pos[2,2] - pos[0,2]/pos[2,2] + c[1] + 1
        xb = -pos[1,2]/pos[2,2]
        xc = -dx/pos[2,2] - 1 + xa
    else:
        xa = 0
        xb = 0
        xc = n
        if pos[1,2] > 0:
            i0 = min(max(i0, int(c[0] - pos[0,2]/pos[1,2] + 1)), m)
            i1 = max(min(i1, int(c[0] + (dx - pos[0,2])/pos[1,2])), i0)
            x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            while i0 < i1 and x0 // dx != 0:
                i0 += 1
                x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            while i1 > i0 and x0 // dx != 0:
                i1 -= 1
                x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            if i0 == i1:
                # for i in prange(m, nogil=True):
                for i in range(m):
                    for j in range(n):
                        for k in range(dc):
                            res[k,i,j] = 0
                return False
        elif pos[1,2] < 0:
            i0 = min(max(i0, int(c[0] + (dx - pos[0,2])/pos[1,2] + 1)), m)
            i1 = max(min(i1, int(c[0] - pos[0,2]/pos[1,2])), i0)
            x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            while i0 < i1 and x0 // dx != 0:
                i0 += 1
                x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            while i1 > i0 and x0 // dx != 0:
                i1 -= 1
                x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            if i0 == i1:
                # for i in prange(m, nogil=True):
                for i in range(m):
                    for j in range(n):
                        for k in range(dc):
                            res[k,i,j] = 0
                return False
        elif pos[0,2] < 0 or pos[0,2] >= dx:
            # for i in prange(m, nogil=True):
            for i in range(m):
                for j in range(n):
                    for k in range(dc):
                        res[k,i,j] = 0
            return False
        
    # for i in prange(i0, nogil=True):
    for i in range(i0):
        for j in range(n):
            for k in range(dc):
                res[k,i,j] = 0
    # for i in prange(i1, m, nogil=True):
    for i in range(i1, m):
        for j in range(n):
            for k in range(dc):
                res[k,i,j] = 0
    
    # for i in prange(i0, i1, nogil=True):
    for i in range(i0, i1):
        m = i - c[0]
        z0 = pos[0,0] + m*pos[1,0]
        y0 = pos[0,1] + m*pos[1,1]
        x0 = pos[0,2] + m*pos[1,2]
        
        s = int(min(max(za + zb*m, ya + yb*m, xa + xb*m, 0), n))
        e = int(max(min(zc + zb*m, yc + yb*m, xc + xb*m, n), s))
        
        if s == e:
            for j in range(n):
                for k in range(dc):
                    res[k,i,j] = 0
            continue
        
        x = s - c[1]
        z = z0 + x*pos[2,0]
        y = y0 + x*pos[2,1]
        x = x0 + x*pos[2,2]
        while s < e and (z//dz!=0 or y//dy!=0 or x//dx!=0):
            s = s + 1
            x = s - c[1]
            z = z0 + x*pos[2,0]
            y = y0 + x*pos[2,1]
            x = x0 + x*pos[2,2]
            
        x = e - c[1] - 1
        z = z0 + x*pos[2,0]
        y = y0 + x*pos[2,1]
        x = x0 + x*pos[2,2]
        while e > s and (z//dz!=0 or y//dy!=0 or x//dx!=0):
            e = e - 1
            x = e - c[1] - 1
            z = z0 + x*pos[2,0]
            y = y0 + x*pos[2,1]
            x = x0 + x*pos[2,2]
        
        if s == e:
            for j in range(n):
                for k in range(dc):
                    res[k,i,j] = 0
            continue
        exist += True
        
        for j in range(int(s)):
            for k in range(dc):
                res[k,i,j] = 0
        for j in range(int(e),n):
            for k in range(dc):
                res[k,i,j] = 0
                    
        for j in range(s, e):
            x = j - c[1]
            z = z0 + x*pos[2,0]
            y = y0 + x*pos[2,1]
            x = x0 + x*pos[2,2]
            zg1 = int(z)
            yg1 = int(y)
            xg1 = int(x)
            zg2 = zg1 + 1
            yg2 = yg1 + 1
            xg2 = xg1 + 1
            zd1 = z%1
            yd1 = y%1
            xd1 = x%1
            zd2 = 1.- zd1
            yd2 = 1.- yd1
            xd2 = 1.- xd1
            
            for k in range(chs):
                l = ch_show[k]
                res[l,i,j] = int(((box[l, zg1, yg1, xg1]*xd2 +\
                                   box[l, zg1, yg1, xg2]*xd1)*yd2 + \
                                  (box[l, zg1, yg2, xg1]*xd2 + \
                                   box[l, zg1, yg2, xg2]*xd1)*yd1)*zd2 + \
                                 ((box[l, zg2, yg1, xg1]*xd2 +\
                                   box[l, zg2, yg1, xg2]*xd1)*yd2 + \
                                  (box[l, zg2, yg2, xg1]*xd2 + \
                                   box[l, zg2, yg2, xg2]*xd1)*yd1)*zd1)
    return exist


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef fast_section(cnp.ndarray[DTYPE_t, ndim=4] box, cnp.ndarray[DTYPE_t2, ndim=2] pos,
                   cnp.ndarray[DTYPE_t, ndim=3] res, cnp.ndarray[DTYPE_t3, ndim=1] c,
                   cnp.ndarray[DTYPE_t3, ndim=1] ch_show):
    cdef int i, j, k, l, zg1, yg1, xg1, s, e
    cdef float z0, y0, x0, z, y, x
    cdef float za, ya, xa, zb, yb, xb, zc, yc, xc
    cdef bint exist = False
    cdef int dc = box.shape[0]
    cdef int dz = box.shape[1] - 1
    cdef int dy = box.shape[2] - 1
    cdef int dx = box.shape[3] - 1
    cdef int m = res.shape[1]
    cdef int n = res.shape[2]
    
    cdef int i0 = 0
    cdef int i1 = m
    
    cdef int chs = len(ch_show)
    
    if pos[2,0] > 0:
        za = -pos[0,0]/pos[2,0] + c[1] + 1
        zb = -pos[1,0]/pos[2,0]
        zc = dz/pos[2,0] - 1 + za
    elif pos[2,0] < 0:
        za = dz/pos[2,0] - pos[0,0]/pos[2,0] + c[1] + 1
        zb = -pos[1,0]/pos[2,0]
        zc = -dz/pos[2,0] - 1 + za
    else:
        za = 0
        zb = 0
        zc = n
        if pos[1,0] > 0:
            i0 = min(max(i0, int(c[0] - pos[0,0]/pos[1,0] + 1)), m)
            i1 = max(min(i1, int(c[0] + (dz - pos[0,0])/pos[1,0])), i0)
            z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            while i0 < i1 and z0 // dz != 0:
                i0 += 1
                z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            while i1 > i0 and z0 // dz != 0:
                i1 -= 1
                z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            if i0 == i1:
                # for i in prange(m, nogil=True):
                for i in range(m):
                    for j in range(n):
                        for k in range(dc):
                            res[k,i,j] = 0
                return False
        elif pos[1,0] < 0:
            i0 = min(max(i0, int(c[0] + (dz - pos[0,0])/pos[1,0] + 1)), m)
            i1 = max(min(i1, int(c[0] - pos[0,0]/pos[1,0])), i0)
            z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            while i0 < i1 and z0 // dz != 0:
                i0 += 1
                z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            while i1 > i0 and z0 // dz != 0:
                i1 -= 1
                z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            if i0 == i1:
                # for i in prange(m, nogil=True):
                for i in range(m):
                    for j in range(n):
                        for k in range(dc):
                            res[k,i,j] = 0
                return False
        elif pos[0,0] < 0 or pos[0,0] >= dz:
            # for i in prange(m, nogil=True):
            for i in range(m):
                for j in range(n):
                    for k in range(dc):
                        res[k,i,j] = 0
            return False
    if pos[2,1] > 0:
        ya = -pos[0,1]/pos[2,1] + c[1] + 1
        yb = -pos[1,1]/pos[2,1]
        yc = dy/pos[2,1] - 1 + ya
    elif pos[2,1] < 0:
        ya = dy/pos[2,1] - pos[0,1]/pos[2,1]+ c[1] + 1
        yb = -pos[1,1]/pos[2,1]
        yc = -dy/pos[2,1] - 1 + ya
    else:
        ya = 0
        yb = 0
        yc = n
        if pos[1,1] > 0:
            i0 = min(max(i0, int(c[0] - pos[0,1]/pos[1,1] + 1)), m)
            i1 = max(min(i1, int(c[0] + (dy - pos[0,1])/pos[1,1])), i0)
            y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            while i0 < i1 and y0 // dy != 0:
                i0 += 1
                y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            while i1 > i0 and y0 // dy != 0:
                i1 -= 1
                y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            if i0 == i1:
                # for i in prange(m, nogil=True):
                for i in range(m):
                    for j in range(n):
                        for k in range(dc):
                            res[k,i,j] = 0
                return False
        elif pos[1,1] < 0:
            i0 = min(max(i0, int(c[0] + (dy - pos[0,1])/pos[1,1] + 1)), m)
            i1 = max(min(i1, int(c[0] - pos[0,1]/pos[1,1])), i0)
            y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            while i0 < i1 and y0 // dy != 0:
                i0 += 1
                y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            while i1 > i0 and y0 // dy != 0:
                i1 -= 1
                y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            if i0 == i1:
                # for i in prange(m, nogil=True):
                for i in range(m):
                    for j in range(n):
                        for k in range(dc):
                            res[k,i,j] = 0
                return False
        elif pos[0,1] < 0 or pos[0,1] >= dy:
            # for i in prange(m, nogil=True):
            for i in range(m):
                for j in range(n):
                    for k in range(dc):
                        res[k,i,j] = 0
            return False
    if pos[2,2] > 0:
        xa = -pos[0,2]/pos[2,2] + c[1] + 1
        xb = -pos[1,2]/pos[2,2]
        xc = dx/pos[2,2] - 1 + xa
    elif pos[2,2] < 0:
        xa = dx/pos[2,2] - pos[0,2]/pos[2,2] + c[1] + 1
        xb = -pos[1,2]/pos[2,2]
        xc = -dx/pos[2,2] - 1 + xa
    else:
        xa = 0
        xb = 0
        xc = n
        if pos[1,2] > 0:
            i0 = min(max(i0, int(c[0] - pos[0,2]/pos[1,2] + 1)), m)
            i1 = max(min(i1, int(c[0] + (dx - pos[0,2])/pos[1,2])), i0)
            x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            while i0 < i1 and x0 // dx != 0:
                i0 += 1
                x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            while i1 > i0 and x0 // dx != 0:
                i1 -= 1
                x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            if i0 == i1:
                # for i in prange(m, nogil=True):
                for i in range(m):
                    for j in range(n):
                        for k in range(dc):
                            res[k,i,j] = 0
                return False
        elif pos[1,2] < 0:
            i0 = min(max(i0, int(c[0] + (dx - pos[0,2])/pos[1,2] + 1)), m)
            i1 = max(min(i1, int(c[0] - pos[0,2]/pos[1,2])), i0)
            x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            while i0 < i1 and x0 // dx != 0:
                i0 += 1
                x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            while i1 > i0 and x0 // dx != 0:
                i1 -= 1
                x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            if i0 == i1:
                # for i in prange(m, nogil=True):
                for i in range(m):
                    for j in range(n):
                        for k in range(dc):
                            res[k,i,j] = 0
                return False
        elif pos[0,2] < 0 or pos[0,2] >= dx:
            # for i in prange(m, nogil=True):
            for i in range(m):
                for j in range(n):
                    for k in range(dc):
                        res[k,i,j] = 0
            return False
        
    # for i in prange(i0, nogil=True):
    for i in range(i0):
        for j in range(n):
            for k in range(dc):
                res[k,i,j] = 0
    # for i in prange(i1, m, nogil=True):
    for i in range(i1, m):
        for j in range(n):
            for k in range(dc):
                res[k,i,j] = 0
    
    # for i in prange(i0, i1, nogil=True):
    for i in range(i0, i1):
        m = i - c[0]
        z0 = pos[0,0] + m*pos[1,0]
        y0 = pos[0,1] + m*pos[1,1]
        x0 = pos[0,2] + m*pos[1,2]
        
        s = int(min(max(za + zb*m, ya + yb*m, xa + xb*m, 0), n))
        e = int(max(min(zc + zb*m, yc + yb*m, xc + xb*m, n), s))
        
        if s == e:
            for j in range(n):
                for k in range(dc):
                    res[k,i,j] = 0
            continue
        
        x = s - c[1]
        z = z0 + x*pos[2,0]
        y = y0 + x*pos[2,1]
        x = x0 + x*pos[2,2]
        while s < e and (z//dz!=0 or y//dy!=0 or x//dx!=0):
            s = s + 1
            x = s - c[1]
            z = z0 + x*pos[2,0]
            y = y0 + x*pos[2,1]
            x = x0 + x*pos[2,2]
            
        x = e - c[1] - 1
        z = z0 + x*pos[2,0]
        y = y0 + x*pos[2,1]
        x = x0 + x*pos[2,2]
        while e > s and (z//dz!=0 or y//dy!=0 or x//dx!=0):
            e = e - 1
            x = e - c[1] - 1
            z = z0 + x*pos[2,0]
            y = y0 + x*pos[2,1]
            x = x0 + x*pos[2,2]
        
        if s == e:
            for j in range(n):
                for k in range(dc):
                    res[k,i,j] = 0
            continue
        exist += True
        
        for j in range(int(s)):
            for k in range(chs):
                res[ch_show[k],i,j] = 0
        for j in range(int(e),n):
            for k in range(chs):
                res[ch_show[k],i,j] = 0
                    
        for j in range(s, e):
            x = j - c[1]
            z = z0 + x*pos[2,0]
            y = y0 + x*pos[2,1]
            x = x0 + x*pos[2,2]
            zg1 = int(z)
            yg1 = int(y)
            xg1 = int(x)
            
            for k in range(chs):
                l = ch_show[k]
                res[l,i,j] = box[l, zg1, yg1, xg1]
    return exist


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef fill_box(cnp.ndarray[DTYPE_t, ndim=4] box, cnp.ndarray[DTYPE_t2, ndim=2] pos,
               cnp.ndarray[DTYPE_t2, ndim=1] v, int start, int stop,
               cnp.ndarray[DTYPE_t, ndim=4] res, cnp.ndarray[DTYPE_t3, ndim=1] c):
    cdef cnp.ndarray[DTYPE_t3, ndim=1] ch_show = np.arange(len(box))
    for a in range(stop-start+1):
        pos1 = pos.copy()
        pos1[0,0] = pos1[0,0] + v[0]*(a+start)
        pos1[0,1] = pos1[0,1] + v[1]*(a+start)
        pos1[0,2] = pos1[0,2] + v[2]*(a+start)
        calc_section(box, pos1, res[:,-a-1], c, ch_show)


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef stack_section(cnp.ndarray[DTYPE_t, ndim=4] box, cnp.ndarray[DTYPE_t2, ndim=2] pos,
                    cnp.ndarray[DTYPE_t2, ndim=1] v, int start, int stop,
                    cnp.ndarray[DTYPE_t, ndim=3] res, cnp.ndarray[DTYPE_t3, ndim=1] c,
                    cnp.ndarray[DTYPE_t3, ndim=1] ch_show):
    cdef int i, j, k, l, zg1, yg1, xg1, zg2, yg2, xg2, r, j0, j1, k0, k1
    cdef float z0, y0, x0, z1, y1, x1, z, y, x, zd1, yd1, xd1, zd2, yd2, xd2, s, t
    cdef float za, ya, xa, zb, yb, xb, zc, yc, xc, zd, yd, xd, ze, ye, xe, zf, yf, xf, zg, yg, xg
    cdef bint exist = False
    cdef int dc = box.shape[0]
    cdef int dz = box.shape[1] - 1
    cdef int dy = box.shape[2] - 1
    cdef int dx = box.shape[3] - 1
    cdef int m = res.shape[1]
    cdef int n = res.shape[2]
    
    cdef int i0 = 0
    cdef int i1 = m
    
    cdef int chs = len(ch_show)
    
    # for i in prange(m, nogil=True):
    for i in range(m):
        for j in range(n):
            for l in range(chs):
                res[ch_show[l],i,j] = 0
    
    za, zb, zc, zd = start, 0., 0., stop
    ze, zf, zg = 0., 0., n
    if v[0] > 0:
        za = -pos[0,0]/v[0] + 1
        zb = -pos[1,0]/v[0]
        zc = -pos[2,0]/v[0]
        zd = (dz - pos[0,0])/v[0]
    elif v[0] < 0:
        za = (dz - pos[0,0])/v[0] + 1
        zb = -pos[1,0]/v[0]
        zc = -pos[2,0]/v[0]
        zd = -pos[0,0]/v[0]
    else:
        if pos[2,0] > 0:
            ze = -pos[0,0]/pos[2,0] + c[1] + 1
            zf = -pos[1,0]/pos[2,0]
            zg = (dz - pos[0,0])/pos[2,0] + c[1]
        elif pos[2,0] < 0:
            ze = (dz - pos[0,0])/pos[2,0] + c[1] + 1
            zf = -pos[1,0]/pos[2,0]
            zg = -pos[0,0]/pos[2,0] + c[1]
        else:
            if pos[1,0] > 0:
                i0 = int(min(max(-pos[0,0]/pos[1,0] + c[0] + 1, 0), m))
                i1 = int(max(min((dz - pos[0,0])/pos[1,0] + c[0], m), i0))
            else:
                i0 = int(min(max((dz - pos[0,0])/pos[1,0] + c[0] + 1, 0), m))
                i1 = int(max(min(-pos[0,0]/pos[1,0] + c[0], m), i0))
            z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            while i0 < i1 and z0 // dz != 0:
                i0 += 1
                z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            while i1 > i0 and z0 // dz != 0:
                i1 -= 1
                z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            if i0 == i1:
                return False
            
    ya, yb, yc, yd = start, 0., 0., stop
    ye, yf, yg = 0., 0., n
    if v[1] > 0:
        ya = -pos[0,1]/v[1] + 1
        yb = -pos[1,1]/v[1]
        yc = -pos[2,1]/v[1]
        yd = (dy - pos[0,1])/v[1]
    elif v[1] < 0:
        ya = (dy - pos[0,1])/v[1] + 1
        yb = -pos[1,1]/v[1]
        yc = -pos[2,1]/v[1]
        yd = -pos[0,1]/v[1]
    else:
        if pos[2,1] > 0:
            ye = -pos[0,1]/pos[2,1] + c[1] + 1
            yf = -pos[1,1]/pos[2,1]
            yg = (dy - pos[0,1])/pos[2,1] + c[1]
        elif pos[2,1] < 0:
            ye = (dy - pos[0,1])/pos[2,1] + c[1] + 1
            yf = -pos[1,1]/pos[2,1]
            yg = -pos[0,1]/pos[2,1] + c[1]
        else:
            if pos[1,1] > 0:
                i0 = int(min(max(-pos[0,1]/pos[1,1] + c[0] + 1, 0), m))
                i1 = int(max(min((dy - pos[0,1])/pos[1,1] + c[0], m), i0))
            else:
                i0 = int(min(max((dy - pos[0,1])/pos[1,1] + c[0] + 1, 0), m))
                i1 = int(max(min(-pos[0,1]/pos[1,1] + c[0], m), i0))
            y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            while i0 < i1 and y0 // dy != 0:
                i0 += 1
                y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            while i1 > i0 and y0 // dy != 0:
                i1 -= 1
                y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            if i0 == i1:
                return False
            
    xa, xb, xc, xd = start, 0., 0., stop
    xe, xf, xg = 0., 0., n
    if v[2] > 0:
        xa = -pos[0,2]/v[2] + 1
        xb = -pos[1,2]/v[2]
        xc = -pos[2,2]/v[2]
        xd = (dx - pos[0,2])/v[2]
    elif v[2] < 0:
        xa = (dx - pos[0,2])/v[2] + 1
        xb = -pos[1,2]/v[2]
        xc = -pos[2,2]/v[2]
        xd = -pos[0,2]/v[2]
    else:
        if pos[2,2] > 0:
            xe = -pos[0,2]/pos[2,2] + c[1] + 1
            xf = -pos[1,2]/pos[2,2]
            xg = (dx - pos[0,2])/pos[2,2] + c[1]
        elif pos[2,2] < 0:
            xe = (dx - pos[0,2])/pos[2,2] + c[1] + 1
            xf = -pos[1,2]/pos[2,2]
            xg = -pos[0,2]/pos[2,2] + c[1]
        else:
            if pos[1,2] > 0:
                i0 = int(min(max(-pos[0,2]/pos[1,2] + c[0] + 1, 0), m))
                i1 = int(max(min((dx - pos[0,2])/pos[1,2] + c[0], m), i0))
            else:
                i0 = int(min(max((dx - pos[0,2])/pos[1,2] + c[0] + 1, 0), m))
                i1 = int(max(min(-pos[0,2]/pos[1,2] + c[0], m), i0))
            x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            while i0 < i1 and x0 // dx != 0:
                i0 += 1
                x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            while i1 > i0 and x0 // dx != 0:
                i1 -= 1
                x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            if i0 == i1:
                return False
            
    # for i in prange(i0, i1, nogil=True):
    for i in range(i0, i1):
        s = i - c[0]
        z0 = pos[0,0] + s*pos[1,0]
        y0 = pos[0,1] + s*pos[1,1]
        x0 = pos[0,2] + s*pos[1,2]     
        
        j0 = int(min(max(ze + zf*s, ye + yf*s, xe + xf*s, 0), n))
        j1 = int(max(min(zg + zf*s, yg + yf*s, xg + xf*s, n), j0))
        
        for j in range(j0, j1):
            t = j - c[1]
            z1 = z0 + t*pos[2,0]
            y1 = y0 + t*pos[2,1]
            x1 = x0 + t*pos[2,2]
            
            k0 = int(min(max(za + zb*s + zc*t, ya + yb*s + yc*t, xa + xb*s + xc*t, start), stop))
            k1 = int(max(min(zd + zb*s + zc*t, yd + yb*s + yc*t, xd + xb*s + xc*t, stop), k0))
            
            if k0 == k1:
                continue
            z = z1 + k0*v[0]
            y = y1 + k0*v[1]
            x = x1 + k0*v[2]
            while k0 < k1 and (z//dz!=0 or y//dy!=0 or x//dx!=0):
                k0 = k0 + 1
                z = z1 + k0*v[0]
                y = y1 + k0*v[1]
                x = x1 + k0*v[2]
            z = z1 + (k1-1)*v[0]
            y = y1 + (k1-1)*v[1]
            x = x1 + (k1-1)*v[2]
            while k1 > k0 and (z//dz!=0 or y//dy!=0 or x//dx!=0):
                k1 = k1 - 1
                z = z1 + (k1-1)*v[0]
                y = y1 + (k1-1)*v[1]
                x = x1 + (k1-1)*v[2]
            if k0 == k1:
                continue
            if k0 <= 0 and k1 > 0:
                exist += True
            
            for k in range(k0, k1):
                z = z1 + k*v[0]
                y = y1 + k*v[1]
                x = x1 + k*v[2]
                zg1 = int(z)
                yg1 = int(y)
                xg1 = int(x)
                zg2 = zg1 + 1
                yg2 = yg1 + 1
                xg2 = xg1 + 1
                zd1 = z%1
                yd1 = y%1
                xd1 = x%1
                zd2 = 1.- zd1
                yd2 = 1.- yd1
                xd2 = 1.- xd1
                
                for l in range(chs):
                    r = int(((box[ch_show[l], zg1, yg1, xg1]*xd2 +\
                              box[ch_show[l], zg1, yg1, xg2]*xd1)*yd2 + \
                             (box[ch_show[l], zg1, yg2, xg1]*xd2 + \
                              box[ch_show[l], zg1, yg2, xg2]*xd1)*yd1)*zd2 + \
                            ((box[ch_show[l], zg2, yg1, xg1]*xd2 +\
                              box[ch_show[l], zg2, yg1, xg2]*xd1)*yd2 + \
                             (box[ch_show[l], zg2, yg2, xg1]*xd2 + \
                              box[ch_show[l], zg2, yg2, xg2]*xd1)*yd1)*zd1)
                    if r > res[ch_show[l],i,j]:
                        res[ch_show[l],i,j] = r
                        
    return exist


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef stack_section2(cnp.ndarray[DTYPE_t, ndim=4] box, cnp.ndarray[DTYPE_t2, ndim=2] pos,
                     cnp.ndarray[DTYPE_t2, ndim=1] v, int start, int stop, 
                     cnp.ndarray[DTYPE_t, ndim=3] res):
    cdef int i, j, k, l, z, y, x, i0, i1, s, e
    cdef float z0, y0, x0, za, ya, xa, zc, yc, xc
    cdef int dc = box.shape[0]
    cdef int dz = box.shape[1] - 1
    cdef int dy = box.shape[2] - 1
    cdef int dx = box.shape[3] - 1
    cdef int m = res.shape[1]
    cdef int n = res.shape[2]
    cdef cnp.ndarray[DTYPE_t2, ndim=2] pos1
    
    # for i in prange(m, nogil=True):
    for i in range(m):
        for j in range(n):
            for l in range(dc):
                res[l,i,j] = 0
    
    y0 = pos[0,1] - (m//2) + 0.5
    
    i0 = int(-pos[0,1] + 1) + m//2
    i1 = int(dy - pos[0,1]) + m//2
    
    for l in range(start, stop):
        pos1 = pos.copy()
        pos1[0,0] = pos1[0,0] + v[0]*l
        pos1[0,2] = pos1[0,2] + v[2]*l
    
        if pos1[2,0] > 0:
            za = -pos1[0,0]/pos1[2,0] + n//2 + 1
            zc = dz/pos1[2,0] - 1 + za
        elif pos1[2,0] < 0:
            za = dz/pos1[2,0] - pos1[0,0]/pos1[2,0] + n//2 + 1
            zc = -dz/pos1[2,0] - 1 + za
        else:
            za = 0
            zc = n
            if pos1[0,0] < 0 or pos1[0,0] >= dz:
                continue
        
        if pos1[2,2] > 0:
            xa = -pos1[0,2]/pos1[2,2] + n//2 + 1
            xc = dx/pos1[2,2] - 1 + xa
        elif pos1[2,2] < 0:
            xa = dx/pos1[2,2] - pos1[0,2]/pos1[2,2] + n//2 + 1
            xc = -dx/pos1[2,2] - 1 + xa
        else:
            xa = 0
            xc = n
            if pos1[0,2] < 0 or pos1[0,2] >= dx:
                continue
            
        s = int(min(max(za, xa, 0), n))
        e = int(max(min(zc, xc, n), s))
        
        if s == e:
            continue
        
        z0 = pos1[0,0] + 0.5
        x0 = pos1[0,2] + 0.5
        
        x = int(s) - (n//2)
        z = int(z0 + x*pos1[2,0])
        x = int(x0 + x*pos1[2,2])
        while s < e and (z//dz!=0 or x//dx!=0):
            s = s + 1
            x = int(s) - (n//2)
            z = int(z0 + x*pos1[2,0])
            x = int(x0 + x*pos1[2,2])
            
        x = int(e) - (n//2) - 1
        z = int(z0 + x*pos1[2,0])
        x = int(x0 + x*pos1[2,2])
        while e > s and (z//dz!=0 or x//dx!=0):
            e = e - 1
            x = int(e) - (n//2) - 1
            z = int(z0 + x*pos1[2,0])
            x = int(x0 + x*pos1[2,2])
            
        if s == e:
            continue
        
        # for i in prange(i0, i1, nogil=True):
        for i in range(i0, i1):
            y = int(y0 + i)
            for j in range(s,e):
                x = j - (n//2)
                z = int(z0 + x*pos1[2,0])
                x = int(x0 + x*pos1[2,2])
                for k in range(dc):
                    if box[k,z,y,x] > res[k,i,j]:
                        res[k,i,j] = box[k,z,y,x]
    return True


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef span_section(cnp.ndarray[DTYPE_t, ndim=4] box, cnp.ndarray[DTYPE_t2, ndim=2] pos,
                   cnp.ndarray[DTYPE_t2, ndim=1] v, int start, int stop,
                   cnp.ndarray[DTYPE_t, ndim=4] res, cnp.ndarray[DTYPE_t3, ndim=1] c,
                   cnp.ndarray[DTYPE_t3, ndim=1] ch_show):
    cdef int i, j, k, l, zg1, yg1, xg1, zg2, yg2, xg2, r, j0, j1, k0, k1
    cdef float z0, y0, x0, z1, y1, x1, z, y, x, zd1, yd1, xd1, zd2, yd2, xd2, s, t
    cdef float za, ya, xa, zb, yb, xb, zc, yc, xc, zd, yd, xd, ze, ye, xe, zf, yf, xf, zg, yg, xg
    cdef bint exist = False
    cdef int dc = box.shape[0]
    cdef int dz = box.shape[1] - 1
    cdef int dy = box.shape[2] - 1
    cdef int dx = box.shape[3] - 1
    cdef int depth = res.shape[0]
    cdef int m = res.shape[2]
    cdef int n = res.shape[3]
    
    cdef int i0 = 0
    cdef int i1 = m
    
    cdef int chs = len(ch_show)
    
    # for i in prange(m, nogil=True):
    for i in range(m):
        for j in range(n):
            for k in range(depth):
                for l in range(dc):
                    res[k,l,i,j] = 0
    
    za, zb, zc, zd = start, 0., 0., stop
    ze, zf, zg = 0., 0., n
    if v[0] > 0:
        za = -pos[0,0]/v[0] + 1
        zb = -pos[1,0]/v[0]
        zc = -pos[2,0]/v[0]
        zd = (dz - pos[0,0])/v[0]
    elif v[0] < 0:
        za = (dz - pos[0,0])/v[0] + 1
        zb = -pos[1,0]/v[0]
        zc = -pos[2,0]/v[0]
        zd = -pos[0,0]/v[0]
    else:
        if pos[2,0] > 0:
            ze = -pos[0,0]/pos[2,0] + c[1] + 1
            zf = -pos[1,0]/pos[2,0]
            zg = (dz - pos[0,0])/pos[2,0] + c[1]
        elif pos[2,0] < 0:
            ze = (dz - pos[0,0])/pos[2,0] + c[1] + 1
            zf = -pos[1,0]/pos[2,0]
            zg = -pos[0,0]/pos[2,0] + c[1]
        else:
            if pos[1,0] > 0:
                i0 = int(min(max(-pos[0,0]/pos[1,0] + c[0] + 1, 0), m))
                i1 = int(max(min((dz - pos[0,0])/pos[1,0] + c[0], m), i0))
            else:
                i0 = int(min(max((dz - pos[0,0])/pos[1,0] + c[0] + 1, 0), m))
                i1 = int(max(min(-pos[0,0]/pos[1,0] + c[0], m), i0))
            z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            while i0 < i1 and z0 // dz != 0:
                i0 += 1
                z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            while i1 > i0 and z0 // dz != 0:
                i1 -= 1
                z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            if i0 == i1:
                return False
            
    ya, yb, yc, yd = start, 0., 0., stop
    ye, yf, yg = 0., 0., n
    if v[1] > 0:
        ya = -pos[0,1]/v[1] + 1
        yb = -pos[1,1]/v[1]
        yc = -pos[2,1]/v[1]
        yd = (dy - pos[0,1])/v[1]
    elif v[1] < 0:
        ya = (dy - pos[0,1])/v[1] + 1
        yb = -pos[1,1]/v[1]
        yc = -pos[2,1]/v[1]
        yd = -pos[0,1]/v[1]
    else:
        if pos[2,1] > 0:
            ye = -pos[0,1]/pos[2,1] + c[1] + 1
            yf = -pos[1,1]/pos[2,1]
            yg = (dy - pos[0,1])/pos[2,1] + c[1]
        elif pos[2,1] < 0:
            ye = (dy - pos[0,1])/pos[2,1] + c[1] + 1
            yf = -pos[1,1]/pos[2,1]
            yg = -pos[0,1]/pos[2,1] + c[1]
        else:
            if pos[1,1] > 0:
                i0 = int(min(max(-pos[0,1]/pos[1,1] + c[0] + 1, 0), m))
                i1 = int(max(min((dy - pos[0,1])/pos[1,1] + c[0], m), i0))
            else:
                i0 = int(min(max((dy - pos[0,1])/pos[1,1] + c[0] + 1, 0), m))
                i1 = int(max(min(-pos[0,1]/pos[1,1] + c[0], m), i0))
            y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            while i0 < i1 and y0 // dy != 0:
                i0 += 1
                y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            while i1 > i0 and y0 // dy != 0:
                i1 -= 1
                y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            if i0 == i1:
                return False
            
    xa, xb, xc, xd = start, 0., 0., stop
    xe, xf, xg = 0., 0., n
    if v[2] > 0:
        xa = -pos[0,2]/v[2] + 1
        xb = -pos[1,2]/v[2]
        xc = -pos[2,2]/v[2]
        xd = (dx - pos[0,2])/v[2]
    elif v[2] < 0:
        xa = (dx - pos[0,2])/v[2] + 1
        xb = -pos[1,2]/v[2]
        xc = -pos[2,2]/v[2]
        xd = -pos[0,2]/v[2]
    else:
        if pos[2,2] > 0:
            xe = -pos[0,2]/pos[2,2] + c[1] + 1
            xf = -pos[1,2]/pos[2,2]
            xg = (dx - pos[0,2])/pos[2,2] + c[1]
        elif pos[2,2] < 0:
            xe = (dx - pos[0,2])/pos[2,2] + c[1] + 1
            xf = -pos[1,2]/pos[2,2]
            xg = -pos[0,2]/pos[2,2] + c[1]
        else:
            if pos[1,2] > 0:
                i0 = int(min(max(-pos[0,2]/pos[1,2] + c[0] + 1, 0), m))
                i1 = int(max(min((dx - pos[0,2])/pos[1,2] + c[0], m), i0))
            else:
                i0 = int(min(max((dx - pos[0,2])/pos[1,2] + c[0] + 1, 0), m))
                i1 = int(max(min(-pos[0,2]/pos[1,2] + c[0], m), i0))
            x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            while i0 < i1 and x0 // dx != 0:
                i0 += 1
                x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            while i1 > i0 and x0 // dx != 0:
                i1 -= 1
                x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            if i0 == i1:
                return False
            
    # for i in prange(i0, i1, nogil=True):
    for i in range(i0, i1):
        s = i - c[0]
        z0 = pos[0,0] + s*pos[1,0]
        y0 = pos[0,1] + s*pos[1,1]
        x0 = pos[0,2] + s*pos[1,2]     
        
        j0 = int(min(max(ze + zf*s, ye + yf*s, xe + xf*s, 0), n))
        j1 = int(max(min(zg + zf*s, yg + yf*s, xg + xf*s, n), j0))
        
        for j in range(j0, j1):
            t = j - c[1]
            z1 = z0 + t*pos[2,0]
            y1 = y0 + t*pos[2,1]
            x1 = x0 + t*pos[2,2]
            
            k0 = int(min(max(za + zb*s + zc*t, ya + yb*s + yc*t, xa + xb*s + xc*t, start), stop))
            k1 = int(max(min(zd + zb*s + zc*t, yd + yb*s + yc*t, xd + xb*s + xc*t, stop), k0))
            
            if k0 == k1:
                continue
            z = z1 + k0*v[0]
            y = y1 + k0*v[1]
            x = x1 + k0*v[2]
            while k0 < k1 and (z//dz!=0 or y//dy!=0 or x//dx!=0):
                k0 = k0 + 1
                z = z1 + k0*v[0]
                y = y1 + k0*v[1]
                x = x1 + k0*v[2]
            z = z1 + (k1-1)*v[0]
            y = y1 + (k1-1)*v[1]
            x = x1 + (k1-1)*v[2]
            while k1 > k0 and (z//dz!=0 or y//dy!=0 or x//dx!=0):
                k1 = k1 - 1
                z = z1 + (k1-1)*v[0]
                y = y1 + (k1-1)*v[1]
                x = x1 + (k1-1)*v[2]
            if k0 == k1:
                continue
            if k0 <= 0 and k1 > 0:
                exist += True
            
            for k in range(k0, k1):
                z = z1 + k*v[0]
                y = y1 + k*v[1]
                x = x1 + k*v[2]
                zg1 = int(z)
                yg1 = int(y)
                xg1 = int(x)
                zg2 = zg1 + 1
                yg2 = yg1 + 1
                xg2 = xg1 + 1
                zd1 = z%1
                yd1 = y%1
                xd1 = x%1
                zd2 = 1.- zd1
                yd2 = 1.- yd1
                xd2 = 1.- xd1
                
                for l in range(chs):
                    r = int(((box[ch_show[l], zg1, yg1, xg1]*xd2 +\
                              box[ch_show[l], zg1, yg1, xg2]*xd1)*yd2 + \
                             (box[ch_show[l], zg1, yg2, xg1]*xd2 + \
                              box[ch_show[l], zg1, yg2, xg2]*xd1)*yd1)*zd2 + \
                            ((box[ch_show[l], zg2, yg1, xg1]*xd2 +\
                              box[ch_show[l], zg2, yg1, xg2]*xd1)*yd2 + \
                             (box[ch_show[l], zg2, yg2, xg1]*xd2 + \
                              box[ch_show[l], zg2, yg2, xg2]*xd1)*yd1)*zd1)
                    res[k-start,ch_show[l],i,j] = r
                        
    return exist


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef fast_stack(cnp.ndarray[DTYPE_t, ndim=4] box, cnp.ndarray[DTYPE_t2, ndim=2] pos,
                 cnp.ndarray[DTYPE_t2, ndim=1] v, int start, int stop,
                 cnp.ndarray[DTYPE_t, ndim=3] res, cnp.ndarray[DTYPE_t3, ndim=1] c,
                 cnp.ndarray[DTYPE_t3, ndim=1] ch_show):
    cdef int i, j, k, l, gz, gy, gx, r, j0, j1, k0, k1
    cdef float z0, y0, x0, z1, y1, x1, z, y, x, s, t
    cdef float za, ya, xa, zb, yb, xb, zc, yc, xc, zd, yd, xd, ze, ye, xe, zf, yf, xf, zg, yg, xg
    cdef bint exist = False
    cdef int dc = box.shape[0]
    cdef int dz = box.shape[1] - 1
    cdef int dy = box.shape[2] - 1
    cdef int dx = box.shape[3] - 1
    cdef int m = res.shape[1]
    cdef int n = res.shape[2]
    
    cdef int i0 = 0
    cdef int i1 = m
    
    cdef int chs = len(ch_show)
    
    # for i in prange(m, nogil=True):
    for i in range(m):
        for j in range(n):
            for l in range(chs):
                res[ch_show[l],i,j] = 0
    
    za, zb, zc, zd = start, 0., 0., stop
    ze, zf, zg = 0., 0., n
    if v[0] > 0:
        za = -pos[0,0]/v[0] + 1
        zb = -pos[1,0]/v[0]
        zc = -pos[2,0]/v[0]
        zd = (dz - pos[0,0])/v[0]
    elif v[0] < 0:
        za = (dz - pos[0,0])/v[0] + 1
        zb = -pos[1,0]/v[0]
        zc = -pos[2,0]/v[0]
        zd = -pos[0,0]/v[0]
    else:
        if pos[2,0] > 0:
            ze = -pos[0,0]/pos[2,0] + c[1] + 1
            zf = -pos[1,0]/pos[2,0]
            zg = (dz - pos[0,0])/pos[2,0] + c[1]
        elif pos[2,0] < 0:
            ze = (dz - pos[0,0])/pos[2,0] + c[1] + 1
            zf = -pos[1,0]/pos[2,0]
            zg = -pos[0,0]/pos[2,0] + c[1]
        else:
            if pos[1,0] > 0:
                i0 = int(min(max(-pos[0,0]/pos[1,0] + c[0] + 1, 0), m))
                i1 = int(max(min((dz - pos[0,0])/pos[1,0] + c[0], m), i0))
            else:
                i0 = int(min(max((dz - pos[0,0])/pos[1,0] + c[0] + 1, 0), m))
                i1 = int(max(min(-pos[0,0]/pos[1,0] + c[0], m), i0))
            z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            while i0 < i1 and z0 // dz != 0:
                i0 += 1
                z0 = pos[0,0] + (i0 - c[0])*pos[1,0]
            z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            while i1 > i0 and z0 // dz != 0:
                i1 -= 1
                z0 = pos[0,0] + (i1 - c[0] - 1)*pos[1,0]
            if i0 == i1:
                return False
            
    ya, yb, yc, yd = start, 0., 0., stop
    ye, yf, yg = 0., 0., n
    if v[1] > 0:
        ya = -pos[0,1]/v[1] + 1
        yb = -pos[1,1]/v[1]
        yc = -pos[2,1]/v[1]
        yd = (dy - pos[0,1])/v[1]
    elif v[1] < 0:
        ya = (dy - pos[0,1])/v[1] + 1
        yb = -pos[1,1]/v[1]
        yc = -pos[2,1]/v[1]
        yd = -pos[0,1]/v[1]
    else:
        if pos[2,1] > 0:
            ye = -pos[0,1]/pos[2,1] + c[1] + 1
            yf = -pos[1,1]/pos[2,1]
            yg = (dy - pos[0,1])/pos[2,1] + c[1]
        elif pos[2,1] < 0:
            ye = (dy - pos[0,1])/pos[2,1] + c[1] + 1
            yf = -pos[1,1]/pos[2,1]
            yg = -pos[0,1]/pos[2,1] + c[1]
        else:
            if pos[1,1] > 0:
                i0 = int(min(max(-pos[0,1]/pos[1,1] + c[0] + 1, 0), m))
                i1 = int(max(min((dy - pos[0,1])/pos[1,1] + c[0], m), i0))
            else:
                i0 = int(min(max((dy - pos[0,1])/pos[1,1] + c[0] + 1, 0), m))
                i1 = int(max(min(-pos[0,1]/pos[1,1] + c[0], m), i0))
            y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            while i0 < i1 and y0 // dy != 0:
                i0 += 1
                y0 = pos[0,1] + (i0 - c[0])*pos[1,1]
            y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            while i1 > i0 and y0 // dy != 0:
                i1 -= 1
                y0 = pos[0,1] + (i1 - c[0] - 1)*pos[1,1]
            if i0 == i1:
                return False
            
    xa, xb, xc, xd = start, 0., 0., stop
    xe, xf, xg = 0., 0., n
    if v[2] > 0:
        xa = -pos[0,2]/v[2] + 1
        xb = -pos[1,2]/v[2]
        xc = -pos[2,2]/v[2]
        xd = (dx - pos[0,2])/v[2]
    elif v[2] < 0:
        xa = (dx - pos[0,2])/v[2] + 1
        xb = -pos[1,2]/v[2]
        xc = -pos[2,2]/v[2]
        xd = -pos[0,2]/v[2]
    else:
        if pos[2,2] > 0:
            xe = -pos[0,2]/pos[2,2] + c[1] + 1
            xf = -pos[1,2]/pos[2,2]
            xg = (dx - pos[0,2])/pos[2,2] + c[1]
        elif pos[2,2] < 0:
            xe = (dx - pos[0,2])/pos[2,2] + c[1] + 1
            xf = -pos[1,2]/pos[2,2]
            xg = -pos[0,2]/pos[2,2] + c[1]
        else:
            if pos[1,2] > 0:
                i0 = int(min(max(-pos[0,2]/pos[1,2] + c[0] + 1, 0), m))
                i1 = int(max(min((dx - pos[0,2])/pos[1,2] + c[0], m), i0))
            else:
                i0 = int(min(max((dx - pos[0,2])/pos[1,2] + c[0] + 1, 0), m))
                i1 = int(max(min(-pos[0,2]/pos[1,2] + c[0], m), i0))
            x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            while i0 < i1 and x0 // dx != 0:
                i0 += 1
                x0 = pos[0,2] + (i0 - c[0])*pos[1,2]
            x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            while i1 > i0 and x0 // dx != 0:
                i1 -= 1
                x0 = pos[0,2] + (i1 - c[0] - 1)*pos[1,2]
            if i0 == i1:
                return False
            
    # for i in prange(i0, i1, nogil=True):
    for i in range(i0, i1):
        s = i - c[0]
        z0 = pos[0,0] + s*pos[1,0]
        y0 = pos[0,1] + s*pos[1,1]
        x0 = pos[0,2] + s*pos[1,2]     
        
        j0 = int(min(max(ze + zf*s, ye + yf*s, xe + xf*s, 0), n))
        j1 = int(max(min(zg + zf*s, yg + yf*s, xg + xf*s, n), j0))
        
        for j in range(j0, j1):
            t = j - c[1]
            z1 = z0 + t*pos[2,0]
            y1 = y0 + t*pos[2,1]
            x1 = x0 + t*pos[2,2]
            
            k0 = int(min(max(za + zb*s + zc*t, ya + yb*s + yc*t, xa + xb*s + xc*t, start), stop))
            k1 = int(max(min(zd + zb*s + zc*t, yd + yb*s + yc*t, xd + xb*s + xc*t, stop), k0))
            
            if k0 == k1:
                continue
            z = z1 + k0*v[0]
            y = y1 + k0*v[1]
            x = x1 + k0*v[2]
            while k0 < k1 and (z//dz!=0 or y//dy!=0 or x//dx!=0):
                k0 = k0 + 1
                z = z1 + k0*v[0]
                y = y1 + k0*v[1]
                x = x1 + k0*v[2]
            z = z1 + (k1-1)*v[0]
            y = y1 + (k1-1)*v[1]
            x = x1 + (k1-1)*v[2]
            while k1 > k0 and (z//dz!=0 or y//dy!=0 or x//dx!=0):
                k1 = k1 - 1
                z = z1 + (k1-1)*v[0]
                y = y1 + (k1-1)*v[1]
                x = x1 + (k1-1)*v[2]
            if k0 == k1:
                continue
            if k0 <= 0 and k1 > 0:
                exist += True
            if k0%2 == 0:
                k0 = k0 + (i+j)%2
            else:
                k0 = k0 + (i+j+1)%2
            
            for k in range(k0, k1, 2):
                z = z1 + k*v[0]
                y = y1 + k*v[1]
                x = x1 + k*v[2]
                gz = int(z)
                gy = int(y)
                gx = int(x)
                
                for l in range(chs):
                    r = box[ch_show[l], gz, gy, gx]
                    if r > res[ch_show[l],i,j]:
                        res[ch_show[l],i,j] = r
                        
    return exist


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef calc_bgr(cnp.ndarray[DTYPE_t, ndim=3] frame, cnp.ndarray[DTYPE_t2, ndim=2] alpha,
               cnp.ndarray[DTYPE_t4, ndim=2] colors, cnp.ndarray[DTYPE_t3, ndim=1] ch_show,
               cnp.ndarray[DTYPE_t4, ndim=3] res):
    cdef int i, j, k, chs
    cdef float B, G, R, A, a
    chs = len(ch_show)
    if chs == 0:
        # for i in prange(frame.shape[1], nogil=True):
        for i in range(frame.shape[1]):
            for j in range(frame.shape[2]):
                res[i,j,0] = 0
                res[i,j,1] = 0
                res[i,j,2] = 0
                res[i,j,3] = 0
        return
    cdef cnp.ndarray[DTYPE_t2, ndim=2] clr = np.empty([chs,3])
    for k in range(chs):
        clr[k] = colors[ch_show[k]]/255
    
    # for i in prange(frame.shape[1], nogil=True):
    for i in range(frame.shape[1]):
        for j in range(frame.shape[2]):
            A = alpha[ch_show[0], frame[ch_show[0],i,j]]
            B = A*clr[0,0]
            G = A*clr[0,1]
            R = A*clr[0,2]
            for k in range(1,chs):
                a = alpha[ch_show[k], frame[ch_show[k],i,j]]
                B = B + (1-B)*a*clr[k,0]
                G = G + (1-G)*a*clr[k,1]
                R = R + (1-R)*a*clr[k,2]
                A = A + (1-A)*a
            if A > 0:
                B = B/A
                G = G/A
                R = R/A
            res[i,j,0] = int(B*255)
            res[i,j,1] = int(G*255)
            res[i,j,2] = int(R*255)
            res[i,j,3] = int(A*255)


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef calc_bgr_w(cnp.ndarray[DTYPE_t, ndim=3] frame, cnp.ndarray[DTYPE_t2, ndim=2] alpha,
                 cnp.ndarray[DTYPE_t4, ndim=2] colors, cnp.ndarray[DTYPE_t3, ndim=1] ch_show,
                 cnp.ndarray[DTYPE_t4, ndim=3] res):
    cdef int i, j, k, chs
    cdef float B, G, R, A, a
    chs = len(ch_show)
    if chs == 0:
        # for i in prange(frame.shape[1], nogil=True):
        for i in range(frame.shape[1]):
            for j in range(frame.shape[2]):
                res[i,j,0] = 0
                res[i,j,1] = 0
                res[i,j,2] = 0
                res[i,j,3] = 0
        return
    cdef cnp.ndarray[DTYPE_t2, ndim=2] clr = np.empty([chs,3])
    for k in range(chs):
        clr[k] = 1 - colors[ch_show[k]]/255
    
    # for i in prange(frame.shape[1], nogil=True):
    for i in range(frame.shape[1]):
        for j in range(frame.shape[2]):
            A = alpha[ch_show[0], frame[ch_show[0],i,j]]
            B = A*clr[0,0]
            G = A*clr[0,1]
            R = A*clr[0,2]
            for k in range(1,chs):
                a = alpha[ch_show[k], frame[ch_show[k],i,j]]
                B = B + (1-B)*a*clr[k,0]
                G = G + (1-G)*a*clr[k,1]
                R = R + (1-R)*a*clr[k,2]
                A = A + (1-A)*a
            if A > 0:
                B = B/A
                G = G/A
                R = R/A
            res[i,j,0] = int((1-B)*255)
            res[i,j,1] = int((1-G)*255)
            res[i,j,2] = int((1-R)*255)
            res[i,j,3] = int(A*255)
    
                
