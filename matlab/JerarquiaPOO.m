classdef JerarquiaPOO < handle
    % App programática con componentes de App Designer. Requiere MATLAB.
    % Los modelos de los archivos auxiliares también se prueban en GNU Octave.
    properties (Access = private)
        UIFigure
        CampoFrecuencia
        CampoMuestreo
        CampoDuracion
        Escala
        EjeTiempo
        EjeEspectro
        EtiquetaFFT
        SenalGenerada = []
        TiempoGenerado = []
        FrecuenciaMuestreo = 10000
        VectorFrecuencias = []
        MagnitudEspectro = []
        ParametrosFFT = []
        ConteoFFT = 0
        CampoNatural
        CampoZeta
        CampoVelocidad
        EjeRespuesta
        EjeFase
        Dimension
        Rango
        EjeSVD
        MetricasSVD
        MatrizOriginal = []
        U = []
        Sigma = []
        Vt = []
        DimensionGuardada = 0
        ConteoSVD = 0
    end
    methods
        function app=JerarquiaPOO()
            app.crearVista();
            app.generarSenal();
            app.simularOscilador();
            app.cambiarDimension();
        end
        function delete(app)
            if ~isempty(app.UIFigure) && isvalid(app.UIFigure), delete(app.UIFigure); end
        end
    end
    methods (Access = private)
        function crearVista(app)
            app.UIFigure=uifigure('Name','Tarea 4 | Laboratorio MVC','Position',[80 80 1180 740]);
            app.UIFigure.CloseRequestFcn=@(~,~) delete(app);
            raiz=uigridlayout(app.UIFigure,[1 1]);
            tabs=uitabgroup(raiz);
            % Actividad 1: contenedores relativos a UIFigure mediante grid.
            tab=uitab(tabs,'Title','Señal y FFT'); g=uigridlayout(tab,[3 1]);
            g.RowHeight={92,'1x',34};
            c=uigridlayout(g,[2 5]);
            uilabel(c,'Text','Frecuencia de señal (Hz)'); uilabel(c,'Text','Muestreo fs (Hz)');
            uilabel(c,'Text','Duración (s)'); uilabel(c,'Text','Escala del espectro'); uilabel(c,'Text','');
            app.CampoFrecuencia=uieditfield(c,'numeric','Value',440);
            app.CampoMuestreo=uieditfield(c,'numeric','Value',10000);
            app.CampoDuracion=uieditfield(c,'numeric','Value',1);
            app.Escala=uidropdown(c,'Items',{'Lineal','Semilogarítmica'},'ValueChangedFcn',@(~,~) app.redibujarEspectro());
            uibutton(c,'Text','Generar y analizar','ButtonPushedFcn',@(~,~) app.generarSenal());
            e=uigridlayout(g,[1 2]); app.EjeTiempo=uiaxes(e); app.EjeEspectro=uiaxes(e);
            app.EtiquetaFFT=uilabel(g,'Text','FFT ejecutadas: 0');
            % Equivalente de la actividad 2: condición inicial y espacio de fases.
            tab=uitab(tabs,'Title','Oscilador'); g=uigridlayout(tab,[2 1]); g.RowHeight={92,'1x'};
            c=uigridlayout(g,[2 5]);
            uilabel(c,'Text','Frecuencia natural (Hz)'); uilabel(c,'Text','Factor zeta');
            uilabel(c,'Text','Velocidad inicial'); uilabel(c,'Text',''); uilabel(c,'Text','');
            app.CampoNatural=uieditfield(c,'numeric','Value',2.5);
            app.CampoZeta=uieditfield(c,'numeric','Value',.15);
            app.CampoVelocidad=uieditfield(c,'numeric','Value',0);
            uibutton(c,'Text','Simular','ButtonPushedFcn',@(~,~) app.simularOscilador());
            uibutton(c,'Text','Restablecer nominales','ButtonPushedFcn',@(~,~) app.restablecer());
            e=uigridlayout(g,[1 2]); app.EjeRespuesta=uiaxes(e); app.EjeFase=uiaxes(e);
            % Equivalente de la actividad 3: factores residentes y rango secundario.
            tab=uitab(tabs,'Title','Compresión SVD'); g=uigridlayout(tab,[3 1]); g.RowHeight={110,70,'1x'};
            c=uigridlayout(g,[2 2]); c.ColumnWidth={180,'1x'};
            uilabel(c,'Text','Dimensión n'); uilabel(c,'Text','Rango k (1 a n/10)');
            app.Dimension=uidropdown(c,'Items',{'100','250','500','1000'},'ValueChangedFcn',@(~,~) app.cambiarDimension());
            app.Rango=uislider(c,'Limits',[1 10],'Value',1,'ValueChangedFcn',@(~,~) app.actualizarRango());
            app.MetricasSVD=uilabel(g,'Text','Sin factores','WordWrap','on');
            app.EjeSVD=uiaxes(g);
        end

        function [f,m]=calcularEspectroFFT(app)
            % Modelo auxiliar puro: solo lee la señal y el fs guardados.
            % No toca gráficos, etiquetas ni controles de la vista.
            [f,m]=calcular_espectro_fft(app.SenalGenerada,app.FrecuenciaMuestreo);
        end

        function generarSenal(app)
            progreso=[];
            anterior={app.SenalGenerada,app.TiempoGenerado,app.FrecuenciaMuestreo,app.VectorFrecuencias,app.MagnitudEspectro,app.ParametrosFFT,app.ConteoFFT};
            try
                f=app.CampoFrecuencia.Value; fs=app.CampoMuestreo.Value; d=app.CampoDuracion.Value;
                % Validación exigida dentro del try del controlador.
                if fs<=2*f, error('Tarea4:Nyquist','Nyquist: fs debe ser estrictamente mayor que 2*f.'); end
                if isequal(app.ParametrosFFT,[f fs d]), app.redibujarEspectro(); return; end
                progreso=uiprogressdlg(app.UIFigure,'Title','Procesando señal','Message','Generación y FFT…','Indeterminate','on');
                drawnow;
                [t,y]=sintetizar_senal(f,fs,d);
                app.SenalGenerada=y; app.TiempoGenerado=t; app.FrecuenciaMuestreo=fs;
                [freq,mag]=app.calcularEspectroFFT();
                app.VectorFrecuencias=freq; app.MagnitudEspectro=mag;
                app.ParametrosFFT=[f fs d]; app.ConteoFFT=app.ConteoFFT+1;
                plot(app.EjeTiempo,t,y); title(app.EjeTiempo,'Ventana inicial (hasta 20 ms)'); xlim(app.EjeTiempo,[0 min(.02,t(end))]);
                xlabel(app.EjeTiempo,'Tiempo (s)'); ylabel(app.EjeTiempo,'Amplitud'); grid(app.EjeTiempo,'on');
                app.redibujarEspectro();
            catch errorDetectado
                app.SenalGenerada=anterior{1}; app.TiempoGenerado=anterior{2}; app.FrecuenciaMuestreo=anterior{3};
                app.VectorFrecuencias=anterior{4}; app.MagnitudEspectro=anterior{5};
                app.ParametrosFFT=anterior{6}; app.ConteoFFT=anterior{7};
                if ~isempty(progreso) && isvalid(progreso), close(progreso); progreso=[]; end
                uialert(app.UIFigure,errorDetectado.message,'No se pudo generar la señal','Icon','warning');
            end
            if ~isempty(progreso) && isvalid(progreso), close(progreso); end
        end

        function redibujarEspectro(app)
            if isempty(app.VectorFrecuencias), return; end
            % Solo caché: no se ejecuta fft ni calcularEspectroFFT aquí.
            f=app.VectorFrecuencias; m=app.MagnitudEspectro;
            cla(app.EjeEspectro);
            if strcmp(app.Escala.Value,'Semilogarítmica')
                semilogx(app.EjeEspectro,f(2:end),m(2:end));
            else
                plot(app.EjeEspectro,f,m); app.EjeEspectro.XScale='linear';
            end
            title(app.EjeEspectro,'Espectro unilateral'); xlabel(app.EjeEspectro,'Frecuencia (Hz)');
            ylabel(app.EjeEspectro,'Amplitud normalizada'); grid(app.EjeEspectro,'on');
            app.EtiquetaFFT.Text=sprintf('FFT ejecutadas: %d | Cambiar la escala solo redibuja la caché. DC no se dibuja en escala logarítmica.',app.ConteoFFT);
        end

        function simularOscilador(app)
            try
                [t,x,v]=evaluar_amortiguamiento(app.CampoNatural.Value,app.CampoZeta.Value,app.CampoVelocidad.Value);
                plot(app.EjeRespuesta,t,x); title(app.EjeRespuesta,'Respuesta temporal');
                xlabel(app.EjeRespuesta,'Tiempo (s)'); ylabel(app.EjeRespuesta,'x(t)'); grid(app.EjeRespuesta,'on');
                plot(app.EjeFase,x,v); title(app.EjeFase,'Retrato de fase');
                xlabel(app.EjeFase,'Desplazamiento x'); ylabel(app.EjeFase,'Velocidad v'); grid(app.EjeFase,'on');
            catch errorDetectado
                uialert(app.UIFigure,errorDetectado.message,'Dominio físico inválido','Icon','warning');
            end
        end
        function restablecer(app)
            app.CampoNatural.Value=2.5; app.CampoZeta.Value=.15; app.CampoVelocidad.Value=0;
            app.simularOscilador();
        end

        function cambiarDimension(app)
            n=str2double(app.Dimension.Value);
            if n==app.DimensionGuardada, app.actualizarRango(); return; end
            progreso=uiprogressdlg(app.UIFigure,'Title','Factorizando','Message','Calculando SVD…','Indeterminate','on');
            limpieza=onCleanup(@() close(progreso)); drawnow;
            try
                [A,U,s,Vt]=calcular_svd_matriz(n);
                app.MatrizOriginal=A; app.U=U; app.Sigma=s; app.Vt=Vt;
                app.DimensionGuardada=n; app.ConteoSVD=app.ConteoSVD+1;
                app.Rango.Value=1; app.Rango.Limits=[1 floor(n/10)];
                app.actualizarRango();
            catch errorDetectado
                if app.DimensionGuardada>0, app.Dimension.Value=num2str(app.DimensionGuardada); end
                uialert(app.UIFigure,errorDetectado.message,'Error SVD');
            end
        end
        function actualizarRango(app)
            if isempty(app.Sigma), return; end
            try
                k=max(1,min(floor(app.DimensionGuardada/10),round(app.Rango.Value))); app.Rango.Value=k;
                [~,err,red,bytes]=reconstruir_svd(app.MatrizOriginal,app.U,app.Sigma,app.Vt,k);
                app.MetricasSVD.Text=sprintf('Error Frobenius: %.4f | Reducción de almacenamiento: %.2f%% | Ejecuciones SVD: %d\nArreglos de la sesión con A_k: %.2f MiB. La reducción es teórica para los factores truncados.',err,red,app.ConteoSVD,bytes/2^20);
                semilogy(app.EjeSVD,1:numel(app.Sigma),app.Sigma); hold(app.EjeSVD,'on');
                xline(app.EjeSVD,k,'--'); hold(app.EjeSVD,'off');
                title(app.EjeSVD,'Decaimiento de valores singulares'); xlabel(app.EjeSVD,'Índice');
                ylabel(app.EjeSVD,'Valor singular'); grid(app.EjeSVD,'on');
            catch errorDetectado
                uialert(app.UIFigure,errorDetectado.message,'Rango inválido');
            end
        end
    end
end
