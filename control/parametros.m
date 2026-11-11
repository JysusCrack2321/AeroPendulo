function p = parametros()
% Parametros de la planta y del controlador. Valores de identificar_planta.m.
% theta en grados desde la posicion colgada: 0 colgado, 90 horizontal, 180 arriba.

p.g   = 9.81;
p.R   = 0.1307;              % pivote -> centro del motor [m]
p.m   = 0.03172;             % masa del conjunto [kg] (pesada)
p.d   = 0.0245;              % pivote -> CM [m] (CAD)
p.mgd = p.m * p.g * p.d;     % [N*m]
p.I_cad = 9.45e-5;           % [kg*m^2] (CAD)

p.w2  = 93.8;                % mgd/I de la oscilacion libre [1/s^2]
p.a   = 0.90;                % b/I de la oscilacion libre [1/s]
p.I   = p.mgd / p.w2;        % [kg*m^2]
p.b   = p.a * p.I;           % [N*m*s]

p.Ka  = 8.044e-4;            % [N/duty] barrido de 5 ciclos con lastre (6 nov)
p.F0  = -4.730e-3;           % [N] intercepto (zona muerta ~6 duty)
p.Fcuad = [-6.268e-7 9.799e-4 -1.451e-2];   % F(u) = polyval [N], ajuste cuadratico
p.kb  = p.Ka * p.R / p.I * 180/pi;          % [grados/s^2 por duty]

p.sigma_theta = 0.39;        % ruido del AS5600 con motor encendido [grados]
p.q_theta = 360/4095;        % cuantizacion del ADC [grados]

p.Ts   = 0.01;
p.Kp   = 1.0;                % duty/grado
p.Ki   = 1.0;                % duty/(grado*s)
p.Kd   = 0.2;                % duty*s/grado
p.Tf   = 0.02;               % [s]
p.beta = 0.0;
p.u_max = 255;

% misma secuencia que firmware/control-pid/src/main.cpp
p.sec_ref = [45 90 105 120 135 150 135 120 105 90 45];
p.sec_dur = 10*ones(1, 11);
end
