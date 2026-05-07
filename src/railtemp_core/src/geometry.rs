use crate::profiles::{UIC54_PROFILE, UIC60_PROFILE};
use crate::types::{Point3D, SunCoordinates};
use chrono::FixedOffset;
use geo::{Area, ConvexHull, LineString};
use pyo3::prelude::*;
use solar_positioning::{grena3, time::DeltaT, RefractionCorrection};

pub fn project_points_to_ground(points: &Vec<Point3D>, sun: SunCoordinates) -> Vec<Point3D> {
    let kx = -(sun.azimuth().to_radians().sin() / sun.elevation().to_radians().tan());
    let ky = -(sun.azimuth().to_radians().cos() / sun.elevation().to_radians().tan());

    let mut projected_points_vec: Vec<Point3D> = Vec::with_capacity(points.len());

    for p in points {
        projected_points_vec.push(Point3D::new(p.x + kx * p.z, p.y + ky * p.z, 0.0));
    }

    projected_points_vec
}

fn convex_hull_area(points: &Vec<Point3D>) -> f64 {
    // Placeholder for convex hull area calculation
    // In a real implementation, you would compute the convex hull of the points and then calculate its area.

    // Transform vector into linestring from geo crate

    let line = LineString::new(
        points
            .iter()
            .map(|p| geo::Coord { x: p.x, y: p.y })
            .collect(),
    );

    let hull = line.convex_hull();
    let area = hull.unsigned_area();
    area
}

pub fn calculate_shadow_sun_area(
    profile: &Vec<Point3D>,
    sun: SunCoordinates,
    rail_azimuth: f64,
) -> Result<(f64, f64), String> {
    let equivalent_azimuth = (sun.azimuth() - rail_azimuth).rem_euclid(360.0);

    let equivalent_sun = SunCoordinates::new(equivalent_azimuth, sun.elevation())?;

    let projected_profile = project_points_to_ground(profile, equivalent_sun);

    let shadow_area = convex_hull_area(&projected_profile);

    let mut sun_area = shadow_area * equivalent_sun.elevation().to_radians().sin();
    if sun_area < 0.0 {
        sun_area = 0.0; // Ensure sun area is not negative
    }

    Ok((shadow_area, sun_area))
}

pub fn calculate_sun_area_from_position(
    profile: &Vec<Point3D>,
    rail_azimuth: f64,
    lat: f64,
    lon: f64,
    datetime: chrono::DateTime<FixedOffset>,
) -> Result<(f64, f64, f64), String> {
    let delta_t = DeltaT::estimate_from_date_like(datetime).map_err(|e| e.to_string())?;
    let refraction = Some(RefractionCorrection::standard());

    let sun = match grena3::solar_position(datetime, lat, lon, delta_t, refraction) {
        Ok(s) => s,
        Err(e) => return Err(format!("Error calculating solar position: {}", e)),
    };

    let sun_coordinates = SunCoordinates::new(sun.azimuth(), sun.elevation_angle())?;
    dbg!("Calculated sun coordinates: {:?}", sun_coordinates);
    let (_, sun_area) = calculate_shadow_sun_area(profile, sun_coordinates, rail_azimuth)?;
    Ok((sun_area, sun.azimuth(), sun.elevation_angle()))
}

#[pyfunction]
pub fn calculate_areas(
    profile: String,
    lat: f64,
    long: f64,
    azimuth: f64,
    time: Vec<String>,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let mut sun_areas: Vec<f64> = Vec::with_capacity(time.len());
    let mut azimuths: Vec<f64> = Vec::with_capacity(time.len());
    let mut elevations: Vec<f64> = Vec::with_capacity(time.len());
    let profile_vector = match profile.as_str() {
        "UIC54" => UIC54_PROFILE.to_vec(),
        "UIC60" => UIC60_PROFILE.to_vec(),
        _ => {
            !panic!("Unsupported profile: {}", profile);
        }
    };

    for t in time {
        let datetime = match t.parse::<chrono::DateTime<FixedOffset>>() {
            Ok(dt) => dt,
            Err(e) => {
                eprintln!("Error parsing datetime '{}': {}", t, e);
                sun_areas.push(0.0);
                azimuths.push(0.0);
                elevations.push(0.0);
                continue;
            }
        };

        match calculate_sun_area_from_position(&profile_vector, azimuth, lat, long, datetime) {
            Ok((sun_area, azimuth, elevation)) => {
                sun_areas.push(sun_area);
                azimuths.push(azimuth);
                elevations.push(elevation);
            }
            Err(e) => {
                eprintln!("Error calculating sun area for time '{}': {}", t, e);
                sun_areas.push(0.0);
                azimuths.push(0.0);
                elevations.push(0.0);
            }
        }
    }

    return (sun_areas, azimuths, elevations);
}

