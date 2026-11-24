# Reporte de Tarea 4

## Objetivo y alcance

Se desarrollaron herramientas para análisis espectral, dinámica de un oscilador y aproximación matricial, separando el cálculo de la interfaz y reutilizando resultados costosos. Se usaron los cinco cuadernos `Semana 3 - Ejemplos_A` a `Ejemplos_E` como referencia y el planteamiento proporcionado como especificación. El ejemplo D contiene una adaptación con ipywidgets; aquí se construyó la versión Tkinter solicitada. No se proporcionó una clase MATLAB `JerarquiaPOO.m`, por lo que se creó su implementación.

Python presenta FFT y oscilador en Tkinter, y SVD en Streamlit. MATLAB y C++ reúnen las tres actividades en aplicaciones con pestañas. C++ utiliza Qt para la vista y Eigen para cálculo. Esta tarea estudia arquitectura, estado y validación; las tablas de tiempos de las tareas anteriores no forman parte de este planteamiento.

## 1. Separación Modelo–Vista–Controlador

| Responsabilidad | Python | MATLAB | C++ |
|---|---|---|---|
| Modelo: cálculo sin componentes gráficos | `modelo.py` | Funciones `.m` y método privado `calcularEspectroFFT` | `models.hpp` |
| Vista: controles, lienzos y métricas | `vista_tk.py`, `vista_streamlit.py` | Creación de componentes y métodos de dibujo en `JerarquiaPOO` | `view.hpp` |
| Controlador: eventos, validaciones y actualización del estado | `controlador_tk.py`, `app_streamlit.py`, `estado.py` | Callbacks de `JerarquiaPOO` | `controller.hpp` |
| Estado persistente | Objetos de estado y `st.session_state` | Propiedades privadas | Estructuras de estado del controlador |

La tabla muestra dónde se encuentra cada responsabilidad. En MATLAB las responsabilidades de vista y controlador están organizadas en métodos de una misma clase, mientras que las funciones numéricas independientes permiten probar el cálculo sin abrir la aplicación. El método privado solicitado lee la señal y devuelve el espectro sin dibujar.

El controlador valida antes de confirmar un resultado nuevo. Una entrada inválida conserva el último resultado válido. En Tkinter y C++ el cálculo pesado de FFT se realiza en un trabajador y la actualización gráfica ocurre en el hilo principal; C++ también calcula SVD en segundo plano. MATLAB muestra progreso modal durante el cálculo síncrono: no se presenta como una implementación de cálculo en segundo plano.

## 2. Señal y FFT unilateral

Se construye una señal de amplitud unitaria:

\[
y_j=\sin(2\pi f j/f_s),\qquad j=0,\ldots,N-1.
\]

El controlador exige valores finitos, frecuencia y duración positivas y **\(f_s>2f\)**. El valor inicial es \(f_s=10000\) Hz. Se limita la señal a un máximo de un millón de muestras para evitar asignaciones desproporcionadas.

Después se calcula \(Y=\operatorname{FFT}(y)\). Para el espectro unilateral:

\[
f_k=kf_s/N,\qquad P_k=|Y_k|/N,\qquad 0\leq k\leq\lfloor N/2\rfloor.
\]

Se duplican las amplitudes positivas, excepto el término de Nyquist cuando \(N\) es par; DC nunca se duplica. Así se recupera la amplitud de una senoide cuyo número de ciclos coincide con la ventana de observación. Para frecuencias que no coinciden con un bin puede aparecer fuga espectral: no se aplica ventana adicional.

En MATLAB, `VectorFrecuencias` y `MagnitudEspectro` son propiedades privadas. Cambiar entre escala lineal y semilogarítmica solamente dibuja esos arreglos. En escala logarítmica se omite la frecuencia cero porque su logaritmo no está definido. La ventana temporal inicial de hasta 20 ms facilita ver los ciclos; el análisis utiliza la señal completa.

![Modelo FFT](evidencias/modelo_fft.png)

## 3. Oscilador con velocidad inicial

El modelo implementado es el oscilador lineal libre amortiguado:

\[
x''+2\zeta\omega_n x'+\omega_n^2x=0,\quad
\omega_n=2\pi f,\quad x(0)=x_0=1,\quad x'(0)=v_0.
\]

