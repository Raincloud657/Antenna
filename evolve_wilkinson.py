import random
import json
from dataclasses import dataclass, field
from typing import List

@dataclass
class Candidate:
    stub_length: float
    resistor_value: float
    trace_width: float
    topology: str
    fitness: float = field(default=0.0)
    metrics: dict = field(default_factory=dict)


def simulate(candidate: Candidate) -> dict:
    """Run EM simulation using openEMS (external) and return measurement data."""
    # Placeholder: integrate with openEMS or other solver.
    # Example return structure with S-parameters and VSWR across frequency.
    return {
        "insertion_loss": random.uniform(0.0, 0.5),  # dB
        "isolation": random.uniform(10.0, 50.0),     # dB
        "vswr": random.uniform(1.0, 2.0),            # unitless
        "bandwidth": random.uniform(4e9, 10e9),      # Hz
        "reconfigurable": random.choice([0.0, 0.5, 1.0])
    }


def evaluate(candidate: Candidate) -> float:
    results = simulate(candidate)
    candidate.metrics = results
    # Weighted fitness evaluation
    fitness = 0.0
    # Lower insertion loss is better
    fitness += (0.1 - results["insertion_loss"]) * 5.0
    # Higher isolation is better
    fitness += (results["isolation"] / 40.0) * 5.0
    # VSWR close to 1 is better
    fitness += (2.0 - results["vswr"]) * 5.0
    # Wide bandwidth is better
    bw_score = min(results["bandwidth"], 10e9) / 10e9
    fitness += bw_score * 2.0
    # Reconfigurability increases score
    fitness += results["reconfigurable"] * 3.0
    # Penalize unrealistic physical size (placeholder)
    return fitness


def meets_goals(candidate: Candidate) -> bool:
    m = candidate.metrics
    return (
        m.get("insertion_loss", 1.0) <= 0.1 and
        m.get("isolation", 0.0) >= 40.0 and
        m.get("vswr", 2.0) <= 1.05 and
        5e8 <= m.get("bandwidth", 0.0) <= 10e9 and
        m.get("reconfigurable", 0.0) >= 1.0
    )


def mutate(candidate: Candidate) -> Candidate:
    return Candidate(
        stub_length=candidate.stub_length * random.uniform(0.9, 1.1),
        resistor_value=candidate.resistor_value * random.uniform(0.9, 1.1),
        trace_width=candidate.trace_width * random.uniform(0.9, 1.1),
        topology=random.choice([candidate.topology, "alt"]),
    )


def crossover(a: Candidate, b: Candidate) -> Candidate:
    return Candidate(
        stub_length=random.choice([a.stub_length, b.stub_length]),
        resistor_value=random.choice([a.resistor_value, b.resistor_value]),
        trace_width=random.choice([a.trace_width, b.trace_width]),
        topology=random.choice([a.topology, b.topology])
    )


def evolve(population: List[Candidate], generations: int = 50, elite: int = 5) -> Candidate:
    """Evolve population and print progress information."""
    best_so_far = 0.0
    for gen in range(1, generations + 1):
        for cand in population:
            cand.fitness = evaluate(cand)
        population.sort(key=lambda c: c.fitness, reverse=True)

        # Print a message each generation so the user sees progress
        print(f"[gen {gen}] best {population[0].fitness:.3f}")

        # Highlight significant fitness improvements
        if population[0].fitness > best_so_far * 1.1:
            best_so_far = population[0].fitness
            print(f"[gen {gen}] Fitness increase 10% -> {best_so_far:.3f}")

        if gen % 100 == 0:
            print(f"[gen {gen}] Current best fitness {population[0].fitness:.3f}")

        if meets_goals(population[0]):
            print(f"[gen {gen}] Goals satisfied!")
            return population[0]

        next_gen = population[:elite]
        while len(next_gen) < len(population):
            parents = random.sample(population[:10], 2)
            child = crossover(*parents)
            if random.random() < 0.3:
                child = mutate(child)
            next_gen.append(child)
        population = next_gen

    print("Evolution finished")
    return population[0]


if __name__ == "__main__":
    # Initial population
    population = [
        Candidate(
            stub_length=random.uniform(1.0, 10.0),
            resistor_value=random.uniform(90.0, 110.0),
            trace_width=random.uniform(0.5, 3.0),
            topology="std"
        )
        for _ in range(20)
    ]
    best = evolve(population, generations=100)
    print(json.dumps(best.__dict__, indent=2))