#[cfg(test)]
mod tests {
    use crate::profiles::{UIC54_PROFILE, UIC60_PROFILE};
    use chrono::FixedOffset;
    use pyo3::pyfunction;

    use super::{
        calculate_shadow_sun_area, calculate_sun_area_from_position, convex_hull_area,
        project_points_to_ground,
    };
    use crate::types::{Point3D, SunCoordinates};

    use std::iter::zip;

    #[test]
    fn project2ground_projects_point_using_sun_coordinates() {
        let cases = vec![
            (
                Point3D::new(2.0, 1.0, 1.0),
                (0.0, 60.0),
                Point3D::new(2.0, 0.42264973081037405, 0.0),
            ),
            (
                Point3D::new(2.0, 1.0, 1.0),
                (45.0, 60.0),
                Point3D::new(1.5917517095361369, 0.5917517095361369, 0.0),
            ),
            (
                Point3D::new(2.0, 1.0, 1.0),
                (90.0, 60.0),
                Point3D::new(1.422649730810374, 1.0, 0.0),
            ),
            (
                Point3D::new(2.0, 1.0, 1.0),
                (135.0, 60.0),
                Point3D::new(1.5917517095361369, 1.4082482904638631, 0.0),
            ),
            (
                Point3D::new(2.0, 1.0, 1.0),
                (180.0, 60.0),
                Point3D::new(2.0, 1.577350269189626, 0.0),
            ),
            (
                Point3D::new(2.0, 1.0, 1.0),
                (225.0, 60.0),
                Point3D::new(2.408248290463863, 1.4082482904638631, 0.0),
            ),
            (
                Point3D::new(2.0, 1.0, 1.0),
                (270.0, 60.0),
                Point3D::new(2.577350269189626, 1.0, 0.0),
            ),
            (
                Point3D::new(2.0, 1.0, 1.0),
                (315.0, 60.0),
                Point3D::new(2.408248290463863, 0.591751709536137, 0.0),
            ),
        ];

        let eps = 1e-9;
        for (input, (azimuth, elevation), expected) in cases {
            let sun = SunCoordinates::new(azimuth, elevation).unwrap();
            let projected = project_points_to_ground(&vec![input], sun)[0];

            dbg!("Projected: {:?}, Expected: {:?}", projected, expected);
            assert!((projected.x - expected.x).abs() < eps);
            assert!((projected.y - expected.y).abs() < eps);
            assert!((projected.z - expected.z).abs() < eps);
        }
    }

    #[test]
    fn test_project_points_to_ground() {
        let points = vec![
            Point3D::new(2.0, 1.0, 1.0),
            Point3D::new(3.0, 2.0, 1.0),
            Point3D::new(4.0, 3.0, 1.0),
        ];
        let sun = SunCoordinates::new(45.0, 60.0).unwrap();

        let projected_points = project_points_to_ground(&points, sun);

        let expected_points = vec![
            Point3D::new(1.5917517095361369, 0.5917517095361369, 0.0),
            Point3D::new(2.591751709536137, 1.5917517095361369, 0.0),
            Point3D::new(3.591751709536137, 2.591751709536137, 0.0),
        ];

        let eps = 1e-9;
        for (proj, exp) in zip(projected_points.iter(), expected_points.iter()) {
            dbg!("Projected: {:?}, Expected: {:?}", proj, exp);
            assert!((proj.x - exp.x).abs() < eps);
            assert!((proj.y - exp.y).abs() < eps);
            assert!((proj.z - exp.z).abs() < eps);
        }
    }

