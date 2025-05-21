# Quinali Sub-basin NDVI Analysis

This Flask application analyzes the Normalized Difference Vegetation Index (NDVI) for the Quinali Sub-basin of the Bicol River Basin using Google Earth Engine.

## Features

- Dynamic time range selection for NDVI analysis
- Interactive map visualization
- Color-coded NDVI representation
- Historical data comparison
- User-friendly interface

## Prerequisites

- Python 3.7+
- Google Earth Engine account
- Google Earth Engine Python API authenticated

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-name>
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

4. Authenticate Earth Engine:
```bash
earthengine authenticate
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

3. Use the date selectors to choose your desired time range for NDVI analysis.

4. Click "Update NDVI" to refresh the visualization.

## NDVI Color Scale

- Red: Low vegetation (-1.0)
- Yellow: Moderate vegetation (0.0)
- Green: Dense vegetation (1.0)

## Notes

- The coordinates for the Quinali Sub-basin are approximate and may need adjustment for precise analysis.
- Cloud cover may affect the quality of NDVI calculations.
- The application uses Landsat 8 imagery for NDVI calculation.

## License

MIT License 