"""Vista web: controles, métricas y figuras; no factoriza ni reconstruye matrices."""
import streamlit as st
from matplotlib.figure import Figure


def iniciar():
    st.set_page_config(page_title='Tarea 4 · Compresión SVD',layout='wide')
    st.title('Explorador de compresión espectral')
    st.caption('Elige la dimensión para factorizar; modifica k para reutilizar los factores guardados en tu sesión.')
    return st.sidebar.selectbox('Dimensión n × n',[100,250,500,1000],index=0,key='n')


def elegir_rango(n):
    return st.sidebar.slider('Rango de aproximación k',min_value=1,max_value=n//10,key='k')


def dibujar(factores,Ak,k,error,reduccion,bytes_ram,conteo):
    n=factores.A.shape[0]
    c1,c2,c3=st.columns(3)
    c1.metric('Error relativo de Frobenius',f'{error:.4f}')
    c2.metric('Reducción de almacenamiento',f'{reduccion:.2f}%')
    c3.metric('Ejecuciones de la SVD',conteo)
    st.caption(f'Reducción calculada para almacenar solo Uₖ, σₖ y Vᵀₖ. '
               f'Los arreglos A, U, σ, Vᵀ y Aₖ usados por la app suman {bytes_ram/2**20:.2f} MiB; '
               'la aplicación conserva los factores completos para permitir interacción.')
    fig=Figure(figsize=(10,4.6),layout='constrained'); ax=fig.add_subplot(111)
    ax.semilogy(range(1,n+1),factores.sigma,color='#146a91')
    ax.axvline(k,color='#d16b30',linestyle='--',label=f'Corte k={k}')
    ax.set(title='Decaimiento de valores singulares',xlabel='Índice del valor singular',ylabel='Valor singular (escala logarítmica)')
    ax.grid(alpha=.25); ax.legend(); st.pyplot(fig)
    st.caption('Una matriz aleatoria densa puede mantener un error alto con k ≤ n/10: reducir almacenamiento no garantiza buena fidelidad.')
    with st.expander('Ver la matriz original y su aproximación'):
        fig2=Figure(figsize=(10,4),layout='constrained')
        a,b=fig2.add_subplot(121),fig2.add_subplot(122)
        limite=float(abs(factores.A).max())
        a.imshow(factores.A,cmap='coolwarm',vmin=-limite,vmax=limite); a.set_title('A original')
        im=b.imshow(Ak,cmap='coolwarm',vmin=-limite,vmax=limite); b.set_title(f'Aₖ · rango {k}')
        fig2.colorbar(im,ax=[a,b],shrink=.8); st.pyplot(fig2)
