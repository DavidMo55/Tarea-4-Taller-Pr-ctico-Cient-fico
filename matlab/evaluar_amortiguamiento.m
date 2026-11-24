function [t,x,v]=evaluar_amortiguamiento(f,zeta,v0,x0)
if nargin<4, x0=1; end
validar_finito(f,'Frecuencia natural'); validar_finito(zeta,'Zeta');
validar_finito(v0,'Velocidad inicial'); validar_finito(x0,'Desplazamiento inicial');
if f<=0 || f>50, error('Tarea4:Dominio','Se requiere 0 < f <= 50 Hz.'); end
if zeta<0 || zeta>=1, error('Tarea4:Dominio','Solo régimen subamortiguado: 0 <= zeta < 1.'); end
if abs(v0)>1e6 || abs(x0)>1e6, error('Tarea4:Dominio','Condiciones iniciales fuera de rango.'); end
t=linspace(0,5,2000); wn=2*pi*f; a=zeta*wn; wd=wn*sqrt((1-zeta)*(1+zeta));
u=wd*t; sinc_estable=ones(size(u)); mascara=abs(u)>1e-8;
sinc_estable(mascara)=sin(u(mascara))./u(mascara);
sinc_estable(~mascara)=1-u(~mascara).^2/6;
seno_sobre_wd=t.*sinc_estable; envolvente=exp(-a*t); c=cos(u);
x=envolvente.*(x0*c+(v0+a*x0)*seno_sobre_wd);
v=envolvente.*(v0*c-(wn^2*x0+a*v0)*seno_sobre_wd);
if any(~isfinite(x)) || any(~isfinite(v)), error('Tarea4:Numerico','Resultado no finito.'); end
end