    #[test]
    fn test_all_points_on_ground() {
        let points = vec![
            Point3D::new(2.0, 1.0, 1.0),
            Point3D::new(3.0, 2.0, 1.0),
            Point3D::new(4.0, 3.0, 1.0),
        ];
        let sun = SunCoordinates::new(45.0, 60.0).unwrap();

        let projected_points = project_points_to_ground(&points, sun);

        for p in projected_points {
            assert!(p.z.abs() < 1e-9);
        }
    }

    #[test]
    fn test_convex_hull() {
        let sun = SunCoordinates::new(15.0, 60.0).unwrap();
        let project_profile_uic60 = project_points_to_ground(&UIC60_PROFILE.to_vec(), sun);

        let area = convex_hull_area(&project_profile_uic60);

        let eps = 1e-9;
        assert!((area - 0.1613229146819561).abs() < eps);
    }

    #[test]
    fn test_shadow_area_sun_area() {
        let (shadow_area, sun_area) = calculate_shadow_sun_area(
            &UIC60_PROFILE.to_vec(),
            SunCoordinates::new(15.0, 60.0).unwrap(),
            0.0,
        )
        .unwrap();

        let eps = 1e-9;
        assert!((shadow_area - 0.1613229146819561).abs() < eps);
        assert!((sun_area - 0.13970974232712355).abs() < eps);

        let (shadow_area, sun_area) = calculate_shadow_sun_area(
            &UIC60_PROFILE.to_vec(),
            SunCoordinates::new(15.0, 10.0).unwrap(),
            35.0,
        )
        .unwrap();

        assert!((shadow_area - 0.5283836218335604).abs() < eps);
        assert!((sun_area - 0.09175285304045022).abs() < eps);

        let (shadow_area, sun_area) = calculate_shadow_sun_area(
            &UIC60_PROFILE.to_vec(),
            SunCoordinates::new(15.0, 90.0).unwrap(),
            77.7,
        )
        .unwrap();

        assert!((shadow_area - 0.15).abs() < eps);
        assert!((sun_area - 0.15).abs() < eps);

        let (shadow_area, sun_area) = calculate_shadow_sun_area(
            &UIC60_PROFILE.to_vec(),
            SunCoordinates::new(15.0, 25.0).unwrap(),
            77.7,
        )
        .unwrap();

        assert!((shadow_area - 0.4413487451473862).abs() < eps);
        assert!((sun_area - 0.18652203949562732).abs() < eps);
    }

    #[test]
    fn test_calculate_sun_area_from_position() {
        let (lat, lon) = (41.482628, -7.183741);
        let rail_azimuth = 93.0;

        let datetime = "2020-08-09T12:05:00+01:00"
            .parse::<chrono::DateTime<FixedOffset>>()
            .unwrap();

        let (sun_area, _, _) = calculate_sun_area_from_position(
            &UIC54_PROFILE.to_vec(),
            rail_azimuth,
            lat,
            lon,
            datetime,
        )
        .unwrap();

        assert!((sun_area - 0.14894605421960894).abs() < 1e-3);

        let datetime = "2020-08-09T14:15:00+01:00"
            .parse::<chrono::DateTime<FixedOffset>>()
            .unwrap();

        let (sun_area, _, _) = calculate_sun_area_from_position(
            &UIC54_PROFILE.to_vec(),
            rail_azimuth,
            lat,
            lon,
            datetime,
        )
        .unwrap();

        assert!((sun_area - 0.15941019292599917).abs() < 1e-3);

        let datetime = "2020-08-09T19:45:00+01:00"
            .parse::<chrono::DateTime<FixedOffset>>()
            .unwrap();

        let (sun_area, _, _) = calculate_sun_area_from_position(
            &UIC54_PROFILE.to_vec(),
            rail_azimuth,
            lat,
            lon,
            datetime,
        )
        .unwrap();

        assert!((sun_area - 0.05822633294216206).abs() < 1e-3);
    }
}
