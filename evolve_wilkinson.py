import random
import json
from dataclasses import dataclass, field, asdict
from typing import List
from pathlib import Path

@dataclass
class Candidate:
    stub_length: float
    resistor_value: float
    trace_width: float
    topology: str
    size: float
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


def save_candidate(candidate: Candidate, filename: str) -> None:
    """Save candidate parameters and metrics to a JSON file."""
    Path(filename).write_text(json.dumps(asdict(candidate), indent=2))


def evaluate(candidate: Candidate) -> float:
    results = simulate(candidate)
    candidate.metrics = results
    # Weighted fitness evaluation
    fitness = 0.0

    # 1. Insertion Loss (<=0.1 dB ideal)
    il_ratio = min(results["insertion_loss"] / 0.1, 1.0)
    fitness += (1.0 - il_ratio) * 5.0

    # 2. Isolation (>=40 dB ideal)
    iso_ratio = min(results["isolation"] / 40.0, 1.0)
    fitness += iso_ratio * 5.0

    # 3. VSWR (<=1.05)
    vswr_ratio = min(results["vswr"] / 1.05, 2.0)
    fitness += (2.0 - vswr_ratio) * 5.0

    # 4. Bandwidth coverage 500 MHz-10 GHz
    bw = results["bandwidth"]
    bw_ratio = min(max((bw - 5e8) / (10e9 - 5e8), 0.0), 1.0)
    fitness += bw_ratio * 2.0

    # 5. Reconfigurability
    fitness += results["reconfigurable"] * 2.0

    # 6. Physical size (<10mm)
    size_ratio = min(candidate.size / 10.0, 1.5)
    fitness += (1.5 - size_ratio) * 1.0

    return fitness


def meets_goals(candidate: Candidate) -> bool:
    m = candidate.metrics
    return (
        m.get("insertion_loss", 1.0) <= 0.1 and
        m.get("isolation", 0.0) >= 40.0 and
        m.get("vswr", 2.0) <= 1.05 and
        5e8 <= m.get("bandwidth", 0.0) <= 10e9 and
        m.get("reconfigurable", 0.0) >= 1.0 and
        candidate.size <= 10.0
    )


def mutate(candidate: Candidate) -> Candidate:
    return Candidate(
        stub_length=candidate.stub_length * random.uniform(0.9, 1.1),
        resistor_value=candidate.resistor_value * random.uniform(0.9, 1.1),
        trace_width=candidate.trace_width * random.uniform(0.9, 1.1),
        topology=random.choice([candidate.topology, "alt"]),
        size=candidate.size * random.uniform(0.9, 1.1),
    )


def crossover(a: Candidate, b: Candidate) -> Candidate:
    return Candidate(
        stub_length=random.choice([a.stub_length, b.stub_length]),
        resistor_value=random.choice([a.resistor_value, b.resistor_value]),
        trace_width=random.choice([a.trace_width, b.trace_width]),
        topology=random.choice([a.topology, b.topology]),
        size=random.choice([a.size, b.size])
    )


def evolve(population: List[Candidate], generations: int = 50, elite: int = 5) -> Candidate:
    """Evolve population and print progress information."""
    best_so_far = 0.0
    best_candidate = None
    for gen in range(1, generations + 1):
        for cand in population:
            cand.fitness = evaluate(cand)
        population.sort(key=lambda c: c.fitness, reverse=True)

        # Print a message each generation so the user sees progress
        print(f"[gen {gen}] best {population[0].fitness:.3f}")

        # Highlight significant fitness improvements
        if population[0].fitness > best_so_far * 1.1:
            best_so_far = population[0].fitness
            best_candidate = population[0]
            save_candidate(best_candidate, "best_candidate.json")
            print(f"[gen {gen}] Fitness increase 10% -> {best_so_far:.3f}")
            print("  metrics:", json.dumps(best_candidate.metrics, indent=2))

        if gen % 100 == 0:
            print(f"[gen {gen}] Current best fitness {population[0].fitness:.3f}")
            print("  metrics:", json.dumps(population[0].metrics, indent=2))

        if meets_goals(population[0]):
            best_candidate = population[0]
            save_candidate(best_candidate, "best_candidate.json")
            print(f"[gen {gen}] Goals satisfied!")
            print("  metrics:", json.dumps(best_candidate.metrics, indent=2))
            return best_candidate

        next_gen = population[:elite]
        while len(next_gen) < len(population):
            parents = random.sample(population[:10], 2)
            child = crossover(*parents)
            if random.random() < 0.3:
                child = mutate(child)
            next_gen.append(child)
        population = next_gen

    best_candidate = population[0]
    save_candidate(best_candidate, "best_candidate.json")
    print("Evolution finished")
    return best_candidate


if __name__ == "__main__":
    # Initial population
    population = [
        Candidate(
            stub_length=random.uniform(1.0, 10.0),
            resistor_value=random.uniform(90.0, 110.0),
            trace_width=random.uniform(0.5, 3.0),
            topology="std",
            size=random.uniform(6.0, 12.0)
        )
        for _ in range(20)
    ]
    best = evolve(population, generations=100)
    print(json.dumps(asdict(best), indent=2))
    print("Best candidate saved to best_candidate.json")
