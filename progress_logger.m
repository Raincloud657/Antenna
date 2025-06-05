num_generations = 1000;
fitness = 1.0;
start_fitness = fitness;
prev_fitness = fitness;
for gen = 1:num_generations
    % simulate some random fitness improvement
    new_fitness = fitness + 0.01*randn();
    fitness = new_fitness;
    if mod(gen, 100) == 0
        overall_change = 100 * (fitness - start_fitness) / start_fitness;
        interval_change = 100 * (fitness - prev_fitness) / prev_fitness;
        fprintf('Generation %d: overall change %.2f%%, last 100 generations %.2f%%\n', ...
                gen, overall_change, interval_change);
        prev_fitness = fitness;
    end
end
