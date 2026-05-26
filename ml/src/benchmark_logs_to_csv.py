from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"
OUTPUT_DIR = REPO_ROOT / "datasets"

TIMEHIST_PATTERN = re.compile(r"_timehist\.log$")
LATENCY_PATTERN = re.compile(r"_latency\.log$")
CPUINFO_NAME = "cpuinfo"

BENCHMARK_DIR_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_(?P<workload>.+?)_(?P<scheduler>scx_[^_]+)$"
)


def parse_benchmark_dirname(directory: Path) -> str:
    match = BENCHMARK_DIR_PATTERN.match(directory.name)
    if match:
        workload = match.group("workload")
        scheduler = match.group("scheduler")
        return f"{workload}_{scheduler}"

    normalized = re.sub(r"[^0-9A-Za-z_-]+", "_", directory.name)
    return normalized


def split_table_columns(line: str) -> list[str]:
    return [cell.strip() for cell in re.split(r"\s{2,}", line.strip()) if cell.strip()]


def parse_timehist(lines: Iterable[str]) -> tuple[list[str], list[list[str]]]:
    rows: list[list[str]] = []
    header: list[str] = []
    seen_header = False

    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip() or line.startswith("-"):
            continue
        if line.strip().startswith("Runtime summary"):
            continue

        cells = split_table_columns(line)
        if not cells:
            continue

        if not seen_header:
            header = [c.replace(" ", "_") for c in cells]
            seen_header = True
            continue

        if len(cells) >= len(header):
            rows.append(cells)

    return header, rows


def parse_latency(lines: Iterable[str]) -> tuple[list[str], list[list[str]]]:
    rows: list[list[str]] = []
    header: list[str] = []
    seen_header = False

    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip() or line.startswith("-"):
            continue
        if line.strip().startswith("Task") and "|" in line:
            header = [cell.strip().replace(" ", "_") for cell in line.split("|") if cell.strip()]
            seen_header = True
            continue

        if not seen_header:
            continue

        if "|" not in line:
            continue

        cells = [cell.strip() for cell in line.split("|") if cell.strip()]
        if len(cells) >= len(header):
            rows.append(cells)

    return header, rows


def parse_cpuinfo(lines: Iterable[str]) -> tuple[list[str], list[list[str]]]:
    row = {}
    for raw in lines:
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        name = key.strip().replace(" ", "_").replace("/", "_")
        row[name] = value.strip()

    header = sorted(row.keys())
    return header, [[row[col] for col in header]]


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def convert_file(log_file: Path, output_file: Path) -> bool:
    text = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()

    if TIMEHIST_PATTERN.search(log_file.name):
        header, rows = parse_timehist(text)
    elif LATENCY_PATTERN.search(log_file.name):
        header, rows = parse_latency(text)
    elif log_file.name == CPUINFO_NAME:
        header, rows = parse_cpuinfo(text)
    else:
        return False

    if not header or not rows:
        return False

    write_csv(output_file, header, rows)
    return True


def collect_benchmark_logs(folder: Path) -> list[Path]:
    return [
        path
        for path in sorted(folder.iterdir())
        if path.is_file() and (path.suffix == ".log" or path.name == CPUINFO_NAME)
    ]


def build_output_name(folder_name: str, log_file: Path) -> str:
    stem = log_file.stem
    if log_file.name == CPUINFO_NAME:
        stem = "cpuinfo"
    return f"{folder_name}_{stem}.csv"


def convert_all(benchmarks_dir: Path, output_dir: Path, overwrite: bool = False) -> int:
    if not benchmarks_dir.exists():
        raise FileNotFoundError(f"Benchmarks directory does not exist: {benchmarks_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    converted = 0

    for benchmark_folder in sorted(benchmarks_dir.iterdir()):
        if not benchmark_folder.is_dir():
            continue

        directory_name = parse_benchmark_dirname(benchmark_folder)
        for log_file in collect_benchmark_logs(benchmark_folder):
            output_file = output_dir / build_output_name(directory_name, log_file)
            if output_file.exists() and not overwrite:
                continue
            if convert_file(log_file, output_file):
                converted += 1

    return converted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert benchmark log files under benchmarks/ into CSV datasets."
    )
    parser.add_argument(
        "--benchmarks",
        type=Path,
        default=BENCHMARKS_DIR,
        help="Benchmark root directory. Default: benchmarks/"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR,
        help="CSV output directory. Default: datasets/"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing CSV files."
    )

    args = parser.parse_args()
    count = convert_all(args.benchmarks, args.output, overwrite=args.overwrite)
    print(f"Converted {count} benchmark log files to CSV.")


if __name__ == "__main__":
    main()
