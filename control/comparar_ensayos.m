% Repetibilidad: los dos ensayos de la secuencia completa superpuestos, angulo y senal de control.
close all; clear;
aqui = fileparts(mfilename('fullpath'));
datos = fullfile(aqui, '..', 'procesamiento', 'datos');
figs = fullfile(aqui, 'figuras');
archivos = {'pid_escalones150_20261106_124411.csv', 'pid_escalones150_20261106_124828.csv'};
colores = [0.85 0.15 0.15; 0.1 0.45 0.8];

f = figure('Position', [100 100 1000 800]);
Y = cell(1, 2); U = Y;
for k = 1:2
    T = readtable(fullfile(datos, archivos{k}), 'CommentStyle', '#');
    t = (T.t_ms - T.t_ms(1)) / 1000;
    Y{k} = T.theta; U{k} = T.u;
    subplot(3,1,1); plot(t, T.theta, 'Color', colores(k,:)); hold on;
    subplot(3,1,2); plot(t, T.u, 'Color', colores(k,:)); hold on;
end
n = min(numel(Y{1}), numel(Y{2}));
subplot(3,1,1); stairs(t(1:n), T.ref(1:n), 'k--'); grid on; ylabel('\theta [grados]');
legend('ensayo 1', 'ensayo 2', 'referencia', 'Location', 'southeast');
title('Repetibilidad: dos corridas de la secuencia completa');
subplot(3,1,2); grid on; ylabel('u [duty]'); ylim([-5 140]);
subplot(3,1,3); plot(t(1:n), Y{1}(1:n) - Y{2}(1:n), 'Color', [0.3 0.3 0.3]); grid on;
ylabel('\theta_1 - \theta_2 [grados]'); xlabel('t [s]');
exportgraphics(f, fullfile(figs, 'exp_repetibilidad.png'), 'Resolution', 150);

d = Y{1}(1:n) - Y{2}(1:n);
r = T.ref(1:n);
fprintf('diferencia entre ensayos: RMS %.2f grados; RMS sin el tramo de 150: %.2f grados\n', ...
    rms(d), rms(d(r ~= 150)));
fprintf('diferencia de u en regimen: RMS %.1f duty\n', rms(U{1}(1:n) - U{2}(1:n)));
