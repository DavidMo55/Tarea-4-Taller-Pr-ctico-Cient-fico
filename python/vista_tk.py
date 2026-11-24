"""Vista de escritorio: controles y dibujo, sin fórmulas ni FFT."""
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class VistaTk:
    def __init__(self, raiz, variables):
        raiz.title('Tarea 4 · Laboratorio de señales y dinámica')
        raiz.geometry('1160x680'); raiz.minsize(880,560)
        raiz.columnconfigure(0,weight=1); raiz.rowconfigure(0,weight=1)
        tabs=ttk.Notebook(raiz); tabs.grid(row=0,column=0,sticky='nsew',padx=12,pady=12)
        self.tabs=tabs
        self.botones={}; self.figuras={}; self.ejes={}; self.canvas={}
        for clave,titulo,campos in [
            ('oscilador','Oscilador y retrato de fase',[('f','Frecuencia natural (Hz)'),('zeta','Factor ζ'),('v0','Velocidad inicial')]),
            ('fft','Señal y espectro FFT',[('frecuencia','Frecuencia de señal (Hz)'),('fs','Muestreo fs (Hz)'),('duracion','Duración (s)')])]:
            panel=ttk.Frame(tabs,padding=12); tabs.add(panel,text=titulo)
            panel.rowconfigure(1,weight=1); panel.columnconfigure(0,weight=1)
            controles=ttk.Frame(panel); controles.grid(row=0,column=0,sticky='ew',pady=(0,12))
            for j,(campo,etiqueta) in enumerate(campos):
                ttk.Label(controles,text=etiqueta).grid(row=0,column=j*2,sticky='w',padx=(0,5))
                ttk.Entry(controles,textvariable=variables[campo],width=11).grid(row=0,column=j*2+1,padx=(0,14))
            boton=ttk.Button(controles,text='Simular' if clave=='oscilador' else 'Generar y analizar')
            boton.grid(row=0,column=6,padx=6); self.botones[clave]=boton
            fig=Figure(figsize=(10.4,4.6),dpi=100,layout='constrained')
            ax1,ax2=fig.add_subplot(121),fig.add_subplot(122)
            canvas=FigureCanvasTkAgg(fig,master=panel)
            canvas.get_tk_widget().grid(row=1,column=0,sticky='nsew')
            self.figuras[clave]=fig; self.ejes[clave]=(ax1,ax2); self.canvas[clave]=canvas
            pie=ttk.Frame(panel); pie.grid(row=2,column=0,sticky='ew',pady=(12,0))
            if clave=='oscilador':
                self.restablecer=ttk.Button(pie,text='Restablecer Valores Nominales'); self.restablecer.pack(side='left')
            else:
                ttk.Label(pie,text='Escala del espectro:').pack(side='left',padx=(0,8))
                self.escala=ttk.Combobox(pie,textvariable=variables['escala'],values=('Lineal','Semilogarítmica'),state='readonly',width=20)
                self.escala.pack(side='left')
        self.estado=ttk.Label(raiz,text='Listo',padding=(16,6)); self.estado.grid(row=1,column=0,sticky='ew')

    def dibujar_oscilador(self,t,x,v):
        a,b=self.ejes['oscilador']; a.clear(); b.clear()
        a.plot(t,x,color='#146a91'); a.set(title='Respuesta temporal',xlabel='Tiempo (s)',ylabel='Desplazamiento x(t)')
        b.plot(x,v,color='#d16b30'); b.set(title='Retrato de fase',xlabel='Desplazamiento x',ylabel='Velocidad v')
        for ax in (a,b): ax.grid(alpha=.25)
        self.canvas['oscilador'].draw_idle()

    def dibujar_fft(self,estado,escala):
        a,b=self.ejes['fft']; a.clear(); b.clear()
        a.plot(estado.tiempo,estado.senal,color='#146a91',linewidth=.8)
        a.set(title='Ventana inicial (hasta 20 ms)',xlabel='Tiempo (s)',ylabel='Amplitud')
        a.set_xlim(0,min(.02,float(estado.tiempo[-1])))
        f,m=estado.frecuencias,estado.magnitud
        if escala=='Semilogarítmica': b.semilogx(f[1:],m[1:],color='#d16b30')
        else: b.plot(f,m,color='#d16b30')
        b.set(title=f'Espectro unilateral · FFT ejecutadas: {estado.calculos}',xlabel='Frecuencia (Hz)',ylabel='Amplitud normalizada')
        for ax in (a,b): ax.grid(alpha=.25)
        self.canvas['fft'].draw_idle()
