from pathlib import Path
import sys,json
import numpy as np
from matplotlib.figure import Figure
RAIZ=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RAIZ/'python'))
from modelo import sintetizar_senal,calcular_espectro_fft,evaluar_amortiguamiento,calcular_svd_matriz,reconstruir_svd
out=RAIZ/'evidencias';out.mkdir(exist_ok=True)
# Comparación numérica entre implementaciones independientes, con idénticos parámetros.
t,x,v=evaluar_amortiguamiento(7.3,.22,-1.2,1.3)
mat=np.loadtxt(out/'oscilador_matlab_octave.csv',delimiter=',')
np.testing.assert_allclose(np.column_stack((t,x,v)),mat,rtol=1e-11,atol=1e-11)
t,y=sintetizar_senal();f,m=calcular_espectro_fft(y,10000)
matfft=np.loadtxt(out/'fft_matlab_octave.csv',delimiter=',')
np.testing.assert_allclose(np.column_stack((f,m)),matfft,rtol=1e-9,atol=1e-11)
fig=Figure(figsize=(11,4),layout='constrained');a,b=fig.add_subplot(121),fig.add_subplot(122)
a.plot(t,y,color='#146a91');a.set(xlim=(0,.02),title='Ventana inicial de la señal',xlabel='Tiempo (s)',ylabel='Amplitud')
b.plot(f,m,color='#d16b30');b.set(xlim=(0,1000),title='FFT unilateral · señal de 440 Hz',xlabel='Frecuencia (Hz)',ylabel='Amplitud normalizada')
for ax in (a,b):ax.grid(alpha=.25)
fig.savefig(out/'modelo_fft.png',dpi=150)
t,x,v=evaluar_amortiguamiento(2.5,.15,3)
fig=Figure(figsize=(11,4),layout='constrained');a,b=fig.add_subplot(121),fig.add_subplot(122)
a.plot(t,x,color='#146a91');a.set(title='Respuesta temporal · v₀ = 3',xlabel='Tiempo (s)',ylabel='Desplazamiento x(t)')
b.plot(x,v,color='#d16b30');b.set(title='Retrato de fase',xlabel='Desplazamiento x',ylabel='Velocidad v')
for ax in (a,b):ax.grid(alpha=.25)
fig.savefig(out/'modelo_oscilador.png',dpi=150)
r=calcular_svd_matriz(100);Ak,error,reduccion,ram=reconstruir_svd(r,7)
fig=Figure(figsize=(9,4),layout='constrained');a=fig.add_subplot(111)
a.semilogy(range(1,101),r.sigma,color='#146a91');a.axvline(7,color='#d16b30',linestyle='--',label='k=7')
a.set(title='SVD · factores persistentes',xlabel='Índice',ylabel='Valor singular (escala logarítmica)');a.legend();a.grid(alpha=.25)
fig.savefig(out/'modelo_svd.png',dpi=150)
resumen={'comparacion_python_matlab_octave':'Correcta: FFT y oscilador dentro de tolerancia.',
         'fft':{'frecuencia_pico_hz':float(f[np.argmax(m)]),'amplitud_pico':float(m.max())},
         'svd_python':{'n':100,'k':7,'error_relativo_frobenius':error,'reduccion_teorica_porcentaje':reduccion,
                       'bytes_arreglos_con_Ak':ram}}
(out/'resultados_numericos.json').write_text(json.dumps(resumen,ensure_ascii=False,indent=2))
print('Evidencias generadas; modelos Python y MATLAB/Octave coinciden.')
