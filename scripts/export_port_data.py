import argparse
from pathlib import Path
import csv
import re

HEADER_RE = re.compile(r"% .* current|voltage.*")


def parse_port_file(path):
    times = []
    values = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    t = float(parts[0])
                    v = float(parts[1])
                except ValueError:
                    continue
                times.append(t)
                values.append(v)
    return times, values


def export_to_csv(port_file, output):
    times, values = parse_port_file(port_file)
    with open(output, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time', 'value'])
        writer.writerows(zip(times, values))


def main():
    parser = argparse.ArgumentParser(description="Export openEMS port data to CSV")
    parser.add_argument('port_files', nargs='+', help='Paths to port_ut1, port_it1, etc.')
    parser.add_argument('--out-dir', default='.', help='Directory to store CSV files')
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for port_path in args.port_files:
        port_path = Path(port_path)
        if not port_path.is_file():
            print(f"warning: {port_path} not found")
            continue
        out_file = out_dir / f"{port_path.name}.csv"
        export_to_csv(port_path, out_file)
        print(f"wrote {out_file}")


if __name__ == '__main__':
    main()
