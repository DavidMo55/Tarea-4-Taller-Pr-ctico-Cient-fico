function [A,U,s,Vt]=calcular_svd_matriz(n)
validar_finito(n,'Dimensión');
if n~=fix(n) || n<10 || n>1000, error('Tarea4:Dimension','n debe ser entero entre 10 y 1000.'); end
% Preservar el RNG del llamador: función determinista sin alterar su estado.
previo=rng; limpieza=onCleanup(@() rng(previo));
rng(2026+n,'twister'); A=randn(n,n);
[U,S,V]=svd(A,'econ'); s=diag(S); Vt=V';
end
