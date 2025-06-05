import random

class Candidate:
    def __init__(self, design_id, fitness=0.0, reason="Initial generation"):
        self.design_id = design_id
        self.fitness = fitness
        self.reason = reason

    def mutate(self):
        # Placeholder mutation logic
        change = random.uniform(-0.05, 0.1)
        self.fitness = max(0.0, self.fitness + change)
        self.reason = f"Mutation change {change:+.3f}"


class EvolutionaryOptimizer:
    def __init__(self, population_size, generations):
        self.population_size = population_size
        self.generations = generations
        self.population = [Candidate(i) for i in range(population_size)]

    def evaluate_fitness(self, candidate):
        # Placeholder for real simulation-based fitness
        return candidate.fitness

    def run(self):
        best_fitness = 0.0
        for gen in range(1, self.generations + 1):
            for cand in self.population:
                cand.mutate()
                cand.fitness = self.evaluate_fitness(cand)

            # Pick best candidate
            best = max(self.population, key=lambda c: c.fitness)
            percent_increase = (best.fitness - best_fitness) / best_fitness * 100 if best_fitness else 0.0
            reason = best.reason
            print(f"Gen {gen}: Fitness {percent_increase:+.1f}% increase {best.fitness:.4f} -- {reason}")
            best_fitness = best.fitness


if __name__ == "__main__":
    optimizer = EvolutionaryOptimizer(population_size=5, generations=10)
    optimizer.run()
