import random

def run_sim(num_generations=1000):
    fitness = 1.0
    start_fitness = fitness
    prev_fitness = fitness
    for gen in range(1, num_generations+1):
        # simulate improvement
        fitness += random.uniform(-0.01, 0.02)
        if gen % 100 == 0:
            overall_change = 100 * (fitness - start_fitness) / start_fitness
            interval_change = 100 * (fitness - prev_fitness) / prev_fitness
            print(
                f"Generation {gen}: overall change {overall_change:.2f}%, "
                f"last 100 generations {interval_change:.2f}%"
            )
            prev_fitness = fitness

if __name__ == "__main__":
    run_sim()
