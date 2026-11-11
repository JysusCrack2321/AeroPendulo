function M = metricas_escalones(t, r, y, u)
% Metricas por escalon. El primer tramo arranca desde el angulo inicial medido.
%   ts: ultimo instante fuera de la banda max(2% del escalon, 1 grado), con y suavizada 0.2 s
%   ess: media de r - y en los ultimos 2 s del tramo
t = t(:); r = r(:); y = y(:); u = u(:);
Ts = median(diff(t));
ini = [1; find(abs(diff(r)) > 1e-6) + 1];
fin = [ini(2:end) - 1; numel(t)];

n = numel(ini);
[r0, r1, tr, Mp, ts, ess, iae, umax, uss] = deal(nan(n, 1));
for k = 1:n
    idx = ini(k):fin(k);
    tk = t(idx) - t(ini(k));
    if k == 1
        r0(k) = mean(y(1:min(5, numel(y))));
    else
        r0(k) = r(ini(k) - 1);
    end
    r1(k) = r(ini(k));
    D = r1(k) - r0(k);
    ys = movmean(y(idx), max(1, round(0.2 / Ts)));
    yn = (ys - r0(k)) / D;
    i10 = find(yn >= 0.1, 1); i90 = find(yn >= 0.9, 1);
    if ~isempty(i10) && ~isempty(i90), tr(k) = tk(i90) - tk(i10); end
    Mp(k) = max(0, 100 * (max(yn) - 1));
    banda = max(0.02 * abs(D), 1);
    fuera = find(abs(ys - r1(k)) > banda, 1, 'last');
    if isempty(fuera), ts(k) = 0; elseif fuera == numel(idx), ts(k) = inf; else, ts(k) = tk(fuera + 1); end
    cola = tk > tk(end) - 2;
    ess(k) = mean(r1(k) - y(idx(cola)));
    iae(k) = sum(abs(r1(k) - y(idx))) * Ts;
    umax(k) = max(u(idx));
    uss(k) = mean(u(idx(cola)));
end
M = table((1:n)', r0, r1, r1 - r0, tr, Mp, ts, ess, iae, umax, uss, ...
    'VariableNames', {'paso', 'desde', 'hasta', 'delta', 'tr_s', 'Mp_pct', 'ts_s', 'ess_grados', 'IAE', 'u_max', 'u_ss'});
end
