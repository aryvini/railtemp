use nalgebra::Vector3;

pub type Point3D = Vector3<f64>;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct SunCoordinates {
    azimuth: f64,
    elevation: f64,
}

impl SunCoordinates {
    pub fn new(azimuth: f64, elevation: f64) -> Result<Self, String> {
        if azimuth < 0.0 || azimuth >= 360.0 {
            return Err("Azimuth must be in the range [0, 360)".to_string());
        }

        Ok(Self { azimuth, elevation })
    }

    pub fn azimuth(&self) -> f64 {
        self.azimuth
    }
    pub fn elevation(&self) -> f64 {
        self.elevation
    }
}
