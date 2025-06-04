import os
import subprocess
import random
import statistics
from tempfile import NamedTemporaryFile

class AntennaSimulator:
    """Run openEMS simulations using an Octave template."""
    def __init__(self, template_path):
        self.template_path = template_path

    def simulate(self, params):
        """Run the simulation with given parameters and return metrics."""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        script = template.format(
            WIDTH=params['width'],
            LENGTH=params['length'],
            FEED_POS=params['feed_pos'],
            FEED_WIDTH=params['feed_width']
        )
        with NamedTemporaryFile('w', suffix='.m', delete=False) as tmp:
            tmp.write(script)
            tmp_path = tmp.name
        try:
            result = subprocess.run(
                ['octave', '--quiet', tmp_path],
                capture_output=True, text=True, check=False
            )
        finally:
            os.remove(tmp_path)
        directivity = None
        power = None
        for line in result.stdout.splitlines():
            if 'directivity:' in line:
                try:
                    directivity = float(line.split('=')[1].split()[0])
                except (IndexError, ValueError):
                    pass
            if 'radiated power:' in line:
                try:
                    power = float(line.split('=')[1].split()[0])
                except (IndexError, ValueError):
                    pass
        if directivity is None:
            raise RuntimeError('Failed to parse simulation output:\n' + result.stdout)
        return {
            'directivity': directivity,
            'power': power,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
        }

def mutate(params, sigma=0.05):
    """Return a mutated copy of the parameter dictionary."""
    return {
        'width': max(1.0, random.gauss(params['width'], params['width'] * sigma)),
        'length': max(1.0, random.gauss(params['length'], params['length'] * sigma)),
        'feed_pos': random.gauss(params['feed_pos'], abs(params['feed_pos']) * sigma),
        'feed_width': max(0.1, random.gauss(params['feed_width'], params['feed_width'] * sigma)),
    }

def evolve(initial_params, template_path, target_factor=2.0, population=4, max_generations=50):
    """Simple evolutionary search for improved directivity."""
    sim = AntennaSimulator(template_path)
    metrics = sim.simulate(initial_params)
    baseline = metrics['directivity']
    best_params = initial_params.copy()
    best_score = baseline
    generation = 0
    avg_score = baseline
    history = []
    while avg_score < baseline * target_factor and generation < max_generations:
        candidates = []
        for _ in range(population):
            p = mutate(best_params)
            m = sim.simulate(p)
            p['score'] = m['directivity']
            candidates.append(p)
        avg_score = statistics.mean(c['score'] for c in candidates)
        candidates.sort(key=lambda c: c['score'], reverse=True)
        best_params = candidates[0]
        best_score = best_params['score']
        generation += 1
        history.append({'generation': generation, 'best': best_score, 'average': avg_score})
    return best_params, history

if __name__ == '__main__':
    params = {
        'width': 32.86,
        'length': 41.37,
        'feed_pos': -5.5,
        'feed_width': 2.0,
    }
    template = os.path.join(os.path.dirname(__file__), 'patch_template.m')
    try:
        best, hist = evolve(params, template)
        for h in hist:
            print(f"Generation {h['generation']}: avg={h['average']:.2f} best={h['best']:.2f}")
        print('Best parameters:', best)
    except FileNotFoundError:
        print('Octave not found. Install Octave to run simulations.')
