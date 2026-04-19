"""
profiling.py — Performance profiling for a single CNU simulation run.

Run from the repository root:
    python profiling.py

Outputs:
  1. cProfile table sorted by cumulative time (console)
  2. profiling_output.prof  — binary profile file (open with snakeviz, tuna, etc.)
  3. Backend comparison: Python vs Rust over N repeated runs
  4. Per-phase timing breakdown for each backend

Visualise with:
    pip install snakeviz
    snakeviz profiling_output.prof
"""

import cProfile
import functools
import io
import pstats
import statistics
import time

import pandas as pd
import pytz

from railtemp.railtemp import Rail, RailMaterial, WeatherData, CNU
from railtemp.ParameterValue import (
    BetaParameterValue,
    ClippedNormalParameterValue,
    RandomParameterMode,
    UniformParameterValue,
)
from railtemp.solver_backend import SolverBackend, available_backends, is_available

# ---------------------------------------------------------------------------
# Build the simulation objects (same setup as test_Montecarlo.py)
# ---------------------------------------------------------------------------

INPUT_CSV = "./tests/artifacts/input_montecarlo.csv"
TRAIL_INITIAL = 21.5  # matches first ambient_temperature row in the CSV
N_REPEATS = 20  # number of timed repetitions per backend


class SpecificHeatWrapper:
    def __init__(self):
        sh = UniformParameterValue(439, 487).set_mode(RandomParameterMode.FIXED_GLOBAL)
        self.constant = sh.get_value()

    def get(self, _):
        return self.constant


def build_simulation(backend: SolverBackend | None = None) -> CNU:
    DensityD = UniformParameterValue(7840, 7860).set_mode(RandomParameterMode.VARIABLE)
    SolarAbsD = BetaParameterValue(alpha=5, beta=2).set_mode(RandomParameterMode.FIXED_PER_RUN)
    RailEmiss = BetaParameterValue(mean=0.7, sigma=0.1).set_mode(RandomParameterMode.FIXED_GLOBAL)
    ConvectionAreaD = ClippedNormalParameterValue(0.43046, 0.05, 0, 0.43046).set_mode(
        RandomParameterMode.FIXED_PER_RUN
    )
    RadiationAreaD = ClippedNormalParameterValue(0.43046, 0.05, 0, 0.43046).set_mode(
        RandomParameterMode.FIXED_GLOBAL
    )
    AmbientEmiss = BetaParameterValue(mean=0.5, sigma=0.1).set_mode(
        RandomParameterMode.FIXED_GLOBAL
    )

    steel = RailMaterial(
        density=DensityD,
        solar_absort=SolarAbsD,
        emissivity=RailEmiss,
        specific_heat=SpecificHeatWrapper().get,
    )

    rail = Rail(
        name="UIC54",
        azimuth=93,
        lat=41.482628,
        long=-7.183741,
        elev=220,
        cross_area=7.16e-3,
        convection_area=ConvectionAreaD,
        radiation_area=RadiationAreaD,
        ambient_emissivity=AmbientEmiss,
        material=steel,
    )

    df = pd.read_csv(INPUT_CSV, parse_dates=["record_date"], index_col="record_date")
    weather = WeatherData(
        solar_radiation=df["solar_radiation"],
        wind_velocity=df["wv_avg"],
        ambient_temperature=df["ambient_temperature"],
        timezone=pytz.timezone("Europe/Lisbon"),
    )

    return CNU(rail=rail, weather=weather, backend=backend)


# ---------------------------------------------------------------------------
# Warm-up run (builds caches, avoids first-import noise in the profile)
# ---------------------------------------------------------------------------

print("Warm-up run (not profiled)...")
t0 = time.perf_counter()
build_simulation().run(Trail_initial=TRAIL_INITIAL)
print(f"  Warm-up finished in {time.perf_counter() - t0:.2f}s\n")

# ---------------------------------------------------------------------------
# Profiled run  (Python backend — reference)
# ---------------------------------------------------------------------------

print("Profiled run (Python backend)...")
profiler = cProfile.Profile()
profiler.enable()

