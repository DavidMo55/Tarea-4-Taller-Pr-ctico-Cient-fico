function pruebas_modelo(carpeta)
if nargin<1, carpeta=pwd; end
for n=[1000 1001]
    y=2+3*sin(2*pi*50*(0:n-1)/n);
    [f,m]=calcular_espectro_fft(y,n);
    assert(numel(f)==floor(n/2)+1 && abs(m(1)-2)<1e-10 && abs(m(51)-3)<1e-10 && f(51)==50);
end
[~,m]=calcular_espectro_fft((-1).^(0:999),1000);assert(abs(m(end)-1)<1e-12);
for z=[0 .15 .999999999999]
    [t,x,v]=evaluar_amortiguamiento(2.5,z,3.2);
    assert(x(1)==1 && abs(v(1)-3.2)<1e-12 && all(isfinite(x)) && all(isfinite(v)));
    E=.5*v.^2+.5*(2*pi*2.5)^2*x.^2;
    assert(max(diff(E))<1e-9*max(E));
end
rechazar(@() sintetizar_senal(500,1000,1));
rechazar(@() sintetizar_senal(1,Inf,1));
rechazar(@() evaluar_amortiguamiento(2,1,0));
rechazar(@() evaluar_amortiguamiento(51,.1,0));
rechazar(@() evaluar_amortiguamiento(2,.1,NaN));
[A,U,s,Vt]=calcular_svd_matriz(40);
assert(norm(A-U*diag(s)*Vt,'fro')/norm(A,'fro')<1e-12);
[~,e1]=reconstruir_svd(A,U,s,Vt,1);
[Ak,e4,red,bytes]=reconstruir_svd(A,U,s,Vt,4);
assert(e4<=e1 && abs(e4-norm(s(5:end))/norm(s))<1e-12);
assert(abs(red-79.75)<1e-12 && bytes==8*(4*40*40+40));
rechazar(@() reconstruir_svd(A,U,s,Vt,5));
rng(42); previo=rng; calcular_svd_matriz(20); assert(isequal(rng,previo));
[t,x,v]=evaluar_amortiguamiento(7.3,.22,-1.2,1.3);
dlwrite(fullfile(carpeta,'oscilador_matlab_octave.csv'),[t(:),x(:),v(:)]);
[t,y]=sintetizar_senal(440,10000,1);[f,m]=calcular_espectro_fft(y,10000);
dlwrite(fullfile(carpeta,'fft_matlab_octave.csv'),[f(:),m(:)]);
fprintf('PRUEBAS MODELO MATLAB/Octave: FFT par/impar, Nyquist, oscilador, dominio, SVD y RNG correctos.\n');
end
function rechazar(f)
rechazado=false;
try, f(); catch, rechazado=true; end
assert(rechazado,'Se aceptó una entrada inválida.');
end
function dlwrite(ruta,datos)
fid=fopen(ruta,'w'); limpieza=onCleanup(@() fclose(fid));
formato=[repmat('%.17g,',1,size(datos,2)-1),'%.17g\n'];fprintf(fid,formato,datos.');
end
