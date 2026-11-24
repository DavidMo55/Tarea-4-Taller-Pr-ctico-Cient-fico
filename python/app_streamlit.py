"""Controlador Top-Down: transiciones de sesión y coordinación del modelo/vista."""
import streamlit as st
from estado import asegurar_svd
from modelo import reconstruir_svd
import vista_streamlit as vista

n=vista.iniciar()
if st.session_state.get('dimension_guardada')!=n or 'factores_svd' not in st.session_state:
    try:
        with st.spinner(f'Calculando la SVD de {n} × {n}…'):
            asegurar_svd(st.session_state,n)
        st.session_state['k']=1
    except Exception as error:
        st.error(f'No fue posible factorizar: {error}'); st.stop()
k=vista.elegir_rango(n)
try:
    factores=st.session_state.factores_svd
    Ak,error,reduccion,bytes_ram=reconstruir_svd(factores,k)
except ValueError as error:
    st.warning(str(error)); st.stop()
vista.dibujar(factores,Ak,k,error,reduccion,bytes_ram,st.session_state.conteo_svd)
