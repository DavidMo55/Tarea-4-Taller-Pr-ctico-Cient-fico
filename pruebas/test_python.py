import sys
from pathlib import Path
import unittest
from unittest.mock import patch,MagicMock
import numpy as np

RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ/'python'))
import modelo
from estado import EstadoFFT,asegurar_svd,preparar_estado_fft


class ModeloTests(unittest.TestCase):
    def test_fft_amplitud_par_impar(self):
        for n in (1000,1001):
            y=2+3*np.sin(2*np.pi*50*np.arange(n)/n)
            f,m=modelo.calcular_espectro_fft(y,n)
            self.assertEqual(len(f),n//2+1)
            self.assertAlmostEqual(m[0],2,places=10)
            self.assertAlmostEqual(m[50],3,places=10)
            self.assertEqual(f[50],50)
        _,m=modelo.calcular_espectro_fft((-1.)**np.arange(1000),1000)
        self.assertAlmostEqual(m[-1],1,places=12)

    def test_nyquist_finito_memoria(self):
        for args in ((500,1000,1),(501,1000,1),(1,float('inf'),1),(0,10000,1),(2,10000,-1),(2,10000,1e9)):
            with self.assertRaises(ValueError): modelo.sintetizar_senal(*args)
        t,y=modelo.sintetizar_senal(440,10000,1)
        self.assertEqual(t.size,10000)
        self.assertAlmostEqual(t[-1],.9999)
        with self.assertRaises(ValueError): modelo.calcular_espectro_fft([0,np.nan],100)

    def test_oscilador_condiciones_y_energia(self):
        for z in (0,.15,.999999999999):
            t,x,v=modelo.evaluar_amortiguamiento(2.5,z,3.2)
            self.assertEqual(x[0],1); self.assertAlmostEqual(v[0],3.2)
            self.assertTrue(np.isfinite(x).all() and np.isfinite(v).all())
            energia=.5*v*v+.5*(2*np.pi*2.5)**2*x*x
            self.assertLessEqual(np.diff(energia).max(),1e-9*energia.max())
            if z==0: np.testing.assert_allclose(energia,energia[0],rtol=1e-12)
        t,x,v=modelo.evaluar_amortiguamiento(2.5,.15,-2)
        aproximacion=np.gradient(x,t)
        self.assertLess(np.max(abs(aproximacion[2:-2]-v[2:-2])),.01)

    def test_dominio_oscilador(self):
        for args in ((0,.1,0),(51,.1,0),(2,1,0),(2,1.2,0),(2,-.1,0),(2,.1,np.nan),(2,.1,1e9)):
            with self.assertRaises(ValueError): modelo.evaluar_amortiguamiento(*args)
        modelo.evaluar_amortiguamiento(50,0,0)

    def test_svd_reconstruccion_y_metricas(self):
        r=modelo.calcular_svd_matriz(40)
        np.testing.assert_allclose((r.U*r.sigma)@r.Vt,r.A,atol=1e-12)
        _,e1,_,_=modelo.reconstruir_svd(r,1)
        Ak,e4,red,bytes_ram=modelo.reconstruir_svd(r,4)
        self.assertLessEqual(e4,e1)
        self.assertAlmostEqual(e4,np.linalg.norm(r.sigma[4:])/np.linalg.norm(r.sigma),places=12)
        self.assertAlmostEqual(red,79.75)
        self.assertEqual(bytes_ram,8*(4*40*40+40))
        self.assertEqual(Ak.shape,(40,40))
        with self.assertRaises(ValueError): modelo.reconstruir_svd(r,5)
        for n in (0,9,1001,10.5,True):
            with self.assertRaises(ValueError): modelo.calcular_svd_matriz(n)

    def test_svd_pura(self):
        np.random.seed(42); antes=np.random.get_state()
        a=modelo.calcular_svd_matriz(20);b=modelo.calcular_svd_matriz(20)
        despues=np.random.get_state()
        np.testing.assert_array_equal(a.A,b.A)
        np.testing.assert_array_equal(antes[1],despues[1])

    def test_cache_fft_y_estado_atomico(self):
        previo=EstadoFFT()
        with patch('numpy.fft.rfft',wraps=np.fft.rfft) as fft:
            nuevo=preparar_estado_fft(previo,440,10000,1)
            igual=preparar_estado_fft(nuevo,440,10000,1)
            self.assertIs(igual,nuevo);self.assertEqual(fft.call_count,1)
            self.assertIsNone(previo.senal)
            with self.assertRaises(ValueError): preparar_estado_fft(nuevo,5000,10000,1)
            self.assertEqual(nuevo.calculos,1)
            tercero=preparar_estado_fft(nuevo,441,10000,1)
            self.assertEqual(tercero.calculos,2)
            self.assertEqual(fft.call_count,2)

    def test_cache_svd_y_error_atomico(self):
        estado={}
        with patch('estado.calcular_svd_matriz',wraps=modelo.calcular_svd_matriz) as svd:
            asegurar_svd(estado,40); original=estado['factores_svd']
            modelo.reconstruir_svd(original,1);modelo.reconstruir_svd(original,4)
            asegurar_svd(estado,40)
            self.assertEqual(svd.call_count,1);self.assertEqual(estado['conteo_svd'],1)
            with patch('estado.calcular_svd_matriz',side_effect=ValueError('fallo simulado')):
                with self.assertRaises(ValueError): asegurar_svd(estado,50)
            self.assertIs(estado['factores_svd'],original)
            self.assertEqual(estado['dimension_guardada'],40)
            asegurar_svd(estado,50);self.assertEqual(estado['conteo_svd'],2)

    def test_controlador_tk_restauracion_y_alerta(self):
        import tkinter as tk
        from controlador_tk import AplicacionTkinterDemo
        # Tcl real para DoubleVar; vista sustituida para no requerir WindowServer.
        interprete=tk.Tcl(); app=AplicacionTkinterDemo.__new__(AplicacionTkinterDemo)
        app.raiz=None; app.vista=MagicMock(); app.resultado_oscilador=None
        app.var_frecuencia=tk.DoubleVar(master=interprete,value=8)
        app.var_zeta=tk.DoubleVar(master=interprete,value=.5)
        app.var_velocidad_inicial=tk.DoubleVar(master=interprete,value=3)
        app.restablecer()
        self.assertEqual((app.var_frecuencia.get(),app.var_zeta.get(),app.var_velocidad_inicial.get()),(2.5,.15,0))
        app.vista.dibujar_oscilador.assert_called_once()
        anterior=app.resultado_oscilador;app.var_zeta.set(1)
        with patch('controlador_tk.messagebox.showwarning') as alerta:
            app.simular();alerta.assert_called_once()
        self.assertIs(app.resultado_oscilador,anterior)


if __name__=='__main__': unittest.main(verbosity=2)
