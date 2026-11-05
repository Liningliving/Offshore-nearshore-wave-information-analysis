"""Candidate null generators for validation only; no wave significance acceptance implied."""
import numpy as np


def height_neighbours(z, k_perm=5):
    """Runge (2018) Algorithm 1: nearest neighbours in conditioning space incl. self."""
    z=np.asarray(z,float)
    if z.ndim!=1 or not np.isfinite(z).all() or not 1<k_perm<=len(z):
        raise ValueError('Require finite scalar conditioning values and 1 < k_perm <= N')
    distance=np.abs(z[:,None]-z[None,:])
    return np.argsort(distance,axis=1,kind='stable')[:,:k_perm]


def local_order(neighbours,rng):
    """Try unused local donors first; if exhausted, reuse final candidate as in paper.

    This is approximate sampling without replacement, not a guaranteed bijection.
    One donor row moves an entire multivariate predictor, including Dx and Dy.
    """
    n,k=neighbours.shape
    output=np.empty(n,dtype=int);used=np.zeros(n,dtype=bool)
    for i in rng.permutation(n):
        candidates=rng.permutation(neighbours[i]);donor=candidates[-1]
        for candidate in candidates:
            donor=candidate
            if not used[donor]:break
        output[i]=donor;used[donor]=True
    return output


def compatible_circular_shifts(hours,minimum_separation=180):
    """Exact-hour circle shifts preserving ALL timestamps and the missingness mask.

    The time circle is [0,last_hour], with one artificial seam. No interpolation,
    compression of missing hours or variable-size intersections is permitted.
    """
    hours=np.asarray(hours,dtype=int);period=int(hours[-1])+1
    if len(hours)==0 or hours[0]!=0 or np.any(np.diff(hours)<=0):raise ValueError('Invalid hours')
    mask=np.zeros(period,dtype=bool);mask[hours]=True
    # FFT autocorrelation counts common available slots for every circular shift.
    transform=np.fft.rfft(mask.astype(float))
    matches=np.rint(np.fft.irfft(transform*np.conj(transform),n=period)).astype(int)
    shifts=np.arange(period)
    permitted=(matches==len(hours))&(shifts>=minimum_separation)&(shifts<=period-minimum_separation)
    candidates=shifts[permitted]
    return candidates


def circular_order(hours,shift):
    hours=np.asarray(hours,dtype=int);period=int(hours[-1])+1
    lookup={int(t):i for i,t in enumerate(hours)}
    targets=(hours+int(shift))%period
    if any(int(t) not in lookup for t in targets):raise ValueError('Shift changes the observation mask')
    return np.array([lookup[int(t)] for t in targets])


def elapsed_acf(hours,x,lag=1):
    index={int(t):i for i,t in enumerate(hours)}
    pairs=[(i,index[int(t)+lag]) for i,t in enumerate(hours) if int(t)+lag in index]
    if len(pairs)<3:return np.nan
    a,b=np.asarray(pairs).T
    return float(np.corrcoef(np.asarray(x)[a],np.asarray(x)[b])[0,1])


def p_plus_one(observed,null):
    null=np.asarray(null,float)
    if not np.isfinite(null).all() or not len(null):raise ValueError('Invalid null draws')
    return (1+int(np.count_nonzero(null>=observed)))/(len(null)+1)