simu = build_simulation()
simu.run(Trail_initial=TRAIL_INITIAL)

profiler.disable()
print("Done.\n")

# ---------------------------------------------------------------------------
# Print top-40 functions by cumulative time
# ---------------------------------------------------------------------------

stream = io.StringIO()
stats = pstats.Stats(profiler, stream=stream)
stats.strip_dirs()
stats.sort_stats("cumulative")
stats.print_stats(40)

report = stream.getvalue()
print(report)

# ---------------------------------------------------------------------------
# Save binary profile for visualisation tools
# ---------------------------------------------------------------------------

PROF_FILE = "profiling_output.prof"
profiler.dump_stats(PROF_FILE)
print(f"Binary profile saved to '{PROF_FILE}'")
print("Visualise with:  snakeviz profiling_output.prof")

# ---------------------------------------------------------------------------
# Per-phase timing breakdown (manual stopwatch around each CNU internal step)
# ---------------------------------------------------------------------------

timings: dict[str, float] = {}


def timed_method(name, fn, obj):
    """Wrap a bound method so it records elapsed time in `timings`."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t = time.perf_counter()
        result = fn(*args, **kwargs)
        timings[name] = time.perf_counter() - t
        return result

    return wrapper


def run_phase_breakdown(backend: SolverBackend) -> dict[str, float]:
    """Run one simulation with per-method stopwatches; return the timings dict."""
    local_timings: dict[str, float] = {}
    sim = build_simulation(backend=backend)

    for method_name in [
        "_CNU__celsius_to_kelvin",
        "_CNU__calculate_hconv",
        "_CNU__fetch_solar_data",
        "_CNU__calculate_As",
        "_CNU__create_delta_time_columns",
        "_CNU__initial_conditions",
        "_CNU__solve",
        "_CNU__kelvin_to_celsius",
    ]:
        original = getattr(sim, method_name)

        @functools.wraps(original)
        def _make_wrapper(n, f):
            def wrapper(*args, **kwargs):
                t = time.perf_counter()
                result = f(*args, **kwargs)
                local_timings[n] = time.perf_counter() - t
                return result

            return wrapper

        setattr(sim, method_name, _make_wrapper(method_name, original))

    sim.run(Trail_initial=TRAIL_INITIAL)
    return local_timings


def print_phase_table(label: str, timings: dict[str, float]) -> None:
    total = sum(timings.values())
    print(f"\n  Backend: {label}")
    print(f"  {'Method':<40} {'Time (s)':>10} {'% of total':>12}")
    print("  " + "-" * 65)
    for name, elapsed in sorted(timings.items(), key=lambda x: -x[1]):
        short = name.replace("_CNU__", "")
        pct = (elapsed / total * 100) if total > 0 else 0
        print(f"    {short:<38} {elapsed:>10.4f} {pct:>11.1f}%")
    print(f"\n    {'TOTAL':<38} {total:>10.4f}")


print("\n" + "=" * 65)
print("  PER-PHASE TIMING BREAKDOWN")
print("=" * 65)

py_phase = run_phase_breakdown(SolverBackend.PYTHON)
print_phase_table("PYTHON", py_phase)

if is_available(SolverBackend.RUST):
    rust_phase = run_phase_breakdown(SolverBackend.RUST)
    print_phase_table("RUST", rust_phase)

    py_solve = py_phase.get("_CNU__solve", 0)
    rs_solve = rust_phase.get("_CNU__solve", 0)
    if rs_solve > 0:
        print(f"\n  __solve speedup (Python / Rust): {py_solve / rs_solve:.1f}×")
else:
    print("\n  [Rust backend not available — skipping Rust phase breakdown]")

if is_available(SolverBackend.RUST_BDF):
    bdf_phase = run_phase_breakdown(SolverBackend.RUST_BDF)
    print_phase_table("RUST_BDF", bdf_phase)

    py_solve = py_phase.get("_CNU__solve", 0)
    bdf_solve = bdf_phase.get("_CNU__solve", 0)
    if bdf_solve > 0:
        print(f"\n  __solve speedup (Python / Rust-BDF): {py_solve / bdf_solve:.1f}×")
else:
    print("\n  [Rust-BDF backend not available — skipping]")

# ---------------------------------------------------------------------------
# Backend comparison: repeated runs
# ---------------------------------------------------------------------------

print("\n" + "=" * 65)
print(f"  BACKEND COMPARISON  ({N_REPEATS} runs each)")
print("=" * 65)


def time_backend(backend: SolverBackend, n: int) -> list[float]:
    """Run the full simulation n times and return elapsed seconds per run."""
    samples: list[float] = []
    for _ in range(n):
        sim = build_simulation(backend=backend)
        t0 = time.perf_counter()
        sim.run(Trail_initial=TRAIL_INITIAL)
        samples.append(time.perf_counter() - t0)
    return samples


backends_to_bench = [b for b in available_backends()]
results: dict[str, list[float]] = {}

for backend in backends_to_bench:
    print(f"\n  Timing {backend.name} backend ({N_REPEATS} runs) …", flush=True)
    samples = time_backend(backend, N_REPEATS)
    results[backend.name] = samples
    mean = statistics.mean(samples)
    med = statistics.median(samples)
    stdev = statistics.stdev(samples) if len(samples) > 1 else 0.0
    print(
        f"    mean={mean:.4f}s  median={med:.4f}s  stdev={stdev:.4f}s  "
        f"min={min(samples):.4f}s  max={max(samples):.4f}s"
    )

# Summary table
print("\n" + "-" * 65)
print(
    f"  {'Backend':<12} {'Mean (s)':>10} {'Median (s)':>12} {'Stdev (s)':>10} {'Min (s)':>9} {'Max (s)':>9}"
)
print("  " + "-" * 63)
for name, samples in results.items():
    print(
        f"  {name:<12} {statistics.mean(samples):>10.4f} "
        f"{statistics.median(samples):>12.4f} "
        f"{(statistics.stdev(samples) if len(samples) > 1 else 0):>10.4f} "
        f"{min(samples):>9.4f} {max(samples):>9.4f}"
    )

if "PYTHON" in results and "RUST" in results:
    speedup = statistics.mean(results["PYTHON"]) / statistics.mean(results["RUST"])
    print(f"\n  ⚡ Rust is {speedup:.2f}× faster than Python (mean over {N_REPEATS} runs)")
    proj_py = statistics.mean(results["PYTHON"]) * 3_000_000
    proj_rs = statistics.mean(results["RUST"]) * 3_000_000
    print("\n  Projected time for 3,000,000 MC scenarios:")
    print(f"    Python   : {proj_py / 3600:>7.1f} hours  ({proj_py:,.0f}s)")
    print(f"    Rust     : {proj_rs / 3600:>7.1f} hours  ({proj_rs:,.0f}s)")
    print(f"    Saving   : {(proj_py - proj_rs) / 3600:.1f} hours")

if "PYTHON" in results and "RUST_BDF" in results:
    speedup = statistics.mean(results["PYTHON"]) / statistics.mean(results["RUST_BDF"])
    proj_py = statistics.mean(results["PYTHON"]) * 3_000_000
    proj_bdf = statistics.mean(results["RUST_BDF"]) * 3_000_000
    print(f"\n  ⚡ Rust-BDF is {speedup:.2f}× faster than Python (mean over {N_REPEATS} runs)")
    print(f"    Python   : {proj_py / 3600:>7.1f} hours  ({proj_py:,.0f}s)")
    print(f"    Rust-BDF : {proj_bdf / 3600:>7.1f} hours  ({proj_bdf:,.0f}s)")
    print(f"    Saving   : {(proj_py - proj_bdf) / 3600:.1f} hours")

if "RUST" in results and "RUST_BDF" in results:
    r_mean = statistics.mean(results["RUST"])
    bdf_mean = statistics.mean(results["RUST_BDF"])
    ratio = r_mean / bdf_mean if bdf_mean > 0 else float("nan")
    print(
        f"\n  Rust-secant vs Rust-BDF: {'BDF is' if ratio > 1 else 'Secant is'} {abs(ratio):.2f}× {'faster' if ratio > 1 else 'slower'}"
    )
