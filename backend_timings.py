"""
Benchmark: Python vs Rust backend performance for railtemp simulation.

Run with:
    python backend_timings.py
"""

import timeit
import statistics
import pandas as pd
import pytz
from railtemp.railtemp import CNU, Rail, RailMaterial, WeatherData

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

INPUT_DATA = "./tests/artifacts/input_data.csv"
RUNS = 15  # number of timed repetitions


def _load_fixtures():
    df = pd.read_csv(INPUT_DATA)
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)

    steel = RailMaterial(density=7850, solar_absort=0.8, emissivity=0.7)
    rail = Rail(
        name="UIC54",
        azimuth=93,
        lat=41.482628,
        long=-7.183741,
        elev=220,
        cross_area=7.16e-3,
        convection_area=430.46e-3,
        radiation_area=430.46e-3,
        ambient_emissivity=0.5,
        material=steel,
    )
    weather = WeatherData(
        solar_radiation=df["SR"],
        wind_velocity=df["Wv_avg"],
        ambient_temperature=df["TA"],
        timezone=pytz.timezone("Europe/Lisbon"),
    )
    return rail, weather


def _run(backend: str, rail, weather) -> None:
    simu = CNU(rail=rail, weather=weather)
    simu.run(Trail_initial=23, backend=backend)


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


def benchmark(backend: str, rail, weather, runs: int = RUNS) -> list[float]:
    """Return per-run wall-clock times (seconds) for *runs* repetitions."""
    times = []
    for _ in range(runs):
        t = timeit.timeit(lambda: _run(backend, rail, weather), number=1)
        times.append(t)
    return times


def report(label: str, times: list[float]) -> None:
    mean = statistics.mean(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0.0
    best = min(times)
    worst = max(times)
    print(f"  {label}")
    print(f"    runs : {len(times)}")
    print(f"    mean : {mean * 1000:.1f} ms")
    print(f"    stdev: {stdev * 1000:.1f} ms")
    print(f"    best : {best * 1000:.1f} ms")
    print(f"    worst: {worst * 1000:.1f} ms")


def main():
    print(f"Loading fixtures from {INPUT_DATA} ...")
    rail, weather = _load_fixtures()
    print(f"Running {RUNS} repetitions per backend.\n")

    print("Benchmarking ...")
    python_times = benchmark("python", rail, weather)
    rust_times = benchmark("rust", rail, weather)

    print("\n=== Results ===")
    report("Python backend", python_times)
    print()
    report("Rust backend  ", rust_times)

    speedup = statistics.mean(python_times) / statistics.mean(rust_times)
    print(f"\n  Speedup (Rust vs Python): {speedup:.2f}x")


if __name__ == "__main__":
    main()
