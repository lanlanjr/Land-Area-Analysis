# Land Area Analysis Application

This Flask application performs comprehensive vegetation and land cover analysis for geographical areas using Google Earth Engine, focusing on NDVI and IGBP Land Cover classification.

## Features

- **NDVI Analysis (Normalized Difference Vegetation Index)**:
  - Calculation of vegetation health and density
  - Statistical analysis (mean, min, max, quartile values)
  - Area calculations for different vegetation density ranges
  - Visualization with color gradient from red (low) to green (high)
  
- **IGBP Land Cover Classification**:
  - 17-class land cover categorization from MODIS data
  - Percentage breakdown of each land cover type
  - Detailed class descriptions and area calculations
  - Color-coded visualization of land cover types
  
- **Temporal Analysis**:
  - Dynamic time range selection for NDVI changes
  - Yearly NDVI statistics for trend analysis
  - Historical data comparison between selected periods
  - Seasonal vegetation pattern identification
  
- **Spatial Analysis**:
  - Interactive map for custom area selection
  - Pre-defined regions (Albay, Camarines Sur)
  - Waterway data integration and clipping
  - Custom area selection and saving

## Prerequisites

- Python 3.7+
- Google Earth Engine account with authenticated API access
- Sufficient GEE quota for processing large areas

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd Land-Area-Analysis
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Configure Earth Engine authentication:
   - Create a `.env` file with your Google Earth Engine service account credentials
   - Alternatively, use interactive authentication with `earthengine authenticate`

## Environment Variables

Create a `.env` file with the following variables:
```
GEE_TYPE=service_account
GEE_PROJECT_ID=your-project-id
GEE_PRIVATE_KEY_ID=your-private-key-id
GEE_PRIVATE_KEY=your-private-key
GEE_CLIENT_EMAIL=your-service-account-email
GEE_CLIENT_ID=your-client-id
GEE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
GEE_TOKEN_URI=https://oauth2.googleapis.com/token
GEE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
GEE_CLIENT_X509_CERT_URL=your-cert-url
GEE_UNIVERSE_DOMAIN=googleapis.com
```

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open a web browser and navigate to:
```
http://localhost:5000
```

3. Use the interface to:
   - Select an area of interest on the map
   - Choose between NDVI and IGBP Land Cover analysis
   - Set date ranges for temporal analysis
   - View and interpret results

## NDVI Analysis Details

NDVI (Normalized Difference Vegetation Index) measures vegetation health using the difference between near-infrared (which vegetation strongly reflects) and red light (which vegetation absorbs).

### NDVI Formula
NDVI = (NIR - RED) / (NIR + RED)

### NDVI Value Interpretation
- -1.0 to 0.1: Water, bare soil, or very sparse vegetation
- 0.1 to 0.3: Sparse vegetation (shrubs, grassland, senescing crops)
- 0.3 to 0.6: Moderate vegetation (developing crops, light forest)
- 0.6 to 1.0: Dense vegetation (temperate and tropical forests, crops at peak growth)

### Analysis Capabilities
- Temporal comparison to detect vegetation changes
- Area calculations for each vegetation density class
- Statistical summaries (mean, median, quartiles, min/max)
- Visualization with customizable color scales

## IGBP Land Cover Classification Details

The International Geosphere-Biosphere Programme (IGBP) land cover classification is derived from MODIS satellite data and categorizes land into 17 distinct classes.

### IGBP Classification Classes
1. **Evergreen Needleleaf Forests**: Lands dominated by trees with a canopy cover >60% and height >2m. Almost all trees remain green all year.
2. **Evergreen Broadleaf Forests**: Lands dominated by trees with a canopy cover >60% and height >2m. Almost all trees remain green all year.
3. **Deciduous Needleleaf Forests**: Lands dominated by trees with a canopy cover >60% and height >2m. Trees shed their leaves seasonally.
4. **Deciduous Broadleaf Forests**: Lands dominated by trees with a canopy cover >60% and height >2m. Trees shed their leaves seasonally.
5. **Mixed Forests**: Lands dominated by trees with a canopy cover >60% and height >2m. Neither deciduous nor evergreen types exceed 60% of area.
6. **Closed Shrublands**: Lands with woody vegetation less than 2m tall and with shrub canopy cover >60%.
7. **Open Shrublands**: Lands with woody vegetation less than 2m tall and with shrub canopy cover 10-60%.
8. **Woody Savannas**: Lands with herbaceous and other understory systems, with forest canopy cover 30-60%.
9. **Savannas**: Lands with herbaceous and other understory systems, with forest canopy cover 10-30%.
10. **Grasslands**: Lands with herbaceous types of cover. Tree and shrub cover is less than 10%.
11. **Permanent Wetlands**: Lands with a permanent mixture of water and herbaceous or woody vegetation.
12. **Croplands**: Lands covered with temporary crops followed by harvest and bare soil period.
13. **Urban and Built-up Lands**: Land covered by buildings and other man-made structures.
14. **Cropland/Natural Vegetation Mosaics**: Lands with a mosaic of croplands, forests, shrubland, and grasslands.
15. **Snow and Ice**: Lands under snow or ice cover throughout the year.
16. **Barren**: Lands exposed soil, sand, rocks, or snow with less than 10% vegetation.
17. **Water Bodies**: Oceans, seas, lakes, reservoirs, and rivers.

### Analysis Capabilities
- Percentage distribution of land cover classes within selected area
- Area calculations for each land cover type
- Color-coded visualization of land cover distribution
- Historical comparison (using most recent available year)

## Notes

- Processing large areas may take significant time and resources
- Cloud cover affects the quality of satellite imagery analysis
- The application uses Landsat 8 for NDVI calculation and MODIS for IGBP classification
- IGBP classification uses the most recent available year of data

## License

MIT License 