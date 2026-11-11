function s = simular_pid(p, ref, Tfin, opc)
% Simulacion no lineal en tiempo discreto del PID tal como corre en el ESP32.
%   ref : @(t) referencia en grados desde la horizontal
%   opc : struct opcional
%     .ruido   (true)  ruido gaussiano p.sigma_theta + cuantizacion del ADC
%     .actuador ('cuadratico' | 'lineal')
%     .pert    @(t) par de perturbacion [N*m]
%     .m_extra, .r_extra  masa puntual anadida [kg] a r [m] del pivote (r>0 lado del motor)
%     .fI, .fKa, .fb      factores multiplicativos sobre I, Ka y b de la planta
%     .theta0  angulo inicial (0, colgado)
%     .semilla
if nargin < 4, opc = struct(); end
def = struct('ruido', true, 'actuador', 'cuadratico', 'pert', @(t) 0, ...
             'm_extra', 0, 'r_extra', 0, 'fI', 1, 'fKa', 1, 'fb', 1, 'theta0', 0, 'semilla', 1);
for c = fieldnames(def)'
    if ~isfield(opc, c{1}), opc.(c{1}) = def.(c{1}); end
end
rng(opc.semilla);

I   = p.I * opc.fI + opc.m_extra * opc.r_extra^2;
mgd = p.mgd + opc.m_extra * p.g * opc.r_extra;
b   = p.b * opc.fb;
if strcmp(opc.actuador, 'lineal')
    Fu = @(u) max(0, opc.fKa * (p.Ka * u + p.F0));
else
    Fu = @(u) max(0, opc.fKa * polyval(p.Fcuad, u));
end
dyn = @(t, z, u) [z(2); (Fu(u)*p.R - mgd*sin(z(1)) - b*z(2) + opc.pert(t)) / I];

Ts = p.Ts; N = round(Tfin / Ts); sub = 10; h = Ts / sub;
s.t = (0:N-1)' * Ts;
s.r = zeros(N, 1); s.y = s.r; s.th = s.r; s.u = s.r;

z = [deg2rad(opc.theta0); 0];
integral = p.Kp*(1 - p.beta)*opc.theta0; derivada = 0;
yAnt = opc.theta0; eAnt = ref(0) - opc.theta0;
for k = 1:N
    t = s.t(k);
    th = rad2deg(z(1));
    y = th;
    if opc.ruido
        y = round((th + p.sigma_theta * randn) / p.q_theta) * p.q_theta;
    end
    r = ref(t);
    e = r - y;
    derivada = (2*p.Tf - Ts) / (2*p.Tf + Ts) * derivada - 2*p.Kd / (2*p.Tf + Ts) * (y - yAnt);
    integralNueva = integral + p.Ki * Ts/2 * (e + eAnt);
    uLibre = p.Kp * (p.beta*r - y) + integralNueva + derivada;
    if ~((uLibre > p.u_max && e > 0) || (uLibre < 0 && e < 0))
        integral = integralNueva;
    end
    u = round(min(max(p.Kp * (p.beta*r - y) + integral + derivada, 0), p.u_max));
    eAnt = e; yAnt = y;

    s.r(k) = r; s.y(k) = y; s.th(k) = th; s.u(k) = u;

    for j = 1:sub
        tj = t + (j-1)*h;
        k1 = dyn(tj, z, u);
        k2 = dyn(tj + h/2, z + h/2*k1, u);
        k3 = dyn(tj + h/2, z + h/2*k2, u);
        k4 = dyn(tj + h, z + h*k3, u);
        z = z + h/6 * (k1 + 2*k2 + 2*k3 + k4);
    end
end
end
