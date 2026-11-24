"""Modelo puro: NumPy, validación y ninguna dependencia de interfaces."""
from dataclasses import dataclass
import math
import numpy as np


def finito(valor, nombre):
    try:
        numero = float(valor)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f'{nombre}: introduce un número válido.') from error
    if not math.isfinite(numero):
        raise ValueError(f'{nombre} debe ser finito; no se admite NaN ni infinito.')
    return numero


def sintetizar_senal(frecuencia=440.0, fs=10000.0, duracion=1.0):
    f, fs, duracion = (finito(frecuencia,'Frecuencia'), finito(fs,'Muestreo'), finito(duracion,'Duración'))
    if f <= 0 or fs <= 0 or duracion <= 0:
        raise ValueError('Frecuencia, muestreo y duración deben ser positivos.')
    if fs <= 2*f:
        raise ValueError('Nyquist: el muestreo fs debe ser estrictamente mayor que 2·f.')
    cantidad = fs*duracion
    if not math.isfinite(cantidad) or not 2 <= cantidad <= 1_000_000:
        raise ValueError('La señal debe contener entre 2 y 1 000 000 de muestras.')
    n = int(math.floor(cantidad + 0.5))
    t = np.arange(n, dtype=np.float64)/fs
    return t, np.sin(2*np.pi*f*t)


def calcular_espectro_fft(senal, fs):
    fs = finito(fs, 'Muestreo')
    y = np.asarray(senal, dtype=np.float64)
    if fs <= 0 or y.ndim != 1 or y.size < 2 or not np.isfinite(y).all():
        raise ValueError('FFT: señal unidimensional finita de al menos dos muestras y fs positivo.')
    n = y.size
    magnitud = np.abs(np.fft.rfft(y))/n
    if n % 2 == 0:
        magnitud[1:-1] *= 2  # No duplicar DC ni Nyquist.
    else:
        magnitud[1:] *= 2   # Con N impar no existe bin Nyquist.
    return np.fft.rfftfreq(n, 1/fs), magnitud


def evaluar_amortiguamiento(frecuencia, factor_zeta, v0=0.0, x0=1.0):
    f, z, v0, x0 = (finito(frecuencia,'Frecuencia natural'), finito(factor_zeta,'Zeta'),
                     finito(v0,'Velocidad inicial'), finito(x0,'Desplazamiento inicial'))
    if not 0 < f <= 50:
        raise ValueError('La frecuencia natural debe cumplir 0 < f ≤ 50 Hz.')
    if not 0 <= z < 1:
        raise ValueError('Solo régimen subamortiguado: 0 ≤ ζ < 1; no se admite amortiguamiento crítico ni sobreamortiguado.')
    if abs(v0) > 1e6 or abs(x0) > 1e6:
        raise ValueError('Las condiciones iniciales deben tener magnitud ≤ 1 000 000.')
    t = np.linspace(0, 5, 2000)
    wn = 2*np.pi*f
    a = z*wn
    wd = wn*np.sqrt((1-z)*(1+z))
    seno_sobre_wd = t*np.sinc(wd*t/np.pi)
    envolvente = np.exp(-a*t)
    coseno = np.cos(wd*t)
    x = envolvente*(x0*coseno+(v0+a*x0)*seno_sobre_wd)
    v = envolvente*(v0*coseno-(wn*wn*x0+a*v0)*seno_sobre_wd)
    if not np.isfinite(x).all() or not np.isfinite(v).all():
        raise ValueError('El resultado numérico no es finito.')
    return t, x, v


@dataclass(frozen=True)
class FactoresSVD:
    A: np.ndarray
    U: np.ndarray
    sigma: np.ndarray
    Vt: np.ndarray


def calcular_svd_matriz(n: int):
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or not 10 <= n <= 1000:
        raise ValueError('La dimensión debe ser un entero entre 10 y 1000.')
    # Semilla local determinista: misma entrada → misma matriz; no modifica el RNG global.
    A = np.random.default_rng(2026+n).normal(size=(n,n))
    U, sigma, Vt = np.linalg.svd(A, full_matrices=False)
    return FactoresSVD(A, U, sigma, Vt)


def reconstruir_svd(factores, k):
    n = factores.A.shape[0]
    if isinstance(k,bool) or not isinstance(k,(int,np.integer)) or not 1 <= k <= n//10:
        raise ValueError('El rango debe cumplir 1 ≤ k ≤ floor(n/10).')
    Ak = (factores.U[:,:k]*factores.sigma[:k]) @ factores.Vt[:k,:]
    norma = float(np.linalg.norm(factores.A, 'fro'))
    error = float(np.linalg.norm(factores.A-Ak,'fro')/norma) if norma else 0.0
    bytes_original = factores.A.nbytes
    bytes_comprimidos = (n*k+k+k*n)*factores.A.itemsize
    reduccion = 100*(1-bytes_comprimidos/bytes_original)
    ram_arrays = sum(a.nbytes for a in (factores.A,factores.U,factores.sigma,factores.Vt,Ak))
    return Ak, error, reduccion, ram_arrays
