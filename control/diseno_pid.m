% Diseno del PID del aeropendulo a partir del modelo identificado.
%   I th'' = F(u) R - m g d sin(th) - b th'      th en grados desde colgado
% Linealizado en th0 con la ganancia incremental del actuador k(th0) = F'(u0) R / I:
%   G(s) = k(th0) / (s^2 + a s + w2 cos(th0))
% PID: u = Kp (beta r - y) + Ki/s (r - y) - Kd s/(Tf s + 1) y
close all; clear;
aqui = fileparts(mfilename('fullpath'));
figs = fullfile(aqui, 'figuras'); if ~exist(figs, 'dir'), mkdir(figs); end
guardar = @(f, nombre) exportgraphics(f, fullfile(figs, nombre), 'Resolution', 150);
p = parametros();
s = tf('s');
fid = fopen(fullfile(aqui, 'resultados_diseno.txt'), 'w');
out = @(varargin) [fprintf(varargin{:}), fprintf(fid, varargin{:})];

%% 1) Punto de operacion y ganancia incremental del actuador
ths = 0:1:155;
u0 = zeros(size(ths)); kinc = u0;
for k = 1:numel(ths)
    F0 = p.mgd * sind(ths(k)) / p.R;
    c = p.Fcuad; c(3) = c(3) - F0;
    rr = roots(c); rr = rr(imag(rr) == 0 & rr >= 0 & rr <= 400);
    u0(k) = min(rr);
    kinc(k) = (2*p.Fcuad(1)*u0(k) + p.Fcuad(2)) * p.R / p.I * 180/pi;