Aunque el texto introductorio menciona sistemas no lineales, la ecuación del ejemplo corresponde a un sistema lineal. Se restringe a \(0<f\leq50\) Hz y \(0\leq\zeta<1\), tal como se solicita.

Definiendo \(a=\zeta\omega_n\) y \(\omega_d=\omega_n\sqrt{1-\zeta^2}\), la solución es:

\[
x(t)=e^{-at}\left[x_0\cos(\omega_dt)+(v_0+ax_0)\frac{\sin(\omega_dt)}{\omega_d}\right],
\]

\[
v(t)=e^{-at}\left[v_0\cos(\omega_dt)-(\omega_n^2x_0+av_0)\frac{\sin(\omega_dt)}{\omega_d}\right].
\]

Se usa una evaluación estable del cociente seno/frecuencia cerca del amortiguamiento crítico. Al sustituir \(t=0\), se obtiene exactamente \(x(0)=x_0\) y \(v(0)=v_0\). La función devuelve tres arreglos: tiempo, desplazamiento y velocidad. No estima la velocidad mediante diferencias finitas.

Tkinter vincula la velocidad inicial con una `DoubleVar` y un `ttk.Entry`. El botón de restablecimiento modifica las variables con `.set()` y vuelve a dibujar. Los subgráficos `121` y `122` muestran desplazamiento contra tiempo y velocidad contra desplazamiento. Los valores fuera del dominio producen `messagebox.showwarning`.

Con amortiguamiento positivo la trayectoria de fase converge al origen; sin amortiguamiento conserva su energía y forma una curva cerrada.

![Modelo oscilador](evidencias/modelo_oscilador.png)

## 4. SVD, caché y compresión

El modelo genera una matriz gaussiana cuadrada con un generador local de semilla fija. Para la misma dimensión, cada implementación es reproducible sin modificar el estado aleatorio global. Los generadores de los tres lenguajes no producen necesariamente la misma matriz.

Se factoriza una sola vez por cambio de dimensión:

\[
A=U\Sigma V^T.
\]

En Python se utiliza `np.linalg.svd(A, full_matrices=False)`. El controlador conserva los factores en `st.session_state` y muestra `st.spinner` durante la factorización. Para \(1\leq k\leq\lfloor n/10\rfloor\), se reconstruye:

\[
A_k=U_{:,:k}\operatorname{diag}(\sigma_{:k})V^T_{:k,:}.
\]

Mover el deslizador cambia la reconstrucción, su error y la gráfica, pero no vuelve a ejecutar SVD. El estado guarda la dimensión actual; no acumula matrices de todas las dimensiones visitadas. Las opciones de interfaz son 100, 250, 500 y 1000.

Las tres métricas son:

\[
E=\frac{\|A-A_k\|_F}{\|A\|_F},\qquad
R=100\left(1-\frac{2nk+k}{n^2}\right),\qquad
C=\text{número de factorizaciones completadas}.
\]

**La reducción R corresponde al almacenamiento de los factores truncados**, no a una medición de RAM liberada por la aplicación. Una matriz original requiere \(n^2\) números; los factores truncados requieren \(nk+k+kn\). Para poder interactuar se mantienen la matriz y los factores completos en RAM. Contando además una reconstrucción completa y datos `float64`, sus arreglos suman aproximadamente \(8(4n^2+n)\) bytes, sin contar temporales, objetos ni espacio de trabajo de las bibliotecas. No es memoria total del proceso.

La gráfica utiliza escala logarítmica vertical para los valores singulares y una línea discontinua en el índice k. Una matriz gaussiana densa suele tener rango completo: reducir mucho el almacenamiento puede dejar un error grande. Eso es un resultado esperado, no un fallo del algoritmo.

![Modelo SVD](evidencias/modelo_svd.png)

## 5. Resultados y explicación de las tablas

### Resultados numéricos representativos

| Experimento | Resultado observado | Interpretación |
|---|---:|---|
| FFT: seno de 440 Hz, fs=10000 Hz, duración 1 s | Pico a 440 Hz | Ubicación correcta de la frecuencia de entrada |
| Amplitud del pico | 0.9999999999999998 | Coincide con amplitud 1 dentro del error de punto flotante |
| SVD Python: n=100, k=7 | Error relativo 0.876584 | Se conserva solamente una parte de la matriz aleatoria |
| Almacenamiento truncado: n=100, k=7 | Reducción 85.93 % | 1407 números frente a 10000 de la matriz original |
| Arreglos completos de esa sesión, incluyendo Ak | 320800 bytes | Aproximadamente 0.306 MiB; no representa el ahorro ni la memoria total del proceso |

