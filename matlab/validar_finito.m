function validar_finito(x,nombre)
if ~isnumeric(x) || ~isscalar(x) || ~isreal(x) || ~isfinite(x)
    error('Tarea4:Entrada','%s debe ser un número real finito.',nombre);
end
end
