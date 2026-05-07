use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
use nalgebra::{DMatrix, SMatrix, Vector3};

type Point3D = Vector3<f64>;

// ── Matrix-based approach (current) ─────────────────────────────────────────

fn project_matrix(points: &[Point3D], azimuth: f64, elevation: f64) -> Vec<Point3D> {
    let flat: Vec<f64> = points.iter().flat_map(|p| [p.x, p.y, p.z]).collect();
    let p = DMatrix::from_row_slice(points.len(), 3, &flat);

    let dx = -(azimuth.to_radians().sin() / elevation.to_radians().tan());
    let dy = -(azimuth.to_radians().cos() / elevation.to_radians().tan());

    let m = SMatrix::<f64, 3, 3>::new(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, dx, dy, 0.0);

    let projected = p * m;
    projected
        .row_iter()
        .map(|row| Point3D::new(row[0], row[1], row[2]))
        .collect()
}

// ── Per-point approach (proposed) ────────────────────────────────────────────

fn project_per_point(points: &[Point3D], azimuth: f64, elevation: f64) -> Vec<Point3D> {
    let az = azimuth.to_radians();
    let el = elevation.to_radians();
    let dx = -(az.sin() / el.tan());
    let dy = -(az.cos() / el.tan());

    let mut result = Vec::with_capacity(points.len());
    for p in points {
        result.push(Point3D::new(p.x + dx * p.z, p.y + dy * p.z, 0.0));
    }
    result
}

// ── Fixture ──────────────────────────────────────────────────────────────────

fn make_points(n: usize) -> Vec<Point3D> {
    (0..n)
        .map(|i| {
            let t = i as f64 * 0.01;
            Point3D::new(t.sin(), t.cos(), t * 0.1)
        })
        .collect()
}

// ── Benchmarks ───────────────────────────────────────────────────────────────

fn bench_projection(c: &mut Criterion) {
    let azimuth = 45.0_f64;
    let elevation = 60.0_f64;

    let mut group = c.benchmark_group("project_points_to_ground");

    for n in [10, 50, 100, 127, 200] {
        let points = make_points(n);

        group.bench_with_input(BenchmarkId::new("matrix", n), &points, |b, pts| {
            b.iter(|| project_matrix(black_box(pts), black_box(azimuth), black_box(elevation)))
        });

        group.bench_with_input(BenchmarkId::new("per_point", n), &points, |b, pts| {
            b.iter(|| project_per_point(black_box(pts), black_box(azimuth), black_box(elevation)))
        });
    }

    group.finish();
}

criterion_group!(benches, bench_projection);
criterion_main!(benches);
