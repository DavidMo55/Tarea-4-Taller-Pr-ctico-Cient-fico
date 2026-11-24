"""Lanzadores de Tarea4. No necesita dependencias para seleccionar un entorno."""
from pathlib import Path
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

RAIZ=Path(__file__).resolve().parent


def configuracion():
    archivo=RAIZ/'runtime_local.json'
    c=json.loads(archivo.read_text()) if archivo.exists() else {}
    env=os.environ.copy()
    paquetes=[p for p in c.get('python_packages',[]) if Path(p).exists()]
    if paquetes: env['PYTHONPATH']=os.pathsep.join(paquetes+[env.get('PYTHONPATH','')])
    env['MPLCONFIGDIR']=str(RAIZ/'.cache/matplotlib')
    python=os.environ.get('TAREA4_PYTHON',c.get('python',sys.executable))
    octave=os.environ.get('TAREA4_OCTAVE',c.get('octave',shutil.which('octave-cli') or 'octave'))
    if Path(octave).exists(): env['OCTAVE_HOME']=str(Path(octave).parent.parent)
    env['OCTAVE_IMAGE_PATH']=str(RAIZ/'matlab')
    if c.get('qt_prefix'):
        env['QT_PLUGIN_PATH']=str(Path(c['qt_prefix'])/'plugins')
        env['QT_QPA_FONTDIR']=str(Path(c['qt_prefix'])/'share/fonts')
    return c,env,python,octave


def compilar(c):
    destino=RAIZ/'cpp/build';destino.mkdir(exist_ok=True)
    binario=destino/'laboratorio'
    fuentes=[*list((RAIZ/'cpp').glob('*.cpp')),*list((RAIZ/'cpp').glob('*.hpp'))]
    if binario.exists() and binario.stat().st_mtime>=max(p.stat().st_mtime for p in fuentes): return binario
    qt=c.get('qt_prefix');eigen=c.get('eigen')
    if qt and eigen and sys.platform=='darwin':
        qt=Path(qt)
        cmd=['c++','-std=c++17','-O2','-fPIC','-mmacosx-version-min=11.0','-I',eigen]
        for inc in ('','QtWidgets','QtGui','QtCore'): cmd+=['-I',str(qt/'include/qt'/inc)]
        cmd += [str(RAIZ/'cpp/main.cpp'),'-L',str(qt/'lib'),'-lQt5Widgets','-lQt5Gui','-lQt5Core',
                '-Wl,-rpath,'+str(qt/'lib'),'-o',str(binario)]
        subprocess.run(cmd,check=True)
    else:
        subprocess.run(['cmake','-S',str(RAIZ/'cpp'),'-B',str(destino)],check=True)
        subprocess.run(['cmake','--build',str(destino),'--config','Release'],check=True)
    return binario


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('accion',choices=['pruebas','tkinter','streamlit','cpp','matlab','evidencias'])
    args=p.parse_args();c,env,python,octave=configuracion()
    if args.accion=='tkinter':
        subprocess.run([python,str(RAIZ/'python/app_tk.py')],env=env,check=True)
    elif args.accion=='streamlit':
        subprocess.run([python,'-m','streamlit','run',str(RAIZ/'python/app_streamlit.py'),
                        '--server.address=127.0.0.1','--server.port=8504','--browser.gatherUsageStats=false'],env=env,check=True)
    elif args.accion=='cpp':
        subprocess.run([str(compilar(c))],env=env,check=True)
    elif args.accion=='matlab':
        matlab=os.environ.get('TAREA4_MATLAB',shutil.which('matlab') or '')
        if not matlab: raise SystemExit('La interfaz JerarquiaPOO requiere MATLAB. Abre matlab/JerarquiaPOO.m en MATLAB y ejecuta app = JerarquiaPOO; Octave solo ejecuta los modelos numéricos.')
        ruta=str(RAIZ/'matlab').replace("'","''")
        subprocess.run([matlab,'-r',f"addpath('{ruta}'); app=JerarquiaPOO;"],check=True)
    elif args.accion=='evidencias':
        subprocess.run([python,str(RAIZ/'pruebas/generar_evidencias.py')],env=env,check=True)
    else:
        out=RAIZ/'evidencias';out.mkdir(exist_ok=True)
        etapas=[('python',[python,str(RAIZ/'pruebas/test_python.py')]),
                ('streamlit',[python,str(RAIZ/'pruebas/test_streamlit.py')])]
        resultados=[]
        for nombre,cmd in etapas:
            print('Probando',nombre,flush=True)
            r=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            (out/f'pruebas_{nombre}.log').write_text(r.stdout)
            resultados.append({'prueba':nombre,'exit_code':r.returncode})
            if r.returncode: print(r.stdout);raise SystemExit(r.returncode)
        print('Compilando y probando C++',flush=True);exe=compilar(c)
        for nombre,cmd in [('cpp_modelo',[str(exe),'--test']),('cpp_interfaz',[str(exe),'--test-ui',str(out)])]:
            local=env.copy()
            if nombre=='cpp_interfaz': local['QT_QPA_PLATFORM']='offscreen'
            r=subprocess.run(cmd,env=local,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            (out/f'pruebas_{nombre}.log').write_text(r.stdout)
            resultados.append({'prueba':nombre,'exit_code':r.returncode})
            if r.returncode: print(r.stdout);raise SystemExit(r.returncode)
        print('Probando funciones MATLAB con GNU Octave (sin App Designer)',flush=True)
        ruta=str(RAIZ/'matlab').replace("'","''");salida=str(out).replace("'","''")
        r=subprocess.run([octave,'--no-init-file','--no-site-file','--no-history','--quiet','--eval',
                          f"addpath('{ruta}'); pruebas_modelo('{salida}');"],env=env,
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (out/'pruebas_matlab_octave.log').write_text(r.stdout)
        resultados.append({'prueba':'modelos_matlab_en_octave','exit_code':r.returncode})
        if r.returncode: print(r.stdout);raise SystemExit(r.returncode)
        (out/'verificacion.json').write_text(json.dumps({'sistema':platform.platform(),'pruebas':resultados,
            'interfaz_matlab':'No ejecutada: MATLAB no está instalado.',
            'interfaz_tk':'Controlador probado con Tcl y vista simulada; apertura nativa pendiente.'},ensure_ascii=False,indent=2))
        subprocess.run([python,str(RAIZ/'pruebas/generar_evidencias.py')],env=env,check=True)
        print('Todas las pruebas disponibles pasaron. Consulta evidencias/verificacion.json.',flush=True)


if __name__=='__main__': main()
