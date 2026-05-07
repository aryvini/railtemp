pub mod geometry;
pub mod profiles;
pub mod types;

pub use geometry::project_points_to_ground;
pub use types::{Point3D, SunCoordinates};

use pyo3::prelude::*;

/// Python module – exposes Rust functions under `from railtemp._core import ...`.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(geometry::calculate_areas, m)?)?;
    Ok(())
}
