% Construye aeropendulo_pid.slx: PID discreto (bloque PID Controller (2DOF)) + planta no lineal
%   I th'' = F(u) R - m g d sin(th) - b th'
% con F(u) cuadratica medida, saturacion 0-255, ruido y cuantizacion del encoder.
% Los parametros salen de parametros.m (PreLoadFcn del modelo).
close all; clear;
aqui = fileparts(mfilename('fullpath'));
mdl = 'aeropendulo_pid';
if bdIsLoaded(mdl), close_system(mdl, 0); end
archivo = fullfile(aqui, [mdl '.slx']);
if isfile(archivo), delete(archivo); end
new_system(mdl);
set_param(mdl, 'PreLoadFcn', 'p = parametros();', 'StopTime', 'sum(p.sec_dur) - p.Ts', ...
    'Solver', 'ode45', 'MaxStep', '1e-3', 'SaveOutput', 'on');
p = parametros(); assignin('base', 'p', p);

pos = @(x, y, w, h) [x, y, x + w, y + h];

% referencia: secuencia de escalones del firmware
add_block('simulink/Sources/Repeating Sequence Stair', [mdl '/Referencia'], ...
    'OutValues', 'p.sec_ref', 'tsamp', 'p.sec_dur(1)', 'Position', pos(30, 100, 60, 40));

% PID discreto: P sobre (b r - y), I sobre e, D filtrada sobre (c r - y) con c = 0
add_block('simulink/Continuous/PID Controller (2DOF)', [mdl '/PID'], ...
    'Controller', 'PID', 'Form', 'Parallel', 'TimeDomain', 'Discrete-time', 'SampleTime', 'p.Ts', ...
    'P', 'p.Kp', 'I', 'p.Ki', 'D', 'p.Kd', 'N', '1/p.Tf', 'b', 'p.beta', 'c', '0', ...
    'IntegratorMethod', 'Trapezoidal', 'FilterMethod', 'Trapezoidal', ...
    'LimitOutput', 'on', 'UpperSaturationLimit', 'p.u_max', 'LowerSaturationLimit', '0', ...
    'AntiWindupMode', 'clamping', 'Position', pos(170, 90, 90, 70));

% duty entero, como el PWM de 8 bits
add_block('simulink/Math Operations/Rounding Function', [mdl '/PWM entero'], ...
    'Operator', 'round', 'Position', pos(300, 105, 50, 40));

% planta no lineal
pl = [mdl '/Planta'];
add_block('simulink/Ports & Subsystems/Subsystem', pl, 'Position', pos(400, 110, 130, 50));
delete_line(pl, 'In1/1', 'Out1/1'); delete_block([pl '/In1']); delete_block([pl '/Out1']);
add_block('simulink/Sources/In1', [pl '/u'], 'Position', pos(20, 60, 30, 14));
add_block('simulink/Math Operations/Polynomial', [pl '/Empuje F(u)'], 'coefs', 'p.Fcuad', 'Position', pos(80, 50, 70, 34));
add_block('simulink/Discontinuities/Saturation', [pl '/F >= 0'], 'UpperLimit', 'inf', 'LowerLimit', '0', 'Position', pos(175, 50, 40, 34));
add_block('simulink/Math Operations/Gain', [pl '/R'], 'Gain', 'p.R', 'Position', pos(250, 40, 40, 34));
add_block('simulink/Math Operations/Sum', [pl '/Suma de pares'], 'Inputs', '+--', 'IconShape', 'rectangular', ...
    'Position', pos(330, 35, 30, 90));
add_block('simulink/Math Operations/Gain', [pl '/Inversa de I'], 'Gain', '1/p.I', 'Position', pos(390, 50, 40, 34));
add_block('simulink/Continuous/Integrator', [pl '/omega'], 'Position', pos(460, 50, 34, 34));
add_block('simulink/Continuous/Integrator', [pl '/theta'], 'Position', pos(540, 50, 34, 34));
add_block('simulink/Math Operations/Trigonometric Function', [pl '/sin'], 'Operator', 'sin', ...
    'Position', pos(470, 130, 40, 30), 'Orientation', 'left');
add_block('simulink/Math Operations/Gain', [pl '/mgd'], 'Gain', 'p.mgd', 'Position', pos(390, 130, 50, 30), 'Orientation', 'left');
add_block('simulink/Math Operations/Gain', [pl '/b'], 'Gain', 'p.b', 'Position', pos(400, 180, 60, 30), 'Orientation', 'left');
add_block('simulink/Math Operations/Gain', [pl '/a grados'], 'Gain', '180/pi', 'Position', pos(620, 50, 50, 34));
add_block('simulink/Sinks/Out1', [pl '/theta [grados]'], 'Position', pos(710, 60, 30, 14));
add_line(pl, 'u/1', 'Empuje F(u)/1');
add_line(pl, 'Empuje F(u)/1', 'F >= 0/1');
add_line(pl, 'F >= 0/1', 'R/1');
add_line(pl, 'R/1', 'Suma de pares/1');
add_line(pl, 'Suma de pares/1', 'Inversa de I/1');
add_line(pl, 'Inversa de I/1', 'omega/1');
add_line(pl, 'omega/1', 'theta/1');
add_line(pl, 'theta/1', 'a grados/1');
add_line(pl, 'a grados/1', 'theta [grados]/1');
add_line(pl, 'theta/1', 'sin/1', 'autorouting', 'on');
add_line(pl, 'sin/1', 'mgd/1');
add_line(pl, 'mgd/1', 'Suma de pares/2', 'autorouting', 'on');
add_line(pl, 'omega/1', 'b/1', 'autorouting', 'on');
add_line(pl, 'b/1', 'Suma de pares/3', 'autorouting', 'on');

