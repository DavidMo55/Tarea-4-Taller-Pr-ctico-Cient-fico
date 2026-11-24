function [frecuencias,magnitud]=calcular_espectro_fft(senal,fs)
% Modelo puro; sin referencias a figuras, ejes ni diálogos.
validar_finito(fs,'Muestreo');
if fs<=0 || ~isnumeric(senal) || ~isreal(senal) || ~isvector(senal) || numel(senal)<2 || any(~isfinite(senal(:)))
    error('Tarea4:FFT','Se requiere señal vectorial real y finita, y fs positivo.');
end
senal=senal(:).'; n=numel(senal); transformada=fft(senal);
magnitud=abs(transformada(1:floor(n/2)+1))/n;
if mod(n,2)==0, magnitud(2:end-1)=2*magnitud(2:end-1);
else, magnitud(2:end)=2*magnitud(2:end); end
frecuencias=(0:floor(n/2))*fs/n;
end
