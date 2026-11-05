% Carga el registro_*.csv mas reciente de esta carpeta y grafica el angulo.
% Uso: octave --persist cargar_angulo.m   (o desde dentro de octave: cargar_angulo)

carpeta = fileparts(mfilename('fullpath'));
archivos = dir(fullfile(carpeta, 'registro_*.csv'));

if isempty(archivos)
  error('No hay archivos registro_*.csv en %s', carpeta);
end

[~, idx] = max([archivos.datenum]);
archivo = fullfile(archivos(idx).folder, archivos(idx).name);

datos = dlmread(archivo, ',', 1, 0);   % salta la cabecera
t = datos(:, 1) / 1000;                % ms -> s
ang = datos(:, 2);

fprintf('Archivo: %s\n', archivo);
fprintf('Muestras: %d   Duracion: %.2f s   dt medio: %.1f ms\n', ...
        rows(datos), t(end) - t(1), 1000 * mean(diff(t)));

figure;
plot(t, ang, '.');
grid on;
xlabel('t [s]');
ylabel('angulo [grados]');
title(strrep(archivos(idx).name, '_', '\_'));
