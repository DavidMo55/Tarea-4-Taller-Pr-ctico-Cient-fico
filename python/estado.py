"""Bóvedas de estado y control de invalidación; sin componentes gráficos."""
from dataclasses import dataclass
from modelo import sintetizar_senal, calcular_espectro_fft, calcular_svd_matriz


@dataclass
class EstadoFFT:
    parametros: tuple | None = None
    tiempo: object = None
    senal: object = None
    frecuencias: object = None
    magnitud: object = None
    calculos: int = 0

    def generar(self, f, fs, duracion):
        parametros = (float(f),float(fs),float(duracion))
        if self.parametros == parametros:
            return False
        t,y = sintetizar_senal(*parametros)
        frecuencias,magnitud = calcular_espectro_fft(y,fs)
        # Confirmación atómica: un error no destruye la última señal válida.
        self.tiempo,self.senal = t,y
        self.frecuencias,self.magnitud = frecuencias,magnitud
        self.parametros = parametros
        self.calculos += 1
        return True


def asegurar_svd(estado, n):
    if estado.get('dimension_guardada') == n and 'factores_svd' in estado:
        return False
    resultado = calcular_svd_matriz(n)
    estado['factores_svd'] = resultado
    estado['dimension_guardada'] = n
    estado['conteo_svd'] = estado.get('conteo_svd',0)+1
    return True


def preparar_estado_fft(anterior, f, fs, duracion):
    parametros=(float(f),float(fs),float(duracion))
    if anterior.parametros==parametros:
        return anterior
    nuevo=EstadoFFT()
    nuevo.generar(*parametros)
    nuevo.calculos=anterior.calculos+1
    return nuevo
