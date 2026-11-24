"""Controlador: validación, eventos y transiciones de estado."""
import tkinter as tk
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor
from modelo import evaluar_amortiguamiento
from estado import EstadoFFT, preparar_estado_fft
from vista_tk import VistaTk


class AplicacionTkinterDemo:
    def __init__(self, raiz):
        self.raiz=raiz
        self.var_frecuencia=tk.DoubleVar(value=2.5)
        self.var_zeta=tk.DoubleVar(value=.15)
        self.var_velocidad_inicial=tk.DoubleVar(value=0.0)
        self.variables={'f':self.var_frecuencia,'zeta':self.var_zeta,'v0':self.var_velocidad_inicial,
                        'frecuencia':tk.DoubleVar(value=440),'fs':tk.DoubleVar(value=10000),
                        'duracion':tk.DoubleVar(value=1),'escala':tk.StringVar(value='Lineal')}
        self.estado_fft=EstadoFFT(); self.resultado_oscilador=None
        self.vista=VistaTk(raiz,self.variables)
        self.pool=ThreadPoolExecutor(max_workers=1); self.pendiente=None; self.cerrada=False
        self.vista.botones['oscilador'].configure(command=self.simular)
        self.vista.botones['fft'].configure(command=self.generar)
        self.vista.restablecer.configure(command=self.restablecer)
        self.vista.escala.bind('<<ComboboxSelected>>',self.redibujar_fft)
        raiz.protocol('WM_DELETE_WINDOW',self.cerrar)
        self.simular()

    def simular(self):
        try:
            resultado=evaluar_amortiguamiento(self.var_frecuencia.get(),self.var_zeta.get(),self.var_velocidad_inicial.get())
            self.resultado_oscilador=resultado
            self.vista.dibujar_oscilador(*resultado)
            self.vista.estado.configure(text='Simulación válida · 2 000 muestras · x(0)=1')
        except (ValueError,tk.TclError) as error:
            messagebox.showwarning('Parámetros fuera de dominio',str(error),parent=self.raiz)

    def restablecer(self):
        # La restauración de controles usa exclusivamente .set(); no manipula Entry.
        self.var_frecuencia.set(2.5)
        self.var_zeta.set(.15)
        self.var_velocidad_inicial.set(0.0)
        self.simular()

    def generar(self):
        if self.pendiente is not None: return
        try:
            valores=tuple(self.variables[k].get() for k in ('frecuencia','fs','duracion'))
        except (tk.TclError,ValueError) as error:
            messagebox.showwarning('Entrada inválida',str(error),parent=self.raiz); return
        self.vista.botones['fft'].state(['disabled'])
        self.vista.estado.configure(text='Calculando señal y FFT…')
        # El trabajador no toca widgets. Los resultados se dibujan en el hilo de Tk.
        self.pendiente=self.pool.submit(preparar_estado_fft,self.estado_fft,*valores)
        self.raiz.after(25,self.recoger)

    def recoger(self):
        if self.cerrada: return
        if not self.pendiente.done():
            self.raiz.after(25,self.recoger); return
        try:
            self.estado_fft=self.pendiente.result()
            self.redibujar_fft()
            self.vista.estado.configure(text='Espectro guardado en RAM; cambiar escala no recalcula la FFT.')
        except Exception as error:
            messagebox.showwarning('No se pudo generar la señal',str(error),parent=self.raiz)
        finally:
            self.pendiente=None
            self.vista.botones['fft'].state(['!disabled'])

    def redibujar_fft(self,event=None):
        if self.estado_fft.frecuencias is not None:
            self.vista.dibujar_fft(self.estado_fft,self.variables['escala'].get())

    def cerrar(self):
        self.cerrada=True
        self.pool.shutdown(wait=False,cancel_futures=True)
        self.raiz.destroy()
