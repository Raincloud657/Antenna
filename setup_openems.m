function setup_openems()
%SETUP_OPENEMS Add openEMS MATLAB/Octave path using OPENEMS_HOME
%   This function adds the openEMS matlab directory to the current path.
%   The path is taken from the OPENEMS_HOME environment variable. If the
%   variable is not defined, a warning is displayed and no path is added.

openems_home = getenv('OPENEMS_HOME');
if isempty(openems_home)
    warning('OPENEMS_HOME environment variable not set. Please set it to the openEMS installation directory.');
else
    addpath(fullfile(openems_home, 'matlab'));
end
end

