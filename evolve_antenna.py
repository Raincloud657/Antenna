import os
import re
import json
import random
import hashlib
import shutil
from pathlib import Path

try:
    import pyvista as pv
    import numpy as np
except Exception:
    pv = None

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "cache"
CACHE_DIR.mkdir(exist_ok=True)

TEMP_DIR = ROOT / "tmp_sim"

WIDTH_RE = re.compile(r"patch\.width\s*=\s*([0-9eE.+-]+)")
LENGTH_RE = re.compile(r"patch\.length\s*=\s*([0-9eE.+-]+)")


def scan_examples():
    examples = []
    for path in ROOT.rglob("*.m"):
        text = path.read_text(errors="ignore")
        m_w = WIDTH_RE.search(text)
        m_l = LENGTH_RE.search(text)
        if m_w and m_l:
            examples.append({
                "file": str(path.relative_to(ROOT)),
                "width": float(m_w.group(1)),
                "length": float(m_l.group(1)),
            })
    return examples


def mutate(params, scale=0.05):
    new_p = params.copy()
    for k in ("width", "length"):
        delta = random.uniform(-scale, scale) * params[k]
        new_p[k] += delta
    return new_p


def export_geometry(params, out_path):
    if pv is None:
        return
    w, l = params["width"], params["length"]
    points = np.array([
        [-w/2, -l/2, 0],
        [ w/2, -l/2, 0],
        [ w/2,  l/2, 0],
        [-w/2,  l/2, 0],
    ])
    faces = np.hstack([[4, 0, 1, 2, 3]])
    mesh = pv.PolyData(points, faces)
    mesh.save(out_path)


def cache_key(params):
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()


def simulate(params):
    key = cache_key(params)
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())

    # clean temp dir
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir()

    # placeholder for openEMS call
    random.seed(int(key[:8], 16))
    s11 = random.uniform(-40, -10)  # dB
    result = {"s11_db": s11}

    export_geometry(params, TEMP_DIR / "geometry.vtk")

    cache_file.write_text(json.dumps(result))
    shutil.rmtree(TEMP_DIR)
    return result


def run_generation(base_params, n=10):
    variants = []
    for _ in range(n):
        p = mutate(base_params)
        res = simulate(p)
        variants.append((p, res))
    return variants


def leaderboard():
    data = []
    for f in CACHE_DIR.glob("*.json"):
        params = json.loads(f.read_text())
        data.append((params["s11_db"], f.stem))
    data.sort()
    print("\nLeaderboard (best S11 at 2.4GHz):")
    for i, (val, key) in enumerate(data[:10], 1):
        print(f"{i:2d}. {key} -> {val:.2f} dB")


def main():
    ex = scan_examples()
    if not ex:
        print("No examples found")
        return
    base = random.choice(ex)
    print("Selected base design:", base["file"], "width=", base["width"], "length=", base["length"])
    run_generation(base, n=10)
    leaderboard()


if __name__ == "__main__":
    main()
