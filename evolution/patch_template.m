%
% EXAMPLE / antennas / patch antenna
%
% This example demonstrates how to:
%  - calculate the reflection coefficient of a patch antenna
% 
%
% Tested with
%  - Matlab 2009b
%  - Octave 3.3.52
%  - openEMS v0.0.23
%
% (C) 2010,2011 Thorsten Liebig <thorsten.liebig@uni-due.de>

close all
clear
clc

%% switches & options...
postprocessing_only = 0;
draw_3d_pattern = 0; % this may take a while...
use_pml = 0;         % use pml boundaries instead of mur
openEMS_opts = '';

%% setup the simulation
physical_constants;
unit = 1e-3; % all length in mm

% width in x-direction
% length in y-direction
% main radiation in z-direction
patch.width  = {WIDTH}; % resonant length
patch.length = {LENGTH};

substrate.epsR   = 3.38;
substrate.kappa  = 1e-3 * 2*pi*2.45e9 * EPS0*substrate.epsR;
substrate.width  = 60;
substrate.length = 60;
substrate.thickness = 1.524;
substrate.cells = 4;

feed.pos = {FEED_POS};
feed.width = {FEED_WIDTH};
feed.R = 50; % feed resistance

% size of the simulation box
SimBox = [100 100 25];

%% prepare simulation folder
Sim_Path = 'tmp';
Sim_CSX = 'patch_ant.xml';
if (postprocessing_only==0)
    [status, message, messageid] = rmdir( Sim_Path, 's' ); % clear previous directory
    [status, message, messageid] = mkdir( Sim_Path ); % create empty simulation folder
end

%% setup FDTD parameter & excitation function
max_timesteps = 30000;
min_decrement = 1e-5; % equivalent to -50 dB
f0 = 0e9; % center frequency
fc = 3e9; % 20 dB corner frequency (in this case 0 Hz - 3e9 Hz)
FDTD = InitFDTD( 'NrTS', max_timesteps, 'EndCriteria', min_decrement );
FDTD = SetGaussExcite( FDTD, f0, fc );
BC = {'MUR' 'MUR' 'MUR' 'MUR' 'MUR' 'MUR'}; % boundary conditions
if (use_pml>0)
    BC = {'PML_8' 'PML_8' 'PML_8' 'PML_8' 'PML_8' 'PML_8'}; % use pml instead of mur
end
FDTD = SetBoundaryCond( FDTD, BC );

%% setup CSXCAD geometry & mesh
% currently, openEMS cannot automatically generate a mesh
max_res = c0 / (f0+fc) / unit / 20; % cell size: lambda/20
CSX = InitCSX();
mesh.x = [-SimBox(1)/2 SimBox(1)/2 -substrate.width/2 substrate.width/2 feed.pos];
% add patch mesh with 2/3 - 1/3 rule
mesh.x = [mesh.x -patch.width/2-max_res/2*0.66 -patch.width/2+max_res/2*0.33 patch.width/2+max_res/2*0.66 patch.width/2-max_res/2*0.33];
mesh.x = SmoothMeshLines( mesh.x, max_res, 1.4); % create a smooth mesh between specified mesh lines
mesh.y = [-SimBox(2)/2 SimBox(2)/2 -substrate.length/2 substrate.length/2 -feed.width/2 feed.width/2];
% add patch mesh with 2/3 - 1/3 rule
mesh.y = [mesh.y -patch.length/2-max_res/2*0.66 -patch.length/2+max_res/2*0.33 patch.length/2+max_res/2*0.66 patch.length/2-max_res/2*0.33];
mesh.y = SmoothMeshLines( mesh.y, max_res, 1.4 );
mesh.z = [-SimBox(3)/2 linspace(0,substrate.thickness,substrate.cells) SimBox(3) ];
mesh.z = SmoothMeshLines( mesh.z, max_res, 1.4 );
mesh = AddPML( mesh, [8 8 8 8 8 8] ); % add equidistant cells (air around the structure)
CSX = DefineRectGrid( CSX, unit, mesh );

%% create patch
CSX = AddMetal( CSX, 'patch' ); % create a perfect electric conductor (PEC)
start = [-patch.width/2 -patch.length/2 substrate.thickness];
stop  = [ patch.width/2  patch.length/2 substrate.thickness];
CSX = AddBox(CSX,'patch',10,start,stop);

%% create substrate
CSX = AddMaterial( CSX, 'substrate' );
CSX = SetMaterialProperty( CSX, 'substrate', 'Epsilon', substrate.epsR, 'Kappa', substrate.kappa );
start = [-substrate.width/2 -substrate.length/2 0];
stop  = [ substrate.width/2  substrate.length/2 substrate.thickness];
CSX = AddBox( CSX, 'substrate', 0, start, stop );

%% create ground (same size as substrate)
CSX = AddMetal( CSX, 'gnd' ); % create a perfect electric conductor (PEC)
start(3)=0;
stop(3) =0;
CSX = AddBox(CSX,'gnd',10,start,stop);

%% apply the excitation & resist as a current source
start = [feed.pos-.1 -feed.width/2 0];
stop  = [feed.pos+.1 +feed.width/2 substrate.thickness];
[CSX] = AddLumpedPort(CSX, 5 ,1 ,feed.R, start, stop, [0 0 1], true);

%% dump magnetic field over the patch antenna
CSX = AddDump( CSX, 'Ht_', 'DumpType', 1, 'DumpMode', 2); % cell interpolated
start = [-patch.width -patch.length substrate.thickness+1];
stop  = [ patch.width  patch.length substrate.thickness+1];
CSX = AddBox( CSX, 'Ht_', 0, start, stop );

%%nf2ff calc
[CSX nf2ff] = CreateNF2FFBox(CSX, 'nf2ff', -SimBox/2, SimBox/2);

if (postprocessing_only==0)
    %% write openEMS compatible xml-file
    WriteOpenEMS( [Sim_Path '/' Sim_CSX], FDTD, CSX );

    %% show the structure
%    CSXGeomPlot( [Sim_Path '/' Sim_CSX] );

    % run openEMS
RunOpenEMS( Sim_Path, Sim_CSX, openEMS_opts );
end

freq = linspace( max([1e9,f0-fc]), f0+fc, 501 );
U = ReadUI( {'port_ut1','et'}, 'tmp/', freq ); % time domain/freq domain voltage
I = ReadUI( 'port_it1', 'tmp/', freq ); % time domain/freq domain current (half time step is corrected)

f_res = f0;


% calculate the far field at phi=0 degrees and at phi=90 degrees
thetaRange = (0:2:359) - 180;
phiRange = [0 90];
disp( 'calculating far field at phi=[0 90] deg...' );
nf2ff = CalcNF2FF(nf2ff, Sim_Path, f_res, thetaRange*pi/180, phiRange*pi/180);

Dlog=10*log10(nf2ff.Dmax);

% display power and directivity
disp( ['radiated power: Prad = ' num2str(nf2ff.Prad) ' Watt']);
disp( ['directivity: Dmax = ' num2str(Dlog) ' dBi'] );



