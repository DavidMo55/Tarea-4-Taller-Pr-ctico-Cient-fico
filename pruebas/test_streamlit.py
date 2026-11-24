from pathlib import Path
import sys
from unittest.mock import patch
RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ/'python'))
from streamlit.testing.v1 import AppTest
import modelo

with patch('estado.calcular_svd_matriz',wraps=modelo.calcular_svd_matriz) as modelo_pesado:
    app=AppTest.from_file(str(RAIZ/'python/app_streamlit.py'),default_timeout=60).run()
    assert not app.exception
    assert len(app.metric)==3 and app.metric[2].value=='1'
    factores=app.session_state['factores_svd']
    app.slider[0].set_value(7).run()
    assert not app.exception and app.metric[2].value=='1'
    assert app.session_state['factores_svd'] is factores
    assert modelo_pesado.call_count==1
    app.selectbox[0].set_value(250).run()
    assert not app.exception and app.metric[2].value=='2'
    assert app.slider[0].value==1 and app.slider[0].max==25
    assert modelo_pesado.call_count==2
    app.slider[0].set_value(25).run()
    assert not app.exception and app.metric[2].value=='2'
    app.selectbox[0].set_value(100).run()
    assert not app.exception and app.metric[2].value=='3'
    assert app.slider[0].value==1 and modelo_pesado.call_count==3
print('PRUEBAS STREAMLIT: 5 ejecuciones Top-Down; mover k no repite SVD; cambiar n sí; límites de k correctos.')