% encoder: ruido medido y cuantizacion del ADC, muestreado por el PID
add_block('simulink/Sources/Random Number', [mdl '/Ruido encoder'], 'Variance', 'p.sigma_theta^2', ...
    'SampleTime', 'p.Ts', 'Seed', '1', 'Position', pos(560, 170, 50, 30));
add_block('simulink/Math Operations/Sum', [mdl '/Encoder'], 'Inputs', '++', 'IconShape', 'rectangular', ...
    'Position', pos(620, 115, 30, 70));
add_block('simulink/Discontinuities/Quantizer', [mdl '/ADC'], 'QuantizationInterval', 'p.q_theta', ...
    'Position', pos(690, 133, 50, 34));

add_line(mdl, 'Referencia/1', 'PID/1');
add_line(mdl, 'PID/1', 'PWM entero/1');
add_line(mdl, 'PWM entero/1', 'Planta/1');
add_line(mdl, 'Planta/1', 'Encoder/1');
add_line(mdl, 'Ruido encoder/1', 'Encoder/2', 'autorouting', 'on');
add_line(mdl, 'Encoder/1', 'ADC/1');
add_line(mdl, 'ADC/1', 'PID/2', 'autorouting', 'on');

% salidas
add_block('simulink/Sinks/To Workspace', [mdl '/r'], 'VariableName', 'r_sl', 'SaveFormat', 'Timeseries', 'Position', pos(170, 20, 60, 25));
add_block('simulink/Sinks/To Workspace', [mdl '/u'], 'VariableName', 'u_sl', 'SaveFormat', 'Timeseries', 'Position', pos(400, 20, 60, 25));
add_block('simulink/Sinks/To Workspace', [mdl '/y'], 'VariableName', 'y_sl', 'SaveFormat', 'Timeseries', 'Position', pos(790, 137, 60, 25));
add_block('simulink/Sinks/Scope', [mdl '/Angulo'], 'NumInputPorts', '2', 'Position', pos(780, 160, 40, 50));
add_line(mdl, 'Referencia/1', 'r/1', 'autorouting', 'on');
add_line(mdl, 'PWM entero/1', 'u/1', 'autorouting', 'on');
add_line(mdl, 'ADC/1', 'y/1', 'autorouting', 'on');
add_line(mdl, 'ADC/1', 'Angulo/1', 'autorouting', 'on');
add_line(mdl, 'Referencia/1', 'Angulo/2', 'autorouting', 'on');

Simulink.BlockDiagram.arrangeSystem([mdl '/Planta']);
Simulink.BlockDiagram.arrangeSystem(mdl);
save_system(mdl, archivo);

%% simular y comparar con el script y con el banco
out = sim(mdl);
ts = out.y_sl.Time; ys = squeeze(out.y_sl.Data); us = squeeze(out.u_sl.Data); rs = squeeze(out.r_sl.Data);
tc = [0 cumsum(p.sec_dur)];
refSec = @(t) p.sec_ref(min(numel(p.sec_ref), find(t >= tc, 1, 'last')));
sc = simular_pid(p, refSec, tc(end) - p.Ts);
T = readtable(fullfile(aqui, '..', 'procesamiento', 'datos', 'pid_escalones150_20261106_124411.csv'), 'CommentStyle', '#');
tm = (T.t_ms - T.t_ms(1)) / 1000;

f = figure('Position', [100 100 1000 650]);
subplot(2,1,1);
plot(tm, T.theta, 'Color', [0.85 0.15 0.15]); hold on;
plot(ts, ys, 'Color', [0.1 0.45 0.8]); plot(sc.t, sc.y, 'Color', [0.2 0.65 0.2]);
stairs(out.r_sl.Time, rs, 'k--'); grid on; ylabel('\theta [grados]');
legend('banco (ensayo 1)', 'Simulink', 'script', 'referencia', 'Location', 'southeast');
title('Secuencia de escalones: banco, modelo de Simulink y script');
subplot(2,1,2);
plot(tm, T.u, 'Color', [0.85 0.15 0.15]); hold on;
plot(out.u_sl.Time, us, 'Color', [0.1 0.45 0.8]); plot(sc.t, sc.u, 'Color', [0.2 0.65 0.2]);
grid on; ylabel('u [duty]'); xlabel('t [s]'); ylim([-5 150]);
exportgraphics(f, fullfile(aqui, 'figuras', 'sim_05_simulink.png'), 'Resolution', 150);

yi = interp1(ts, ys, sc.t, 'previous', 'extrap');
m = sc.r ~= 150 & [false; diff(sc.r) == 0];
fprintf('Simulink frente al script: RMS %.2f grados (sin el tramo de 150: %.2f)\n', rms(yi - sc.y), rms(yi(m) - sc.y(m)));
print(['-s' mdl], '-dpng', '-r150', fullfile(aqui, 'figuras', 'simulink_modelo.png'));
print(['-s' mdl '/Planta'], '-dpng', '-r150', fullfile(aqui, 'figuras', 'simulink_planta.png'));
close_system(mdl, 0);
