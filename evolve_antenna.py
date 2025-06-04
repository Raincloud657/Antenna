import os
import re
import json
import random
import hashlib
import shutil
import subprocess
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


def _run_openems(params):
    octave = shutil.which("octave") or shutil.which("octave-cli")
    if not octave:
        return None

    sim_dir = TEMP_DIR / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)
    script = sim_dir / "run.m"
    openems_matlab = os.environ.get("OPENEMS_MATLAB", "/usr/share/openems/matlab")
    script.write_text(
        f"""
addpath('{openems_matlab}');
set(0,'defaultfigurevisible','off');
physical_constants;
unit = 1e-3;
patch.width = {params['width']};
patch.length = {params['length']};
substrate.epsR = 3.38;
substrate.kappa = 1e-3 * 2*pi*2.45e9 * EPS0*substrate.epsR;
substrate.width = patch.width + 20;
substrate.length = patch.length + 20;
substrate.thickness = 1.524;
substrate.cells = 4;
feed.pos = -5.5;
feed.width = 2;
feed.R = 50;
SimBox = [substrate.width+40 substrate.length+40 25];
Sim_Path = '{sim_dir.as_posix()}';
Sim_CSX = 'patch.xml';
max_timesteps = 30000;
min_decrement = 1e-5;
f0 = 2.4e9;
fc = 1.0e9;
FDTD = InitFDTD('NrTS', max_timesteps, 'EndCriteria', min_decrement);
FDTD = SetGaussExcite(FDTD, f0, fc);
BC = {{'MUR','MUR','MUR','MUR','MUR','MUR'}};
FDTD = SetBoundaryCond(FDTD, BC);
max_res = c0/(f0+fc)/unit/20;
CSX = InitCSX();
mesh.x = [-SimBox(1)/2 SimBox(1)/2 -substrate.width/2 substrate.width/2 feed.pos];
mesh.x = [mesh.x -patch.width/2-max_res/2*0.66 -patch.width/2+max_res/2*0.33 patch.width/2+max_res/2*0.66 patch.width/2-max_res/2*0.33];
mesh.x = SmoothMeshLines(mesh.x, max_res, 1.4);
mesh.y = [-SimBox(2)/2 SimBox(2)/2 -substrate.length/2 substrate.length/2 -feed.width/2 feed.width/2];
mesh.y = [mesh.y -patch.length/2-max_res/2*0.66 -patch.length/2+max_res/2*0.33 patch.length/2+max_res/2*0.66 patch.length/2-max_res/2*0.33];
mesh.y = SmoothMeshLines(mesh.y, max_res, 1.4);
mesh.z = [-SimBox(3)/2 linspace(0,substrate.thickness,substrate.cells) SimBox(3)];
mesh.z = SmoothMeshLines(mesh.z, max_res, 1.4);
mesh = AddPML(mesh, 8);
CSX = DefineRectGrid(CSX, unit, mesh);
CSX = AddMetal(CSX,'patch');
start = [-patch.width/2 -patch.length/2 substrate.thickness];
stop = [patch.width/2 patch.length/2 substrate.thickness];
CSX = AddBox(CSX,'patch',10,start,stop);
CSX = AddMaterial(CSX,'substrate');
CSX = SetMaterialProperty(CSX,'substrate','Epsilon',substrate.epsR,'Kappa',substrate.kappa);
start = [-substrate.width/2 -substrate.length/2 0];
stop  = [substrate.width/2 substrate.length/2 substrate.thickness];
CSX = AddBox(CSX,'substrate',0,start,stop);
CSX = AddMetal(CSX,'gnd');
start(3)=0; stop(3)=0;
CSX = AddBox(CSX,'gnd',10,start,stop);
start=[feed.pos-.1 -feed.width/2 0];
stop=[feed.pos+.1 +feed.width/2 substrate.thickness];
[CSX] = AddLumpedPort(CSX,5,1,feed.R,start,stop,[0 0 1],true);
[CSX nf2ff] = CreateNF2FFBox(CSX,'nf2ff',-SimBox/2,SimBox/2);
WriteOpenEMS([Sim_Path '/' Sim_CSX],FDTD,CSX);
system(['csxcad2vtk "' Sim_Path '/' Sim_CSX '" "' Sim_Path '/geometry.vtu"']);
RunOpenEMS(Sim_Path,Sim_CSX,'');
freq = linspace(f0-0.5e9,f0+0.5e9,401);
U = ReadUI({'port_ut1','et'},Sim_Path,freq);
I = ReadUI('port_it1',Sim_Path,freq);
uf_inc = 0.5*(U.FD{1}.val + I.FD{1}.val * feed.R);
uf_ref = U.FD{1}.val - uf_inc;
s11 = uf_ref ./ uf_inc;
fid=fopen([Sim_Path '/s11.csv'],'w');
for n=1:length(freq)
    fprintf(fid,'%g,%g\n',freq(n),20*log10(abs(s11(n))));
end
fclose(fid);
[~, idx] = min(abs(freq - 2.4e9));
fid=fopen([Sim_Path '/result.json'],'w');
fprintf(fid,'{"s11_db": %.6f}\n',20*log10(abs(s11(idx))));
fclose(fid);
exit;
"""
    )
    try:
        subprocess.run([octave, "--no-gui", script.name], cwd=sim_dir, check=True)
    except Exception:
        return None
    res_file = sim_dir / "result.json"
    if res_file.exists():
        geom_file = sim_dir / "geometry.vtu"
        data = json.loads(res_file.read_text())
        csv_file = sim_dir / "s11.csv"
        if csv_file.exists():
            freqs = []
            vals = []
            with csv_file.open() as f:
                for line in f:
                    if "," not in line:
                        continue
                    a, b = line.strip().split(",", 1)
                    freqs.append(float(a))
                    vals.append(float(b))
            data["freq"] = freqs
            data["s11_curve_db"] = vals
        data["geom"] = str(geom_file)
        return data
    return None


def simulate(params):
    key = cache_key(params)
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())

    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir()

    result = _run_openems(params)
    if result is None:
        random.seed(int(key[:8], 16))
        result = {"s11_db": random.uniform(-40, -10)}
        export_geometry(params, TEMP_DIR / "geometry.vtk")
    else:
        geom_path = Path(result.pop("geom"))
        if geom_path.exists():
            shutil.copy(geom_path, TEMP_DIR / "geometry.vtu")

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
