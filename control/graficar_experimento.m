function graficar_experimento(archivos)
% Graficas y metricas de los ensayos del banco (procesamiento/datos/pid_*.csv),
% superpuestos a la simulacion no lineal con la misma referencia y las mismas ganancias.
%   graficar_experimento                      todos los pid_*.csv
%   graficar_experimento('pid_escalones_...csv')
aqui = fileparts(mfilename('fullpath'));
datos = fullfile(aqui, '..', 'procesamiento', 'datos');
figs = fullfile(aqui, 'figuras'); if ~exist(figs, 'dir'), mkdir(figs); end
resultados = fullfile(aqui, 'resultados'); if ~exist(resultados, 'dir'), mkdir(resultados); end
if nargin < 1
    l = dir(fullfile(datos, 'pid_*.csv'));
    archivos = {l.name};
elseif ischar(archivos) || isstring(archivos)
    archivos = cellstr(archivos);
end
if isempty(archivos), error('no hay pid_*.csv en %s', datos); end

for a = 1:numel(archivos)
    close all;
    ruta = archivos{a};
    if ~isfile(ruta), ruta = fullfile(datos, ruta); end
    [~, base] = fileparts(ruta);
    p = parametros();
    p = leer_ganancias(ruta, p);
    T = readtable(ruta, 'CommentStyle', '#');
    t = (T.t_ms - T.t_ms(1)) / 1000;
    r = T.ref; y = T.theta; u = T.u;

    tr = t; rr = r;
    sim = simular_pid(p, @(tt) rr(max(1, find(tr <= tt + 1e-9, 1, 'last'))), t(end), ...
        struct('theta0', mean(y(1:min(5, end)))));

    f = figure('Position', [100 100 1000 820]);
    subplot(3,1,1);
    plot(sim.t, sim.y, 'Color', [0.3 0.5 0.95 0.8]); hold on;
    plot(t, y, 'Color', [0.85 0.15 0.15]);
    stairs(t, r, 'k--', 'LineWidth', 1.1);
    grid on; ylabel('\theta [grados]');
    legend('simulacion', 'medido', 'referencia', 'Location', 'southeast');
    title(sprintf('%s   (K_p %.2f, K_i %.2f, K_d %.3f, T_f %.3f, \\beta %.2f)', ...
        strrep(base, '_', '\_'), p.Kp, p.Ki, p.Kd, p.Tf, p.beta));
    subplot(3,1,2);
    plot(sim.t, sim.u, 'Color', [0.3 0.5 0.95 0.8]); hold on; plot(t, u, 'k');
    grid on; ylabel('u [duty]'); ylim([-5 260]); legend('simulacion', 'medido');
    subplot(3,1,3);
    plot(t, r - y, 'Color', [0.3 0.3 0.3]); hold on; yline([-1 1], 'r:');
    grid on; ylabel('e [grados]'); xlabel('t [s]');
    exportgraphics(f, fullfile(figs, ['exp_' base '.png']), 'Resolution', 150);

    Me = metricas_escalones(t, r, y, u);
    Ms = metricas_escalones(sim.t, sim.r, sim.y, sim.u);
    fprintf('\n== %s ==\nmedido:\n', base); disp(Me);
    fprintf('simulado:\n'); disp(Ms);
    writetable(Me, fullfile(resultados, ['metricas_' base '.csv']));
    writetable(Ms, fullfile(resultados, ['metricas_' base '_sim.csv']));

    n = height(Me);
    if n > 1
        f = figure('Position', [100 100 1100 650]);
        ini = [1; find(abs(diff(r)) > 1e-6) + 1];
        inis = [1; find(abs(diff(sim.r)) > 1e-6) + 1];
        for k = 1:n
            subplot(ceil(n/3), 3, k);
            idx = ini(k):min(ini(k) + 800, numel(t));
            ids = inis(k):min(inis(k) + 800, numel(sim.t));
            plot(sim.t(ids) - sim.t(inis(k)), sim.y(ids), 'Color', [0.3 0.5 0.95]); hold on;
            plot(t(idx) - t(ini(k)), y(idx), 'Color', [0.85 0.15 0.15]);
            yline(Me.hasta(k), 'k--');
            grid on; xlabel('t [s]'); ylabel('\theta [°]');
            title(sprintf('%.0f -> %.0f°: M_p %.0f %%, t_s %.1f s', Me.desde(k), Me.hasta(k), Me.Mp_pct(k), Me.ts_s(k)));
        end
        legend('simulacion', 'medido', 'Location', 'southeast');
        exportgraphics(f, fullfile(figs, ['exp_' base '_pasos.png']), 'Resolution', 150);

        f = figure('Position', [100 100 1000 400]);
        subplot(1,2,1); bar([Me.Mp_pct Ms.Mp_pct]); yline(15, 'r--', '15 %');
        grid on; xlabel('escalon'); ylabel('M_p [%]'); legend('medido', 'simulado');
        subplot(1,2,2); bar([Me.ts_s Ms.ts_s]); yline(5, 'r--', '5 s');
        grid on; xlabel('escalon'); ylabel('t_s [s]'); legend('medido', 'simulado');
        exportgraphics(f, fullfile(figs, ['exp_' base '_metricas.png']), 'Resolution', 150);
    end
end
end

function p = leer_ganancias(ruta, p)
txt = fileread(ruta);
tok = regexp(txt, '#K Kp=([\d.eE+-]+) Ki=([\d.eE+-]+) Kd=([\d.eE+-]+) Tf=([\d.eE+-]+) beta=([\d.eE+-]+)', 'tokens', 'once');
if ~isempty(tok)
    v = str2double(tok);
    p.Kp = v(1); p.Ki = v(2); p.Kd = v(3); p.Tf = v(4); p.beta = v(5);
end
end
