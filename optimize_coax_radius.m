function optimize_coax_radius()
    if exist('RunOpenEMS', 'file') ~= 2
        error('openEMS is not available on the MATLAB/Octave path.');
    end

    start_radius = 100;  % initial inner radius in mm
    target_factor = 2.0; % 100% improvement

    best_fitness = run_sim(start_radius, 0);
    start_fitness = best_fitness;
    best_radius = start_radius;
    iter = 1;

    fprintf('Starting fitness = %g\n', start_fitness);
    while best_fitness < start_fitness * target_factor
        radius = best_radius * (1 + 0.05*randn());
        fitness = run_sim(radius, iter);
        fprintf('Iteration %d: radius %g -> fitness %g\n', iter, radius, fitness);
        if fitness > best_fitness
            best_fitness = fitness;
            best_radius = radius;
        end
        iter = iter + 1;
    end

    fprintf('\nOptimization complete after %d iterations\n', iter-1);
    fprintf('Best radius = %g\n', best_radius);
    fprintf('Fitness improved from %g to %g\n', start_fitness, best_fitness);
end

function fitness = run_sim(radius, iter)
    postprocessing_only = 0;
    use_pml = 0;
    openEMS_opts = '';

    physical_constants;

    Sim_Path = sprintf('tmp_iter_%d', iter);
    Sim_CSX = 'coax.xml';
    if postprocessing_only == 0
        rmdir(Sim_Path, 's');
        mkdir(Sim_Path);
    end

    numTS = 5000;
    length = 1000;
    unit = 1e-3;
    coax_rad_ai = 230;
    coax_rad_aa = 240;
    mesh_res = [5 5 5];

    FDTD = InitFDTD(numTS,1e-5);
    f0 = 0.5e9;
    FDTD = SetGaussExcite(FDTD,f0,f0);
    BC = {'PEC','PEC','PEC','PEC','MUR','MUR'};
    if (use_pml>0)
        BC = {'PEC','PEC','PEC','PEC','PML_8','PML_8'};
    end
    FDTD = SetBoundaryCond(FDTD,BC);

    CSX = InitCSX();
    mesh.x = -coax_rad_aa : mesh_res(1) : coax_rad_aa;
    mesh.y = mesh.x;
    mesh.z = SmoothMeshLines([0 length], mesh_res(3));
    CSX = DefineRectGrid(CSX, unit, mesh);

    CSX = AddMetal(CSX,'copper');
    start = [0,0,0];
    stop  = [0,0,length/2];
    [CSX,port{1}] = AddCoaxialPort(CSX, 10, 1, 'copper', '', start, stop, 'z', radius, coax_rad_ai, coax_rad_aa, 'ExciteAmp', 1, 'FeedShift', 10*mesh_res(1));
    start = [0,0,length/2];
    stop  = [0,0,length];
    [CSX,port{2}] = AddCoaxialPort(CSX, 10, 2, 'copper', '', start, stop, 'z', radius, coax_rad_ai, coax_rad_aa);

    if postprocessing_only == 0
        WriteOpenEMS([Sim_Path '/' Sim_CSX], FDTD, CSX);
        RunOpenEMS(Sim_Path, Sim_CSX, openEMS_opts);
    end

    freq = linspace(0,5e9,1001);
    port = calcPort(port, Sim_Path, freq);
    s11 = port{1}.uf.ref ./ port{1}.uf.inc;
    [~, idx] = min(abs(freq - f0));
    fitness = -abs(s11(idx));
end