La tabla reúne mediciones del archivo `evidencias/resultados_numericos.json`. La coincidencia del pico valida la FFT. La combinación de ahorro alto y error alto muestra el compromiso de comprimir una matriz sin estructura marcada. Los resultados de error SVD de C++ pueden diferir porque su matriz aleatoria es distinta; la fórmula de almacenamiento sí coincide.

### Auditoría de la caché en Streamlit

| Ejecución de la aplicación | Dimensión n | Rango k | Contador de SVD |
|---:|---:|---:|---:|
| 1: inicial | 100 | 1 | 1 |
| 2: cambio de rango | 100 | 7 | 1 |
| 3: cambio de dimensión | 250 | 1 | 2 |
| 4: cambio de rango | 250 | 25 | 2 |
| 5: regreso a dimensión anterior | 100 | 1 | 3 |

Esta tabla reproduce los cinco ciclos comprobados con `AppTest`. Las filas 2 y 4 demuestran reutilización de los mismos factores al mover k. La fila 5 demuestra que se conserva solamente la dimensión actual; volver a una dimensión anterior calcula una nueva factorización.

### Verificación ejecutada y límites

| Componente | Verificación | Resultado |
|---|---|---|
| Modelos y estado Python | 9 pruebas: FFT, dominios, condiciones iniciales, energía, SVD, aleatoriedad y caché | Correcto |
| Controlador Tkinter | Variables Tcl reales, vista simulada, reinicio y advertencias | Correcto; ventana nativa pendiente |
| Streamlit | 5 ejecuciones reales del script mediante AppTest | Correcto; no es una prueba visual en navegador |
| C++ numérico | FFT, oscilador, SVD y entradas inválidas | Correcto |
| C++ interfaz Qt | Eventos, cachés, advertencias, reinicio y capturas sin pantalla | Correcto |
| Funciones MATLAB en GNU Octave 10.3 | Modelos, dominios, RNG y exportación de datos | Correcto |
| Comparación Python–MATLAB/Octave | Arreglos del oscilador y FFT con entradas comunes, dentro de tolerancia | Correcto |
| Interfaz MATLAB | Requiere MATLAB y sus componentes gráficos | No ejecutada: MATLAB no está instalado |

La tabla separa la validación matemática de la interfaz. Probar funciones `.m` en Octave no certifica la ejecución de App Designer. Los registros originales se encuentran en `evidencias/pruebas_*.log`; `verificacion.json` conserva los códigos de salida. No se han inventado resultados de ventanas que no pudieron abrirse.

### Capturas de la aplicación C++

Estas imágenes se obtuvieron renderizando los componentes reales de Qt con el backend `offscreen`:

![Interfaz FFT C++](evidencias/cpp_fft.png)

![Interfaz oscilador C++](evidencias/cpp_oscilador.png)

![Interfaz SVD C++](evidencias/cpp_svd.png)

## 6. Reproducción y cierre

Las instrucciones completas están en [README.md](README.md). `python3 ejecutar.py pruebas` compila cuando es necesario, ejecuta las verificaciones y genera las evidencias. `python3 ejecutar.py evidencias` regenera las gráficas usando los datos exportados.

La optimización central consiste en conservar la FFT cuando solo cambia su escala y conservar la SVD cuando solo cambia el rango. Las validaciones evitan actualizar el estado con datos inválidos, y los modelos separados permiten comprobar fórmulas sin depender de una ventana gráfica. Queda por verificar manualmente la ventana Tkinter en una sesión gráfica y la interfaz MATLAB en una instalación de MATLAB.

## Referencias técnicas

- [MathWorks: fft y espectro unilateral](https://www.mathworks.com/help/matlab/ref/fft.html).
- [Streamlit: AppTest para pruebas de aplicaciones](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
- Material base: cinco cuadernos Semana 3 proporcionados por el usuario y planteamiento de Tarea 4.
