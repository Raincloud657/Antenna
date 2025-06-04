import random

class Antenna:
    def __init__(self, width, length):
        self.width = width
        self.length = length
        self.score = self.evaluate()

    def evaluate(self):
        # Placeholder evaluation function
        return self.width * self.length

    def mutate(self):
        self.width *= random.uniform(0.8, 1.2)
        self.length *= random.uniform(0.8, 1.2)
        self.score = self.evaluate()

    def copy(self):
        return Antenna(self.width, self.length)

def evolve(initial_width=30.0, initial_length=30.0, improvement_factor=2.0, max_generations=1000):
    population = [Antenna(initial_width, initial_length)]
    baseline = population[0].score
    target = baseline * improvement_factor
    generation = 0
    while generation < max_generations:
        # Create mutant
        child = population[0].copy()
        child.mutate()
        if child.score > population[0].score:
            population[0] = child
        generation += 1
        print(f"Gen {generation}: width={population[0].width:.2f}, length={population[0].length:.2f}, score={population[0].score:.2f}")
        if population[0].score >= target:
            print(f"Target achieved after {generation} generations: {population[0].score:.2f} >= {target:.2f}")
            break
    else:
        print("Reached max generations without hitting target")

def main():
    evolve()

if __name__ == "__main__":
    main()
