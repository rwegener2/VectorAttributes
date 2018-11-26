# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Input CRS of any PROJ4 string
- Reprojection for inputs not in EPSG
- Check if crs inputs are rasterio CRS objects and convert to dict

### Changed
- Buffer donut as subclass
- Rename modules

## [0.1.1] - 2018-11-26
## Fixed
- If dem is supplied use that to find DSMCalcs for ground (improves urban analysis)
- Removed repetitive crs_isvalid in dsmfootprint
- Fixed bug in CRS check of crs_isvalid

## Changed
- Pixel area calculated from DSM, not taken as parameter

## [0.1.0] - 2018-11-20
### Added
- CHANGELOG file

### Changed
- Input can be in WGS84 or UTM
- Input is checked for proper coordinate system
- DSMFootprint converts footprints to crs of dsm
- Output geojson geometry is converted to EPSG:4326

## [0.0.1] - 2018-10-25
### Added
- Initial prototype
