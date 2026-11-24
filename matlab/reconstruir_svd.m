function [Ak,errorRel,reduccion,bytesRAM]=reconstruir_svd(A,U,s,Vt,k)
n=size(A,1); validar_finito(k,'Rango');
if k~=fix(k) || k<1 || k>floor(n/10), error('Tarea4:Rango','Se requiere 1 <= k <= floor(n/10).'); end
Ak=bsxfun(@times,U(:,1:k),s(1:k).')*Vt(1:k,:);
norma=norm(A,'fro');
if norma==0, errorRel=0; else, errorRel=norm(A-Ak,'fro')/norma; end
reduccion=100*(1-(2*n*k+k)/(n*n));
bytesRAM=8*(numel(A)+numel(U)+numel(s)+numel(Vt)+numel(Ak));
end
