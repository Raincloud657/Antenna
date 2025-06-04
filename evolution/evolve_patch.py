import os
import json
import random
import math

# Evolution of patch antenna dimensions targeting 2.4 GHz resonance

target_freq = 2.4e9  # 2.4 GHz

eps_r = 3.38
h = 1.524e-3  # substrate thickness in meters

c0 = 299792458.0

fitness_dir = os.path.join('evolution', 'Fitness')
most_fit_dir = os.path.join(fitness_dir, 'Most_fit')
os.makedirs(most_fit_dir, exist_ok=True)

# Base design taken from Patch Antenna 0
base = {
    'width': 32.86e-3,
    'length': 41.37e-3,
}


def resonant_freq(width, length):
    """Return the fundamental resonant frequency of a rectangular patch."""
    eps_eff = (eps_r + 1)/2 + (eps_r - 1)/2 / math.sqrt(1 + 12*h/width)
    delta_l = h * 0.412 * (eps_eff + 0.3) * (width/h + 0.264) / ((eps_eff - 0.258) * (width/h + 0.8))
    l_eff = length + 2*delta_l
    return c0 / (2 * l_eff * math.sqrt(eps_eff))


def evaluate(ind):
    fr = resonant_freq(ind['width'], ind['length'])
    ind['resonant_freq'] = fr
    ind['fitness'] = 1.0 / (1.0 + abs(target_freq - fr))
    return ind['fitness']


def mutate(ind, sigma=0.001):
    new = ind.copy()
    new['width'] += random.gauss(0, sigma)
    new['length'] += random.gauss(0, sigma)
    return new


def evolve(generations=20, pop_size=10, retain=0.3):
    population = [base]
    for _ in range(pop_size-1):
        population.append(mutate(base))

    best_overall = None

    for gen in range(generations):
        for ind in population:
            evaluate(ind)
        population.sort(key=lambda x: x['fitness'], reverse=True)
        best = population[0]
        if best_overall is None or best['fitness'] > best_overall['fitness']:
            best_overall = best.copy()
            with open(os.path.join(most_fit_dir, 'best.json'), 'w') as f:
                json.dump(best_overall, f, indent=2)
        # save generation
        gen_file = os.path.join(fitness_dir, f'generation_{gen}.json')
        with open(gen_file, 'w') as f:
            json.dump(population, f, indent=2)
        # select top individuals
        retain_len = max(1, int(len(population)*retain))
        parents = population[:retain_len]
        # repopulate
        population = parents[:]
        while len(population) < pop_size:
            parent = random.choice(parents)
            child = mutate(parent)
            population.append(child)
    return best_overall


if __name__ == '__main__':
    best = evolve()
    print('Best design:', best)
