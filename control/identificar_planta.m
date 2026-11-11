% Identificacion de la planta con los registros de procesamiento/datos:
%   1) ganancia del actuador F(u) con el barrido de 5 ciclos (masa de 32.5 g a 65 mm, encoder a 0.35 V colgando)
%   2) mgd/I y b/I con las tres oscilaciones libres del brazo solo
close all; clear;
aqui = fileparts(mfilename('fullpath'));
datos = fullfile(aqui, '..', 'procesamiento', 'datos');
figs = fullfile(aqui, 'figuras'); if ~exist(figs, 'dir'), mkdir(figs); end
p = parametros();

%% 1) Ganancia del actuador
B = readtable(fullfile(datos, 'registro_lastre_barrido_20261106_b.csv'));
phi = B.raw * 360/4095;              % grados desde la posicion colgada
cambios = [1; find(diff(B.pwm) ~= 0) + 1; height(B) + 1];
U = []; PHI = []; CIC = [];
ciclo = 1;
for k = 1:numel(cambios) - 1
    idx = cambios(k):cambios(k+1) - 1;
    tt = B.t_s(idx);
    if tt(end) - tt(1) < 4, continue; end
    if B.pwm(idx(1)) == 0 && ~isempty(U), ciclo = ciclo + 1; end
    m = tt > tt(end) - 2;            % ultimos 2 s del escalon: ya asentado
    U(end+1, 1) = B.pwm(idx(1));
    PHI(end+1, 1) = mean(phi(idx(m)));
    CIC(end+1, 1) = ciclo;
end
cero = mean(PHI(U == 0));
mgd2 = p.mgd + 0.0325 * p.g * 0.065;
F = mgd2 * sind(PHI - cero) / p.R;   % equilibrio: F R = mgd2 sin(phi)

sel = U >= 40;
c1 = polyfit(U(sel), F(sel), 1);
c2 = polyfit(U(sel), F(sel), 2);
r2 = 1 - sum((F(sel) - polyval(c1, U(sel))).^2) / sum((F(sel) - mean(F(sel))).^2);
dispersion = zeros(0, 1);
for u = unique(U(sel))', dispersion(end+1) = std(F(U == u)); end
fprintf('Ka = %.4e N/duty, F0 = %.3e N, R2 = %.5f, F(255) = %.1f mN\n', c1(1), c1(2), r2, 1e3*polyval(c1, 255));
fprintf('dispersion entre ciclos: max %.2f mN\n', 1e3*max(dispersion));
fprintf('cuadratico: [%.4e %.4e %.4e]\n', c2);

f = figure('Position', [100 100 900 650]);
subplot(2,1,1);
uu = linspace(0, 255, 200);
colores = lines(max(CIC));
hold on;
for c = 1:max(CIC)
    plot(U(CIC == c), 1e3*F(CIC == c), 'o', 'Color', colores(c,:), 'DisplayName', sprintf('ciclo %d', c));
end
plot(uu, 1e3*polyval(c1, uu), 'k-', 'LineWidth', 1.2, 'DisplayName', sprintf('lineal: %.3f mN/duty', 1e3*c1(1)));
plot(uu, 1e3*polyval(c2, uu), 'r--', 'DisplayName', 'cuadratico');
grid on; xlabel('duty (0-255)'); ylabel('F [mN]'); legend('Location', 'northwest');
title(sprintf('Empuje en equilibrio, F R = m g d sen\\phi  (R^2 = %.4f)', r2));
subplot(2,1,2);
stem(U(sel), 1e3*(F(sel) - polyval(c1, U(sel))), 'filled'); grid on;
xlabel('duty'); ylabel('residuo [mN]'); title('Residuos del ajuste lineal');
exportgraphics(f, fullfile(figs, 'id_01_actuador.png'), 'Resolution', 150);

% tren de pasos: duty aplicado y angulo medido en el tiempo
f = figure('Position', [100 100 1000 550]);
subplot(2,1,1); stairs(B.t_s, B.pwm, 'k', 'LineWidth', 1.1); grid on;
ylabel('u [duty]'); ylim([-10 260]); title('Tren de pasos del barrido (masa de 32.5 g a 65 mm)');
subplot(2,1,2); plot(B.t_s, phi - cero, 'Color', [0.85 0.15 0.15]); grid on;
ylabel('\theta [grados]'); xlabel('t [s]');
exportgraphics(f, fullfile(figs, 'id_03_tren_pasos.png'), 'Resolution', 150);