end
kb = @(th) interp1(ths, kinc, th);
out('Planta: mgd/I = %.1f 1/s^2, b/I = %.2f 1/s, kb lineal = %.1f grados/s^2 por duty\n', p.w2, p.a, p.kb);
for th = [0 45 90 120 135 150]
    pol = roots([1 p.a p.w2*cosd(th)]);
    out('  th0 = %3d: u0 = %5.1f duty, k(th0) = %5.1f, polos de G: %s\n', th, interp1(ths, u0, th), kb(th), mat2str(round(pol.', 2)));
end

f = figure('Position', [100 100 1000 420]);
subplot(1,2,1);
yyaxis left; plot(ths, u0, 'LineWidth', 1.3); ylabel('u_0 [duty]');
yyaxis right; plot(ths, kinc, 'LineWidth', 1.3); hold on; yline(p.kb, ':'); ylabel('k(\theta_0) [°/s^2 por duty]');
grid on; xlabel('\theta_0 [grados]'); title('Punto de operacion y ganancia incremental');
subplot(1,2,2); hold on;
for th = 0:15:150
    pol = roots([1 p.a p.w2*cosd(th)]);
    plot(real(pol), imag(pol), 'o', 'Color', [th/150 0.3 1-th/150], 'MarkerFaceColor', [th/150 0.3 1-th/150]);
end
xline(0, 'k:'); grid on; xlabel('Re'); ylabel('Im');
title('Polos de G(s) de 0° (azul) a 150° (rojo)');
guardar(f, 'dis_01_planta.png');

%% 2) Diseno por lugar de las raices
% El PID con filtro se escribe como ganancia por dos ceros sobre un polo en el origen:
%   C(s) = K (s + z1)(s + z2) / (s (Tf s + 1))
% Se fijan los ceros y el filtro, se dibuja el lugar de las raices en K para cada angulo
% y se elige K. Kp, Ki y Kd salen de desarrollar C(s).
z1 = 1.4;          % cero lento: lo pone la integral
z2 = 3.2;          % cero rapido: lo pone la derivada
K  = 0.22;
B = (s + z1)*(s + z2) / (s*(p.Tf*s + 1));
planta = @(th) kb(th) / (s^2 + p.a*s + p.w2*cosd(th));

Ki_ = K*z1*z2;
Kp_ = K*(z1 + z2) - Ki_*p.Tf;
Kd_ = K - Kp_*p.Tf;
out('\nLugar de las raices: C(s) = K (s + %.1f)(s + %.1f) / (s (%.2f s + 1)), K = %.2f\n', z1, z2, p.Tf, K);
out('  desarrollando: Kd + Kp Tf = K,  Kp + Ki Tf = K (z1 + z2),  Ki = K z1 z2\n');
out('  -> Kp = %.3f, Ki = %.3f, Kd = %.3f  (se redondean a %.1f, %.1f, %.2f)\n', Kp_, Ki_, Kd_, p.Kp, p.Ki, p.Kd);

f = figure('Position', [100 100 1000 820]);
angRL = [45 90 135 150];
for k = 1:4
    th = angRL(k);
    Lk = B * planta(th);
    subplot(2,2,k);
    rlocus(Lk, linspace(0, 1.5, 1500)); hold on;
    pc = pole(feedback(K*Lk, 1));
    plot(real(pc), imag(pc), 'rs', 'MarkerSize', 9, 'LineWidth', 1.5);
    xlim([-25 12]); ylim([-25 25]); grid on;
    pg = pole(planta(th));
    title(sprintf('\\theta_0 = %d°: polos de G en %s', th, mat2str(round(pg.', 1))));
end
guardar(f, 'dis_02_lugar_raices.png');

% rango de K estable en cada angulo
thsK = 0:5:155;
Ks = logspace(-2.5, 0.5, 300);
Kmin = nan(size(thsK)); Kmax = Kmin;
for k = 1:numel(thsK)
    Lk = B * planta(thsK(k));
    ok = arrayfun(@(KK) all(real(pole(feedback(KK*Lk, 1))) < 0), Ks);
    if any(ok), Kmin(k) = Ks(find(ok, 1)); Kmax(k) = Ks(find(ok, 1, 'last')); end
end
thLim = thsK(find(Kmin <= K, 1, 'last'));
for th = [45 90 120 135]
    Lk = B * planta(th);
    zmin = arrayfun(@(KK) min(-real(pole(feedback(KK*Lk, 1))) ./ abs(pole(feedback(KK*Lk, 1)))), [0.15 0.22 0.3 0.4 0.6]);
    out('  th0 = %3d: zeta minimo con K = 0.15/0.22/0.30/0.40/0.60: %s\n', th, mat2str(round(zmin, 2)));
end
out('  rango estable de K: en 90° %.3f..%.2f, en 135° %.3f..%.2f, en 150° %.3f..%.2f\n', ...
    Kmin(thsK == 90), Kmax(thsK == 90), Kmin(thsK == 135), Kmax(thsK == 135), Kmin(thsK == 150), Kmax(thsK == 150));
out('  con K = %.2f el lazo es estable hasta %d grados\n', K, thLim);

% amortiguamiento del polo dominante en funcion de K
Kz = linspace(0.02, 1, 300);
f = figure('Position', [100 100 1000 420]);
subplot(1,2,1);
semilogy(thsK, Kmin, 'b', thsK, Kmax, 'r', 'LineWidth', 1.4); hold on;
yline(K, 'k--', sprintf('K = %.2f', K), 'LineWidth', 1.2);
grid on; xlabel('\theta_0 [grados]'); ylabel('K');
legend('K minimo estable', 'K maximo estable', 'Location', 'northwest');
title('Rango de K que estabiliza el lazo');
subplot(1,2,2); hold on;
for th = [45 90 120 135]
    Lk = B * planta(th);
    zd = zeros(size(Kz));
    for k = 1:numel(Kz)
        pc = pole(feedback(Kz(k)*Lk, 1)); pc = pc(abs(pc) < 40);
        zd(k) = min(-real(pc) ./ abs(pc));
    end
    plot(Kz, zd, 'LineWidth', 1.3, 'DisplayName', sprintf('\\theta_0 = %d°', th));
end
xline(K, 'k--', 'HandleVisibility', 'off'); yline(0, 'k:', 'HandleVisibility', 'off');
grid on; xlabel('K'); ylabel('\zeta minimo de los polos'); ylim([-0.3 1.05]);
legend('Location', 'southeast'); title('Peor amortiguamiento de lazo cerrado');
guardar(f, 'dis_03_eleccion_K.png');

%% 5) Controlador final (ganancias redondeadas)
C = p.Kp + p.Ki/s + p.Kd*s/(p.Tf*s + 1);
out('\nPID: Kp = %.2f, Ki = %.2f, Kd = %.2f, Tf = %.3f s (polo del filtro en %.0f rad/s), beta = %.1f, Ts = %.0f ms\n', ...
    p.Kp, p.Ki, p.Kd, p.Tf, 1/p.Tf, p.beta, 1e3*p.Ts);

%% 6) Lazo C G: polos, margenes y Bode
ang = [0 45 90 120 135 150];
f = figure('Position', [100 100 1000 650]);
out('\nLazo abierto C G:\n');
out('   th0   MF[°]  wc[rad/s]  MG sup[dB]  MG inf[dB]   polo dominante\n');
for k = 1:numel(ang)
    G = kb(ang(k)) / (s^2 + p.a*s + p.w2*cosd(ang(k)));
    L = C * G;
    m = allmargin(L);
    [Pm, i] = min(m.PhaseMargin); Wcp = m.PMFrequency(i);
    gm = m.GainMargin;
    gsup = min([gm(gm > 1), Inf]); ginf = max([gm(gm < 1), 0]);
    T = feedback(C * G, 1);
    pc = pole(T); [~, i] = max(real(pc));
    out('  %4d  %6.1f  %8.2f  %10.1f  %10.1f   %s\n', ang(k), Pm, Wcp, 20*log10(gsup), 20*log10(ginf), num2str(pc(i), '%.2f'));
    bode(L, {0.1, 300}); hold on;
end
grid on; legend(arrayfun(@(x) sprintf('\\theta_0 = %d°', x), ang, 'UniformOutput', false), 'Location', 'southwest');
title('Bode de C(s)G(s)');
guardar(f, 'dis_05_bode.png');

f = figure('Position', [100 100 700 500]); hold on;
for th = 0:5:150
    G = kb(th) / (s^2 + p.a*s + p.w2*cosd(th));
    pc = pole(feedback(C * G, 1));
    pc = pc(abs(pc) < 40);
    plot(real(pc), imag(pc), '.', 'Color', [th/150 0.3 1-th/150], 'MarkerSize', 12);
end
xline(0, 'k:'); grid on; xlabel('Re'); ylabel('Im');
title('Polos de lazo cerrado de 0° (azul) a 150° (rojo)');
guardar(f, 'dis_06_polos_lazo_cerrado.png');

%% 7) Respuesta lineal al escalon y efecto de beta
f = figure('Position', [100 100 1000 650]);
t = (0:0.005:10)';
estilos = {'-', '--'};
for k = 1:numel(ang) - 1
    th = ang(k + 1);
    G = kb(th) / (s^2 + p.a*s + p.w2*cosd(th));
    for b = [0 1]
        Cr = b*p.Kp + p.Ki/s;
        Cy = p.Kp + p.Ki/s + p.Kd*s/(p.Tf*s + 1);
        T = minreal(Cr * G / (1 + Cy * G));
        U = minreal(Cr / (1 + Cy * G));
        y = step(T, t); uu = step(U, t);
        subplot(2,1,1); plot(t, y, 'Color', [th/150 0.3 1-th/150], 'LineStyle', estilos{b + 1}, ...
            'DisplayName', sprintf('%d°, \\beta = %d', th, b)); hold on;
        subplot(2,1,2); plot(t, uu, 'Color', [th/150 0.3 1-th/150], 'LineStyle', estilos{b + 1}, ...
            'HandleVisibility', 'off'); hold on;
        S = stepinfo(y, t);
        out('  escalon lineal en %3d°, beta %d: Mp = %5.1f %%, ts = %.2f s, u pico/escalon = %.1f duty/grado\n', ...
            th, b, S.Overshoot, S.SettlingTime, max(abs(uu)));
    end
end
subplot(2,1,1); yline(1, 'k:', 'HandleVisibility', 'off'); grid on; ylabel('\theta / \Deltar');
legend('Location', 'eastoutside'); title('Escalon unitario lineal: \beta = 0 (continua) y \beta = 1 (discontinua)');
subplot(2,1,2); grid on; ylabel('u / \Deltar [duty/grado]'); xlabel('t [s]');
guardar(f, 'dis_07_escalon_beta.png');
%% 9) Nyquist: arriba de 90 grados G tiene un polo inestable y el lazo debe rodear -1 una vez antihorario
f = figure('Position', [100 100 1000 420]);
out('\nNyquist (P = polos inestables de lazo abierto, Z = de lazo cerrado):\n');
for k = 1:2
    th = [45 135]; th = th(k);
    G = kb(th) / (s^2 + p.a*s + p.w2*cosd(th));
    L = C * G;
    w = logspace(-2, 3, 4000);
    h = squeeze(freqresp(L, w));
    subplot(1,2,k);
    plot(real(h), imag(h), 'b', real(h), -imag(h), 'b--'); hold on;
    plot(-1, 0, 'r+', 'MarkerSize', 12, 'LineWidth', 2);
    th1 = linspace(0, 2*pi, 100); plot(-1 + cos(th1), sin(th1), 'r:');
    axis equal; xlim([-4 2]); ylim([-3 3]); grid on;
    P = sum(real(pole(L)) > 0); Z = sum(real(pole(feedback(L, 1))) > 0);
    title(sprintf('\\theta_0 = %d°: P = %d, Z = %d', th, P, Z));
    out('  th0 = %3d: P = %d, Z = %d\n', th, P, Z);
end
guardar(f, 'dis_09_nyquist.png');

%% 10) Funciones de sensibilidad
f = figure('Position', [100 100 1000 420]);
w = logspace(-1, 2.5, 600);
out('\nSensibilidades:\n');
colS = [0 0.45 0.74; 0.47 0.67 0.19; 0.93 0.6 0.1; 0.8 0.1 0.15];
angS = [45 90 120 135];
for kS = 1:4
    th = angS(kS);
    G = kb(th) / (s^2 + p.a*s + p.w2*cosd(th));
    L = C * G;
    S = feedback(1, L); T = feedback(L, 1);
    Sm = squeeze(abs(freqresp(S, w))); Tm = squeeze(abs(freqresp(T, w)));
    subplot(1,2,1); semilogx(w, 20*log10(Sm), 'Color', colS(kS,:), 'LineWidth', 1.4, 'DisplayName', sprintf('%d°', th)); hold on;
    subplot(1,2,2); semilogx(w, 20*log10(Tm), 'Color', colS(kS,:), 'LineWidth', 1.4, 'DisplayName', sprintf('%d°', th)); hold on;
    out('  th0 = %3d: Ms = %.2f (%.1f dB), Mt = %.2f\n', th, max(Sm), 20*log10(max(Sm)), max(Tm));
end
subplot(1,2,1); yline(20*log10(2), 'k:', 'M_s = 2', 'HandleVisibility', 'off'); grid on;
xlabel('\omega [rad/s]'); ylabel('|S| [dB]'); title('Sensibilidad S = 1/(1+CG)'); legend('Location', 'southeast');
subplot(1,2,2); yline(0, 'k:', 'HandleVisibility', 'off'); grid on; xlabel('\omega [rad/s]'); ylabel('|T| [dB]');
title('Complementaria T = CG/(1+CG)'); legend('Location', 'southwest');
guardar(f, 'dis_10_sensibilidades.png');

%% 11) Discreto (Tustin, Ts = 10 ms) frente a continuo
f = figure('Position', [100 100 1000 420]);
Cd = c2d(C, p.Ts, 'tustin');
out('\nDiscreto frente a continuo (escalon lineal, beta = 1):\n');
for k = 1:2
    th = [90 120]; th = th(k);
    G = kb(th) / (s^2 + p.a*s + p.w2*cosd(th));
    Tc = feedback(C * G, 1);
    Td = feedback(Cd * c2d(G, p.Ts, 'zoh'), 1);
    [yc, tc] = step(Tc, 6); [yd, td] = step(Td, 6);
    subplot(1,2,k); plot(tc, yc, 'b', 'LineWidth', 1.2); hold on; stairs(td, yd, 'r');
    grid on; xlabel('t [s]'); ylabel('\theta / \Deltar'); legend('continuo', 'discreto', 'Location', 'southeast');
    Sc = stepinfo(yc, tc); Sd = stepinfo(yd, td);
    title(sprintf('\\theta_0 = %d°: M_p %.0f %% / %.0f %%', th, Sc.Overshoot, Sd.Overshoot));
    out('  th0 = %3d: Mp continuo %.1f %%, discreto %.1f %%\n', th, Sc.Overshoot, Sd.Overshoot);
