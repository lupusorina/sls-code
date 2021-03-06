% note: run sequentially; some params from later sections depend on
% params specified in previous sections
clear; close all; clc; 

% specify system matrices
sys    = LTISystem;
sys.Nx = 10;

alpha = 0.2; rho = 1; actDens = 1;
generate_dbl_stoch_chain(sys, rho, actDens, alpha); % generate sys.A, sys.B2

sys.B1  = eye(sys.Nx); % used in simulation
sys.C1  = [speye(sys.Nx); sparse(sys.Nu, sys.Nx)]; % used in H2/HInf ctrl
sys.D12 = [sparse(sys.Nx, sys.Nu); speye(sys.Nu)];

% sls parameters
slsParams       = SLSParams();
slsParams.T_    = 20;
slsParams.obj_  = Objective.H2; % objective function

% simulation parameters
simParams           = SimParams;
simParams.tSim_     = 25;
simParams.w_        = zeros(sys.Nx, simParams.tSim_); % disturbance
simParams.w_(floor(sys.Nx/2), 1) = 10;
simParams.openLoop_ = false;

%% (1) basic sls (centralized controller)
slsParams.mode_ = SLSMode.Basic;

slsOuts1 = state_fdbk_sls(sys, slsParams);
[x1, u1] = simulate_system(sys, simParams, slsOuts1.R_, slsOuts1.M_);
plot_heat_map(x1, sys.B2*u1, 'Centralized');

%% (2) d-localized sls
slsParams.mode_     = SLSMode.DAndL;
slsParams.actDelay_ = 1;
slsParams.cSpeed_   = 2; % communication speed must be sufficiently large
slsParams.d_        = 3;

slsOuts2 = state_fdbk_sls(sys, slsParams);
[x2, u2] = simulate_system(sys, simParams, slsOuts2.R_, slsOuts2.M_);
plot_heat_map(x2, sys.B2*u2, 'Localized');

%% (3) approximate d-localized sls
slsParams.mode_     = SLSMode.DAndL;
slsParams.approx_   = true;
slsParams.cSpeed_   = 1;
slsParams.robCoeff_ = 10^3;

slsOuts3 = state_fdbk_sls(sys, slsParams);
[x3, u3] = simulate_system(sys, simParams, slsOuts3.R_, slsOuts3.M_);
plot_heat_map(x3, sys.B2*u3, 'Approximately Localized');