% angulo de equilibrio frente al duty, medido y predicho con F(u) cuadratica
uu = linspace(0, 255, 300);
thMod = asind(min(1, max(0, polyval(c2, uu)) * p.R / mgd2));
f = figure('Position', [100 100 700 450]); hold on;
for c = 1:max(CIC)
    plot(U(CIC == c), PHI(CIC == c) - cero, 'o', 'Color', colores(c,:), 'DisplayName', sprintf('ciclo %d', c));
end
plot(uu, thMod, 'k-', 'LineWidth', 1.2, 'DisplayName', 'modelo: sen\theta = F(u) R / mgd');
grid on; xlabel('u [duty]'); ylabel('\theta de equilibrio [grados]');
legend('Location', 'northwest'); title('Angulo de equilibrio frente al PWM');
exportgraphics(f, fullfile(figs, 'id_04_angulo_pwm.png'), 'Resolution', 150);

%% 2) Oscilacion libre
ensayos = {'registro_20261105_181117.csv', 1.45;
           'registro_20261105_181139.csv', 2.40;
           'registro_20261105_181203.csv', 6.10};
res = zeros(size(ensayos, 1), 3);
f = figure('Position', [100 100 900 800]);
for k = 1:size(ensayos, 1)
    T = readtable(fullfile(datos, ensayos{k, 1}));
    [t, iu] = unique(T.t_s);
    a = T.raw(iu) * 360/4095;
    m = t >= ensayos{k, 2};
    t = t(m) - t(find(m, 1)); a = a(m);
    eq = mean(a(t > t(end) - 1.5));
    y = deg2rad(a - eq);
    costo = @(x) sum((sim_libre(x, t) - y).^2);
    x = fminsearch(costo, [85 0.5 y(1) 0], optimset('MaxFunEvals', 4000, 'MaxIter', 4000, 'TolX', 1e-6, 'TolFun', 1e-8));
    ys = sim_libre(x, t);
    rms = rad2deg(sqrt(mean((ys - y).^2)));
    res(k, :) = [x(1) x(2) rms];
    fprintf('%s: mgd/I = %.2f 1/s^2, b/I = %.3f 1/s, RMS = %.2f grados\n', ensayos{k, 1}, x(1), x(2), rms);
    subplot(3,1,k);
    plot(t, rad2deg(y), '.', 'Color', [0.6 0.6 0.6]); hold on;
    plot(t, rad2deg(ys), 'b', 'LineWidth', 1.1); grid on;
    ylabel('\phi - \phi_{eq} [grados]');
    title(sprintf('Ensayo %d: mgd/I = %.1f s^{-2}, b/I = %.2f s^{-1}, RMS %.1f°', k, x(1), x(2), rms));
    if k == 1, legend('medido', 'modelo no lineal ajustado'); end
end
xlabel('t [s]');
exportgraphics(f, fullfile(figs, 'id_02_oscilacion_libre.png'), 'Resolution', 150);

w2 = mean(res(:, 1)); a = mean(res(:, 2));
I = p.mgd / w2;
fprintf('\nmedia: mgd/I = %.2f +- %.2f, b/I = %.3f +- %.3f\n', w2, std(res(:,1)), a, std(res(:,2)));
fprintf('con mgd = %.4e N*m: I = %.3e kg*m^2 (CAD %.3e, %+.0f %%), b = %.3e N*m*s\n', ...
    p.mgd, I, p.I_cad, 100*(I/p.I_cad - 1), a*I);
fprintf('kb = Ka R / I = %.2f grados/s^2 por duty\n', c1(1)*p.R/I*180/pi);

%% 3) Ruido del sensor con el motor encendido
s = [];
for k = 1:numel(cambios) - 1
    idx = cambios(k):cambios(k+1) - 1;
    tt = B.t_s(idx);
    if tt(end) - tt(1) < 4 || B.pwm(idx(1)) < 40, continue; end
    s(end+1) = std(phi(idx(tt > tt(end) - 2)));
end
fprintf('desviacion del angulo en reposo con motor: %.2f grados (mediana)\n', median(s));

function y = sim_libre(x, t)
    f = @(~, z) [z(2); -x(1)*sin(z(1)) - x(2)*z(2)];
    [~, z] = ode45(f, t, [x(3) x(4)], odeset('RelTol', 1e-7, 'AbsTol', 1e-9));
    y = z(:, 1);
end