end
guardar(f, 'dis_11_discreto.png');

%% 12) Monte Carlo: Ka +-20 %, I +0..25 %, b +-50 %, th0 en [0, 135]
rng(2);
N = 200; inest = 0;
f = figure('Position', [100 100 1000 420]);
subplot(1,2,1); hold on;
MS = zeros(N, 1);
for k = 1:N
    fKa = 1 + 0.4*(rand - 0.5); fI = 1 + 0.25*rand; fb = 1 + (rand - 0.5); th = 135*rand;
    I = p.I * fI;
    kk = kb(th) * fKa / fI;
    G = kk / (s^2 + fb*p.a/fI*s + p.w2/fI*cosd(th));
    L = C * G;
    T = feedback(L, 1);
    if any(real(pole(T)) >= 0), inest = inest + 1; continue; end
    MS(k) = max(abs(squeeze(freqresp(feedback(1, L), logspace(-1, 2.5, 300)))));
    [y, t] = step(minreal(G * p.Ki/s / (1 + C*G)), 10);
    plot(t, y, 'Color', [th/135 0.3 1-th/135 0.4]);
end
grid on; xlabel('t [s]'); ylabel('\theta / \Deltar'); yline(1, 'k:');
title(sprintf('%d plantas: K_a \\pm20 %%, I +0..25 %%, b \\pm50 %%, \\theta_0 0..135° (inestables: %d)', N, inest));
subplot(1,2,2); histogram(MS(MS > 0), 20); grid on; xlabel('M_s'); ylabel('plantas');
title(sprintf('Pico de sensibilidad: mediana %.2f, max %.2f', median(MS(MS > 0)), max(MS)));
out('\nMonte Carlo: %d plantas, %d inestables, Ms mediana %.2f, max %.2f\n', N, inest, median(MS(MS > 0)), max(MS));
guardar(f, 'dis_12_montecarlo.png');
fclose(fid);
