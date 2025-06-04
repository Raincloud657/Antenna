% evolutionary_optimization.m
% Optimize a patch antenna using an evolutionary algorithm and openEMS
% 
% The algorithm iterates over a population of individuals encoding antenna
% parameters (width, length and feed position). The openEMS simulation
% is executed for each individual to obtain a performance metric. This
% metric is recorded as fitness. The loop stops when the fitness of the
% best individual improves by 100%% relative to the initial design.
%
% This script is intended as a template and assumes that openEMS is
% installed and accessible via the MATLAB/Octave interface.

function evolutionary_optimization()
    % Baseline parameters (initial design)
    base_params = struct('width', 30, 'length', 40, 'feed_pos', -5.5);
    base_fitness = evaluate_design(base_params);

    % Evolutionary algorithm settings
    pop_size = 10;
    max_gens = 50;
    mutation_scale = 0.1;

    % Initialise population around baseline
    population = repmat(base_params, [1 pop_size]);
    for i = 1:pop_size
        population(i) = mutate_params(population(i), mutation_scale);
    end

    best_fitness = base_fitness;
    best_params = base_params;

    for gen = 1:max_gens
        % Evaluate population
        fitness = zeros(1, pop_size);
        for i = 1:pop_size
            fitness(i) = evaluate_design(population(i));
        end

        % Select best individual
        [gen_best_fitness, idx] = max(fitness);
        gen_best_params = population(idx);

        if gen_best_fitness > best_fitness
            best_fitness = gen_best_fitness;
            best_params = gen_best_params;
        end

        fprintf('Generation %d - Best fitness: %.4f\n', gen, best_fitness);

        % Check stopping criterion (100%% improvement)
        if best_fitness >= 2 * base_fitness
            disp('Target improvement reached.');
            break;
        end

        % Create next generation using mutation around best design
        for i = 1:pop_size
            population(i) = mutate_params(best_params, mutation_scale);
        end
    end

    disp('Optimal parameters:');
    disp(best_params);
end

function fitness = evaluate_design(params)
    % Create a temporary simulation directory
    sim_dir = tempname();
    mkdir(sim_dir);

    % Copy template simulation files if necessary
    % (Assumes Patch Antenna 0 is used as starting template)
    template = fullfile('Patch Antenna 0', 'Patch_Antenna.m');
    sim_script = fullfile(sim_dir, 'Patch_Antenna.m');
    copyfile(template, sim_script);

    % Modify the script with the new parameters
    replace_param(sim_script, 'patch.width', params.width);
    replace_param(sim_script, 'patch.length', params.length);
    replace_param(sim_script, 'feed.pos', params.feed_pos);

    % Run the simulation
    try
        run(sim_script);
        % Example metric: inverse of |S11| at resonance
        freq = linspace(1e9, 3e9, 501);
        U = ReadUI({'port_ut1','et'}, fullfile(sim_dir, 'tmp'), freq);
        I = ReadUI('port_it1', fullfile(sim_dir, 'tmp'), freq);
        uf_inc = 0.5*(U.FD{1}.val + I.FD{1}.val * 50);
        uf_ref = U.FD{1}.val - uf_inc;
        s11 = uf_ref ./ uf_inc;
        fitness = 1/max(abs(s11));
    catch
        % If simulation fails assign poor fitness
        fitness = 0;
    end

    % Clean up
    rmdir(sim_dir, 's');
end

function params = mutate_params(params, scale)
    params.width = params.width * (1 + scale*randn());
    params.length = params.length * (1 + scale*randn());
    params.feed_pos = params.feed_pos * (1 + scale*randn());
end

function replace_param(file, param_name, value)
    % Simple text substitution of parameter value in MATLAB script
    txt = fileread(file);
    pattern = sprintf('%s\s*=\s*[^;]+;', param_name);
    replacement = sprintf('%s = %.6f;', param_name, value);
    txt = regexprep(txt, pattern, replacement);
    fid = fopen(file, 'w');
    fwrite(fid, txt);
    fclose(fid);
end
