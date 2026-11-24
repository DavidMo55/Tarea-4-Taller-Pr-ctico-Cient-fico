# Tarea 4 — Señales, oscilador y compresión SVD

Solución en **Python, MATLAB y C++** de las actividades proporcionadas. Incluye interfaces, modelos numéricos, persistencia de resultados en RAM, validaciones, pruebas y evidencias. El procedimiento y los resultados se explican en [REPORTE.md](REPORTE.md).

## Abrir y ejecutar en VS Code

Abre la carpeta `/Users/salieri/Documents/Tareas/Tarea4` con **Archivo → Abrir carpeta**. Abre una terminal dentro de ella y ejecuta una de estas opciones:

```sh
python3 ejecutar.py tkinter
python3 ejecutar.py streamlit
python3 ejecutar.py cpp
python3 ejecutar.py pruebas
```

Ejecuta cada aplicación por separado. Streamlit muestra la dirección local `http://127.0.0.1:8504`; Ctrl+C detiene su servidor. También hay tareas en **Terminal → Ejecutar tarea**; la tarea de compilación predeterminada ejecuta las pruebas.

Para MATLAB, abre su aplicación, cambia a la subcarpeta `matlab` y escribe:

```matlab
app = JerarquiaPOO;
```

Si `matlab` está disponible en la terminal, puedes usar `python3 ejecutar.py matlab`. Es una interfaz programática con `uifigure`, `uigridlayout`, pestañas y `uiaxes`; el archivo fuente es `.m`, no `.mlapp`.

**Estado de ejecución:** Python y C++ fueron probados; la interfaz C++ se renderizó con Qt en modo sin pantalla. El controlador Tkinter se probó con variables Tcl y una vista simulada; falta comprobar la ventana nativa en una sesión gráfica. Las funciones numéricas `.m` se probaron con **GNU Octave 10.3**. MATLAB no está instalado en este entorno: su interfaz requiere MATLAB y no se ha ejecutado. Octave no sustituye App Designer.

## Contenido

| Carpeta o archivo | Función |
|---|---|
| `python/modelo.py` | FFT, solución del oscilador y SVD, sin interfaz gráfica |
| `python/estado.py` | Cachés de FFT/SVD y contadores |
| `python/app_tk.py` | Entrada de la aplicación Tkinter de FFT y oscilador |
| `python/app_streamlit.py` | Controlador del explorador SVD |
| `python/vista_*.py`, `controlador_tk.py` | Vistas y controlador de escritorio |
| `matlab/JerarquiaPOO.m` | Aplicación MATLAB con las tres actividades |
| `matlab/*.m` | Funciones numéricas y pruebas independientes |
| `cpp/models.hpp`, `view.hpp`, `controller.hpp` | Separación MVC de la aplicación Qt |
| `cpp/main.cpp`, `CMakeLists.txt` | Entrada, pruebas y compilación |
| `pruebas/` | Pruebas Python, Streamlit y generación de evidencias |
| `evidencias/` | Registros, resultados numéricos y gráficas |

## Dependencias y portabilidad

`runtime_local.json` selecciona las dependencias ya disponibles en este equipo. Sus rutas apuntan al entorno de trabajo de Codex; no borres ese entorno si deseas seguir usándolas. El binario C++ incluido está compilado para este Mac y usa sus bibliotecas Qt locales.

Para trasladar el proyecto, retira esa configuración local y prepara Python 3.10 o posterior con Tkinter y las dependencias:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python ejecutar.py tkinter
python ejecutar.py streamlit
```

Para C++ necesitas compilador C++17, CMake, Eigen 3.4 y Qt Widgets 5 o 6. Se verificó con Qt 5.15.15. Compilación portable:

```sh
cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build cpp/build --config Release
./cpp/build/laboratorio
```

CMake debe poder localizar Eigen y Qt; configura `CMAKE_PREFIX_PATH` si están en una ubicación no estándar. El lanzador local utiliza compilación directa en este Mac. La batería completa `pruebas` también necesita Octave; se puede indicar su ruta con `TAREA4_OCTAVE`. MATLAB requiere soporte para `uigridlayout`.

## Comprobación interactiva para clase

1. FFT: genera 440 Hz con muestreo de 10000 Hz. Cambia la escala lineal/logarítmica: el contador no debe aumentar. Introduce un muestreo de 880 Hz: debe rechazarse porque se exige desigualdad estricta.
2. Oscilador: cambia la velocidad inicial a 3 y observa el retrato de fase. Intenta amortiguamiento 1 o frecuencia 51 Hz: debe mostrarse una advertencia. Restablece los valores nominales: 2.5 Hz, amortiguamiento 0.15 y velocidad inicial 0.
3. SVD: con dimensión 100, mueve el rango de 1 a 7: el contador permanece en 1. Cambia la dimensión a 250: pasa a 2 y el rango vuelve a 1. Los factores anteriores se reemplazan; regresar a 100 provoca una nueva SVD.
