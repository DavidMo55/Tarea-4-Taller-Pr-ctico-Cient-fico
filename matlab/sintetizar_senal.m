function [t,y]=sintetizar_senal(f,fs,duracion)
validar_finito(f,'Frecuencia'); validar_finito(fs,'Muestreo'); validar_finito(duracion,'Duración');
if f<=0 || fs<=0 || duracion<=0, error('Tarea4:Entrada','Los parámetros deben ser positivos.'); end
if fs<=2*f, error('Tarea4:Nyquist','Nyquist: fs debe ser estrictamente mayor que 2*f.'); end
cantidad=fs*duracion;
if ~isfinite(cantidad) || cantidad<2 || cantidad>1e6
    error('Tarea4:Memoria','La señal debe contener entre 2 y 1 000 000 de muestras.');
end
n=round(cantidad); t=(0:n-1)/fs; y=sin(2*pi*f*t);
end
