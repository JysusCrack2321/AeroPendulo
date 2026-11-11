% Simulacion no lineal de los ensayos que se hacen en el banco, con el controlador discreto
% tal como esta en el firmware (Ts = 10 ms, anti-windup, PWM entero 0-255), F(u) medida,
% ruido y cuantizacion del AS5600.
close all; clear;
aqui = fileparts(mfilename('fullpath'));
figs = fullfile(aqui, 'figuras'); if ~exist(figs, 'dir'), mkdir(figs); end
guardar = @(f, nombre) exportgraphics(f, fullfile(figs, nombre), 'Resolution', 150);
p = parametros();

tc = [0 cumsum(p.sec_dur)];
refSec = @(t) p.sec_ref(min(numel(p.sec_ref), find(t >= tc, 1, 'last')));
Tfin = tc(end) - p.Ts;

%% Secuencia de escalones
sim = simular_pid(p, refSec, Tfin);
M = metricas_escalones(sim.t, sim.r, sim.y, sim.u);
disp('Simulacion no lineal, secuencia del firmware:'); disp(M);
writetable(M, fullfile(aqui, 'metricas_simulacion.csv'));

f = figure('Position', [100 100 1000 800]);
subplot(3,1,1);
plot(sim.t, sim.y, 'Color', [0.85 0.2 0.2]); hold on;
stairs(sim.t, sim.r, 'k--', 'LineWidth', 1.1);
grid on; ylabel('\theta [grados]'); legend('simulacion', 'referencia', 'Location', 'southeast');
title('Simulacion no lineal de la secuencia de escalones');
subplot(3,1,2);
plot(sim.t, sim.u, 'k'); grid on; ylabel('u [duty]'); ylim([-5 260]);
subplot(3,1,3);
plot(sim.t, sim.r - sim.y, 'Color', [0.3 0.3 0.3]); grid on; ylabel('e [grados]'); xlabel('t [s]');
guardar(f, 'sim_01_escalones.png');

%% Cada escalon superpuesto, normalizado
f = figure('Position', [100 100 800 500]); hold on;
ini = [1; find(diff(sim.r) ~= 0) + 1];
for k = 1:numel(ini)
    idx = ini(k):min(ini(k) + round(8/p.Ts), numel(sim.t));
    plot(sim.t(idx) - sim.t(ini(k)), (sim.y(idx) - M.desde(k)) / M.delta(k), ...
        'DisplayName', sprintf('%+.0f° (%.0f -> %.0f)', M.delta(k), M.desde(k), M.hasta(k)));
end
yline(1.15, 'r--', 'HandleVisibility', 'off'); yline([0.98 1.02], 'k:', 'HandleVisibility', 'off');
grid on; legend('Location', 'southeast'); xlabel('t desde el escalon [s]'); ylabel('(\theta - \theta_{ini}) / \Delta');
title('Escalones normalizados (simulacion no lineal)');
guardar(f, 'sim_02_escalones_normalizados.png');

%% Perturbacion: pulsos de par como el secador (desde arriba y desde abajo)
pert = @(t) 3e-3*((t > 8 & t < 11) - (t > 18 & t < 21)) + 3e-3*(t > 28 & t < 28.3);
per = simular_pid(p, @(t) 90, 36, struct('pert', pert));
f = figure('Position', [100 100 1000 700]);
subplot(3,1,1); plot(per.t, per.y, 'Color', [0.85 0.2 0.2]); hold on; yline(90, 'k--');
grid on; ylabel('\theta [grados]'); title('Rechazo de perturbaciones en \theta = 90° (simulacion)');
subplot(3,1,2); plot(per.t, per.u, 'k'); grid on; ylabel('u [duty]');
subplot(3,1,3); plot(per.t, 1e3*arrayfun(pert, per.t), 'm', 'LineWidth', 1.2); grid on;
ylabel('\tau_d [mN·m]'); xlabel('t [s]');
guardar(f, 'sim_03_perturbacion.png');

%% Robustez: masa anadida (moneda de 3.34 g) y planta con la inercia del CAD, hasta 120 grados
% (a 150 grados la planta nominal ya queda en el limite de Routh)
refRob = [45 90 105 120 105 90 45];
tcRob = [0 cumsum(10*ones(size(refRob)))];
refSecRob = @(t) refRob(min(numel(refRob), find(t >= tcRob, 1, 'last')));
TfinRob = tcRob(end) - p.Ts;
casos = {struct(), 'nominal';
         struct('m_extra', 3.34e-3, 'r_extra', 0.065), 'moneda 3.34 g a 65 mm';
         struct('fI', p.I_cad/p.I), 'I del CAD (+16 %)';
         struct('fKa', 0.8), 'K_a - 20 %'};
f = figure('Position', [100 100 1000 700]);
for k = 1:size(casos, 1)
    sk = simular_pid(p, refSecRob, TfinRob, casos{k, 1});
    Mk = metricas_escalones(sk.t, sk.r, sk.y, sk.u);
    fprintf('%-24s Mp max %5.1f %%  ts max %5.2f s  |ess| max %.2f°  u_ss en 90°: %.0f\n', casos{k, 2}, ...
        max(Mk.Mp_pct), max(Mk.ts_s), max(abs(Mk.ess_grados)), Mk.u_ss(2));
    subplot(2,1,1); plot(sk.t, sk.y, 'DisplayName', casos{k, 2}); hold on;
    subplot(2,1,2); plot(sk.t, sk.u, 'DisplayName', casos{k, 2}); hold on;
end
subplot(2,1,1); stairs(sk.t, sk.r, 'k--', 'DisplayName', 'referencia'); grid on; ylabel('\theta [grados]');
legend('Location', 'southeast'); title('Robustez frente a cambios de la planta (simulacion)');
subplot(2,1,2); grid on; ylabel('u [duty]'); xlabel('t [s]');
guardar(f, 'sim_04_robustez.png');
