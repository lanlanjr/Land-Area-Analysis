import ee
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import os
import json
import geopandas as gpd
from shapely.geometry import shape, mapping

# Initialize Flask app
app = Flask(__name__)

# Initialize Earth Engine using service-account.json
try:
    # Use absolute path for the service account key file on PythonAnywhere
    # Reference the home directory for PythonAnywhere
    service_account_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'service-account.json')
    
    print(f"Looking for service account file at: {service_account_path}")
    
    # Read the service account email from the JSON file
    with open(service_account_path, 'r') as f:
        service_account_info = json.load(f)
    
    service_account = service_account_info["client_email"]
    
    print(f"Using service-account.json file for authentication from {service_account_path}")
    credentials = ee.ServiceAccountCredentials(service_account, service_account_path)
    ee.Initialize(credentials)
    
    print(f"Earth Engine initialized with service account: {service_account}")
    
except Exception as e:
    print("Error initializing Earth Engine:", str(e))
    print("Please make sure your service-account.json file is properly configured")
    
    # For debugging - print detailed error information but not credentials
    import traceback
    print("Detailed error:")
    traceback.print_exc()
    
    # Do not use interactive auth for web server deployment
    # Instead, raise a clear error
    raise RuntimeError(f"Earth Engine authentication failed. Service account authentication is required for web deployment. Error: {str(e)}")

# Default coordinates (can be overridden by user selection)
DEFAULT_COORDS = [
    [123.2, 13.3],
    [123.2, 13.2],
    [123.3, 13.2],
    [123.3, 13.3]
]

def get_ndvi_statistics(ndvi_image, area_of_interest):
    """Calculate detailed NDVI statistics for the area."""
    # Get basic statistics
    stats = ndvi_image.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            reducer2=ee.Reducer.minMax(),
            sharedInputs=True
        ).combine(
            reducer2=ee.Reducer.percentile([25, 50, 75]),
            sharedInputs=True
        ),
        geometry=area_of_interest,
        scale=30,  # Landsat resolution
        maxPixels=1e9
    ).getInfo()

    # Calculate area statistics for different NDVI ranges
    area_stats = {}
    ranges = [
        ('water_or_bare', -1, 0.1, 'Water bodies or bare soil'),
        ('sparse_vegetation', 0.1, 0.3, 'Sparse vegetation'),
        ('moderate_vegetation', 0.3, 0.6, 'Moderate vegetation'),
        ('dense_vegetation', 0.6, 1, 'Dense, healthy vegetation')
    ]

    total_area = 0
    for name, min_val, max_val, description in ranges:
        range_mask = ndvi_image.gte(min_val).And(ndvi_image.lt(max_val))
        area_pixels = range_mask.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=area_of_interest,
            scale=30,
            maxPixels=1e9
        ).get('NDVI').getInfo()
        
        # Convert pixel count to area in hectares (30m x 30m = 900m² per pixel)
        area_hectares = (area_pixels * 900) / 10000
        total_area += area_hectares
        
        area_stats[name] = {
            'description': description,
            'min_ndvi': min_val,
            'max_ndvi': max_val,
            'area_hectares': round(area_hectares, 2),
        }
    
    # Calculate percentages
    for stat in area_stats.values():
        stat['percentage'] = round((stat['area_hectares'] / total_area) * 100, 2)

    return {
        'basic_stats': {
            'mean_ndvi': round(stats.get('NDVI_mean', 0), 3),
            'min_ndvi': round(stats.get('NDVI_min', 0), 3),
            'max_ndvi': round(stats.get('NDVI_max', 0), 3),
            'median_ndvi': round(stats.get('NDVI_p50', 0), 3),
            'q1_ndvi': round(stats.get('NDVI_p25', 0), 3),
            'q3_ndvi': round(stats.get('NDVI_p75', 0), 3)
        },
        'area_stats': area_stats,
        'total_area_hectares': round(total_area, 2)
    }

def get_igbp_land_cover(start_date, end_date, coordinates):
    """Get IGBP land cover classification for an area.
    
    The IGBP classification includes 17 land cover classes:
    1: Evergreen Needleleaf Forests
    2: Evergreen Broadleaf Forests
    3: Deciduous Needleleaf Forests
    4: Deciduous Broadleaf Forests
    5: Mixed Forests
    6: Closed Shrublands
    7: Open Shrublands
    8: Woody Savannas
    9: Savannas
    10: Grasslands
    11: Permanent Wetlands
    12: Croplands
    13: Urban and Built-up Lands
    14: Cropland/Natural Vegetation Mosaics
    15: Snow and Ice
    16: Barren
    17: Water Bodies
    """
    try:
        # Convert coordinates to Earth Engine geometry
        area_of_interest = ee.Geometry.Polygon([coordinates])
        
        # Calculate area in square kilometers for debugging
        area_size = area_of_interest.area().divide(1000 * 1000).getInfo()
        print(f"Area size: {area_size} square kilometers")
        
        # If area is too large, provide a warning
        if area_size > 10000:  # 10,000 sq km threshold
            print(f"Warning: Selected area is very large ({area_size} sq km). Consider selecting a smaller area.")
        
        # Get the MODIS Land Cover Type Yearly Global 500m dataset (IGBP classification)
        # Using collection 061 as specified in the sample code
        modis_lc = ee.ImageCollection("MODIS/061/MCD12Q1")
        
        # First check if the collection has any images at all
        collection_size = modis_lc.size().getInfo()
        if collection_size == 0:
            raise Exception("MODIS land cover dataset is not available")
        
        print(f"Found {collection_size} images in MODIS collection")
        
        # Always get the most recent data available, regardless of input date
        latest_image = modis_lc.sort('system:time_start', False).first()
        
        # Get the actual year from the image timestamp
        timestamp = latest_image.get('system:time_start').getInfo()
        actual_year = datetime.fromtimestamp(timestamp / 1000).year
        print(f"Using data from the latest available year: {actual_year}")
        
        # Make sure we actually have an image
        if latest_image is None:
            raise Exception("No MODIS land cover data available")
        
        # Select the LC_Type1 band and clip to the area of interest
        igbp_image = latest_image.select('LC_Type1').clip(area_of_interest)
        
        # Define the IGBP classification classes and colors based on the sample code
        igbp_classes = {
            1: {'name': 'Evergreen Needleleaf Forest', 'color': '05450a'},
            2: {'name': 'Evergreen Broadleaf Forest', 'color': '086a10'},
            3: {'name': 'Deciduous Needleleaf Forest', 'color': '54a708'},
            4: {'name': 'Deciduous Broadleaf Forest', 'color': '78d203'},
            5: {'name': 'Mixed Forest', 'color': '009900'},
            6: {'name': 'Closed Shrublands', 'color': 'c6b044'},
            7: {'name': 'Open Shrublands', 'color': 'dcd159'},
            8: {'name': 'Woody Savannas', 'color': 'dade48'},
            9: {'name': 'Savannas', 'color': 'fbff13'},
            10: {'name': 'Grasslands', 'color': 'b6ff05'},
            11: {'name': 'Permanent Wetlands', 'color': '27ff87'},
            12: {'name': 'Croplands', 'color': 'c24f44'},
            13: {'name': 'Urban and Built-up Lands', 'color': 'a5a5a5'},
            14: {'name': 'Cropland/Natural Vegetation Mosaics', 'color': 'ff6d4c'},
            15: {'name': 'Snow and Ice', 'color': '69fff8'},
            16: {'name': 'Barren', 'color': 'f9ffa4'},
            17: {'name': 'Water Bodies', 'color': '1c0dff'}
        }
        
        # Create a list of colors for visualization exactly as in the Earth Engine example
        palette = [
            '05450a', '086a10', '54a708', '78d203', '009900', 'c6b044', 'dcd159',
            'dade48', 'fbff13', 'b6ff05', '27ff87', 'c24f44', 'a5a5a5', 'ff6d4c',
            '69fff8', 'f9ffa4', '1c0dff'
        ]
        
        # Set visualization parameters to exactly match the sample code
        vis_params = {
            'min': 1.0,
            'max': 17.0,
            'palette': palette
        }
        
        # Get the map ID for display
        map_id = igbp_image.getMapId(vis_params)
        
        # Get statistics about the area using a more comprehensive approach
        # First, get a histogram of land cover classes
        histogram = igbp_image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=area_of_interest,
            scale=500,  # MODIS resolution is 500m
            maxPixels=1e9
        ).getInfo()
        
        print(f"Land cover histogram: {histogram}")
        
        # Process histogram to get areas for each class
        area_stats = {}
        total_area = 0
        
        if 'LC_Type1' in histogram and histogram['LC_Type1']:
            lc_data = histogram['LC_Type1']
            
            # Convert histogram to percentages and areas
            for class_val_str, pixel_count in lc_data.items():
                # Class values in the histogram come as strings, convert to int
                class_value = int(float(class_val_str))
                
                if class_value in igbp_classes:
                    # Calculate area in hectares (500m x 500m = 25ha per pixel)
                    area_hectares = (pixel_count * 25)
                    total_area += area_hectares
                    
                    area_stats[igbp_classes[class_value]['name']] = {
                        'class_value': class_value,
                        'color': '#' + igbp_classes[class_value]['color'],
                        'area_hectares': round(area_hectares, 2),
                        'pixel_count': pixel_count
                    }
        
        # If no data was found, we'll use a simpler approach as a fallback
        if not area_stats:
            print("No data found with histogram method, trying direct calculation")
            
            # Use a reduced scale for large areas to prevent computation timeouts
            scale = 500  # Default MODIS resolution is 500m
            
            # Loop through each class and calculate area
            for class_value, class_info in igbp_classes.items():
                try:
                    # Create mask for this class
                    class_mask = igbp_image.eq(class_value)
                    
                    # Calculate area in pixels
                    area_pixels = class_mask.reduceRegion(
                        reducer=ee.Reducer.sum(),
                        geometry=area_of_interest,
                        scale=scale,
                        maxPixels=1e9
                    ).get('LC_Type1').getInfo()
                    
                    if area_pixels is not None and area_pixels > 0:
                        # Convert pixel count to area in hectares (500m x 500m = 25ha per pixel)
                        area_hectares = (area_pixels * 25)
                        total_area += area_hectares
                        
                        area_stats[class_info['name']] = {
                            'class_value': class_value,
                            'color': '#' + class_info['color'],
                            'area_hectares': round(area_hectares, 2),
                            'pixel_count': area_pixels
                        }
                except Exception as e:
                    print(f"Error calculating area for class {class_value}: {str(e)}")
        
        # Even if we don't find any specific land cover classes, we should still show the map
        # Just report it as unknown/unclassified
        if not area_stats:
            # Create a generic entry for unclassified area
            total_area = area_size * 100  # convert sq km to hectares
            area_stats['Unclassified'] = {
                'class_value': 0,
                'color': '#808080',  # gray
                'area_hectares': round(total_area, 2),
                'pixel_count': 0,
                'percentage': 100.0
            }
            print("Warning: No specific land cover classes found in the selected area.")
        else:
            # Calculate percentages
            for stat in area_stats.values():
                stat['percentage'] = round((stat['area_hectares'] / total_area) * 100, 2) if total_area > 0 else 0
        
        return {
            'tile_url': map_id['tile_fetcher'].url_format,
            'year': actual_year,
            'area_stats': area_stats,
            'total_area_hectares': round(total_area, 2)
        }
        
    except ee.EEException as e:
        print(f"Earth Engine error: {str(e)}")
        # More detailed error info
        if "permission denied" in str(e).lower():
            raise Exception("Access to Earth Engine data denied. Please check your authentication.")
        elif "timeout" in str(e).lower():
            raise Exception("Request timed out. The selected area may be too large.")
        elif "quota" in str(e).lower():
            raise Exception("Quota exceeded. Please try again later or select a smaller area.")
        else:
            raise Exception(f"Earth Engine error: {str(e)}")
    except Exception as e:
        print(f"Error in IGBP classification: {str(e)}")
        raise Exception(f"Failed to retrieve land cover data: {str(e)}")

def get_ndvi_map_for_year(year, coordinates):
    """Get NDVI map for a specific year."""
    area_of_interest = ee.Geometry.Polygon([coordinates])
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    # Get Landsat 8 collection for the year
    l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_TOA') \
        .filterBounds(area_of_interest) \
        .filterDate(start_date, end_date)
    
    if l8.size().getInfo() > 0:
        # Calculate average NDVI for the year
        annual_ndvi = l8.map(lambda image: image.normalizedDifference(['B5', 'B4']).rename('NDVI')) \
                       .mean() \
                       .clip(area_of_interest)
        
        # Create visualization parameters
        vis_params = {
            'min': -1,
            'max': 1,
            'palette': ['red', 'yellow', 'green']
        }
        
        # Get the NDVI map
        map_id = annual_ndvi.getMapId(vis_params)
        
        return {
            'year': year,
            'tile_url': map_id['tile_fetcher'].url_format
        }
    return None

def get_yearly_ndvi_stats(coordinates, start_year, end_year):
    """Get NDVI statistics for each year in the range."""
    area_of_interest = ee.Geometry.Polygon([coordinates])
    yearly_stats = []
    map_tiles = []

    for year in range(start_year, end_year + 1):
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        # Get Landsat 8 collection for the year
        l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_TOA') \
            .filterBounds(area_of_interest) \
            .filterDate(start_date, end_date)
        
        if l8.size().getInfo() > 0:
            # Calculate average NDVI for the year
            annual_ndvi = l8.map(lambda image: image.normalizedDifference(['B5', 'B4']).rename('NDVI')) \
                           .mean() \
                           .clip(area_of_interest)
            
            # Get statistics for the year
            stats = get_ndvi_statistics(annual_ndvi, area_of_interest)
            stats['year'] = year
            yearly_stats.append(stats)
            
            # Get map tiles for the year
            map_data = get_ndvi_map_for_year(year, coordinates)
            if map_data:
                map_tiles.append(map_data)
    
    return yearly_stats, map_tiles

def calculate_ndvi(start_date, end_date, coordinates):
    """Calculate NDVI for the specified date range and area."""
    # Convert coordinates to Earth Engine geometry
    area_of_interest = ee.Geometry.Polygon([coordinates])
    
    # Get Landsat 8 collection
    l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_TOA') \
        .filterBounds(area_of_interest) \
        .filterDate(start_date, end_date) \
        .sort('CLOUD_COVER') \
        .first()
    
    if l8 is None:
        raise Exception("No Landsat imagery found for the specified time range and area")
    
    # Calculate NDVI
    ndvi = l8.normalizedDifference(['B5', 'B4']).rename('NDVI')
    
    # Clip to the area of interest
    ndvi = ndvi.clip(area_of_interest)
    
    # Get detailed statistics
    statistics = get_ndvi_statistics(ndvi, area_of_interest)
    
    return ndvi, statistics

def get_esa_worldcover(coordinates):
    """Get ESA WorldCover 10m v100 classification for an area.
    
    The ESA WorldCover classification includes 11 land cover classes:
    10: Tree cover
    20: Shrubland
    30: Grassland
    40: Cropland
    50: Built-up
    60: Bare / sparse vegetation
    70: Snow and ice
    80: Permanent water bodies
    90: Herbaceous wetland
    95: Mangroves
    100: Moss and lichen
    """
    try:
        # Convert coordinates to Earth Engine geometry
        area_of_interest = ee.Geometry.Polygon([coordinates])
        
        # Calculate area in square kilometers for debugging
        area_size = area_of_interest.area().divide(1000 * 1000).getInfo()
        print(f"Area size: {area_size} square kilometers")
        
        # If area is too large, provide a warning
        if area_size > 10000:  # 10,000 sq km threshold
            print(f"Warning: Selected area is very large ({area_size} sq km). Consider selecting a smaller area.")
        
        # Get the ESA WorldCover 10m dataset
        esa_wc = ee.ImageCollection("ESA/WorldCover/v100").first()
        
        # Make sure we actually have an image
        if esa_wc is None:
            raise Exception("ESA WorldCover data is not available")
        
        # Select the Map band and clip to the area of interest
        worldcover_image = esa_wc.select('Map').clip(area_of_interest)
        
        # Define the ESA WorldCover classification classes and colors
        worldcover_classes = {
            10: {'name': 'Tree cover', 'color': '006400'},
            20: {'name': 'Shrubland', 'color': 'ffbb22'},
            30: {'name': 'Grassland', 'color': 'ffff4c'},
            40: {'name': 'Cropland', 'color': 'f096ff'},
            50: {'name': 'Built-up', 'color': 'fa0000'},
            60: {'name': 'Bare / sparse vegetation', 'color': 'b4b4b4'},
            70: {'name': 'Snow and ice', 'color': 'f0f0f0'},
            80: {'name': 'Permanent water bodies', 'color': '0064c8'},
            90: {'name': 'Herbaceous wetland', 'color': '0096a0'},
            95: {'name': 'Mangroves', 'color': '00cf75'},
            100: {'name': 'Moss and lichen', 'color': 'fae6a0'}
        }
        
        # Create a list of colors for visualization
        palette = [
            '006400', 'ffbb22', 'ffff4c', 'f096ff', 'fa0000', 'b4b4b4',
            'f0f0f0', '0064c8', '0096a0', '00cf75', 'fae6a0'
        ]
        
        # Get the map date (year)
        worldcover_year = 2020  # ESA WorldCover v100 is from 2020
        
        # Set visualization parameters
        vis_params = {
            'bands': ['Map'],
            'min': 10,
            'max': 100,
            'palette': palette
        }
        
        # Get the map ID for display
        map_id = worldcover_image.getMapId(vis_params)
        
        # Get statistics about the area using a histogram approach
        histogram = worldcover_image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=area_of_interest,
            scale=10,  # ESA WorldCover is 10m resolution
            maxPixels=1e9
        ).getInfo()
        
        print(f"Land cover histogram: {histogram}")
        
        # Process histogram to get areas for each class
        area_stats = {}
        total_area = 0
        
        if 'Map' in histogram and histogram['Map']:
            lc_data = histogram['Map']
            
            # Convert histogram to percentages and areas
            for class_val_str, pixel_count in lc_data.items():
                # Class values in the histogram come as strings, convert to int
                class_value = int(float(class_val_str))
                
                if class_value in worldcover_classes:
                    # Calculate area in hectares (10m x 10m = 100m² per pixel)
                    area_hectares = (pixel_count * 100) / 10000
                    total_area += area_hectares
                    
                    area_stats[worldcover_classes[class_value]['name']] = {
                        'class_value': class_value,
                        'color': '#' + worldcover_classes[class_value]['color'],
                        'area_hectares': round(area_hectares, 2),
                        'pixel_count': pixel_count
                    }
        
        # If no data was found, try a direct calculation approach
        if not area_stats:
            print("No data found with histogram method, trying direct calculation")
            
            # ESA WorldCover resolution is 10m
            scale = 10
            
            # Loop through each class and calculate area
            for class_value, class_info in worldcover_classes.items():
                try:
                    # Create mask for this class
                    class_mask = worldcover_image.eq(class_value)
                    
                    # Calculate area in pixels
                    area_pixels = class_mask.reduceRegion(
                        reducer=ee.Reducer.sum(),
                        geometry=area_of_interest,
                        scale=scale,
                        maxPixels=1e9
                    ).get('Map').getInfo()
                    
                    if area_pixels is not None and area_pixels > 0:
                        # Calculate area in hectares (10m x 10m = 100m² per pixel)
                        area_hectares = (area_pixels * 100) / 10000
                        total_area += area_hectares
                        
                        area_stats[class_info['name']] = {
                            'class_value': class_value,
                            'color': '#' + class_info['color'],
                            'area_hectares': round(area_hectares, 2),
                            'pixel_count': area_pixels
                        }
                except Exception as e:
                    print(f"Error calculating area for class {class_value}: {str(e)}")
        
        # Even if we don't find any specific land cover classes, we should still show the map
        # Just report it as unknown/unclassified
        if not area_stats:
            # Create a generic entry for unclassified area
            total_area = area_size * 100  # convert sq km to hectares
            area_stats['Unclassified'] = {
                'class_value': 0,
                'color': '#808080',  # gray
                'area_hectares': round(total_area, 2),
                'pixel_count': 0,
                'percentage': 100.0
            }
            print("Warning: No specific land cover classes found in the selected area.")
        else:
            # Calculate percentages
            for stat in area_stats.values():
                stat['percentage'] = round((stat['area_hectares'] / total_area) * 100, 2) if total_area > 0 else 0
        
        return {
            'tile_url': map_id['tile_fetcher'].url_format,
            'year': worldcover_year,
            'area_stats': area_stats,
            'total_area_hectares': round(total_area, 2)
        }
        
    except ee.EEException as e:
        print(f"Earth Engine error: {str(e)}")
        # More detailed error info
        if "permission denied" in str(e).lower():
            raise Exception("Access to Earth Engine data denied. Please check your authentication.")
        elif "timeout" in str(e).lower():
            raise Exception("Request timed out. The selected area may be too large.")
        elif "quota" in str(e).lower():
            raise Exception("Quota exceeded. Please try again later or select a smaller area.")
        else:
            raise Exception(f"Earth Engine error: {str(e)}")
    except Exception as e:
        print(f"Error in ESA WorldCover classification: {str(e)}")
        raise Exception(f"Failed to retrieve land cover data: {str(e)}")

def get_dynamic_world(coordinates):
    """Get Dynamic World V1 land cover classification for an area.
    
    Dynamic World V1 includes the following land cover classes:
    0: water
    1: trees
    2: grass
    3: flooded_vegetation
    4: crops
    5: shrub_and_scrub
    6: built
    7: bare
    8: snow_and_ice
    """
    try:
        # Convert coordinates to Earth Engine geometry
        area_of_interest = ee.Geometry.Polygon([coordinates])
        
        # Calculate area in square kilometers for debugging
        area_size = area_of_interest.area().divide(1000 * 1000).getInfo()
        print(f"Area size: {area_size} square kilometers")
        
        # If area is too large, provide a warning
        if area_size > 10000:  # 10,000 sq km threshold
            print(f"Warning: Selected area is very large ({area_size} sq km). Consider selecting a smaller area.")
        
        # Get the Dynamic World V1 dataset
        # We'll use the most recent data available for the area
        now = datetime.now()
        end_date = now.strftime('%Y-%m-%d')
        # Look back 30 days to find suitable imagery
        start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Filter the Dynamic World collection
        dw_col = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1') \
            .filterBounds(area_of_interest) \
            .filterDate(start_date, end_date)
            
        # Check if we have any images
        dw_count = dw_col.size().getInfo()
        print(f"Found {dw_count} Dynamic World images")
        
        if dw_count == 0:
            # Try a longer time range if no recent images
            start_date = (now - timedelta(days=365)).strftime('%Y-%m-%d')  # Look back 1 year
            dw_col = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1') \
                .filterBounds(area_of_interest) \
                .filterDate(start_date, end_date)
            dw_count = dw_col.size().getInfo()
            print(f"Found {dw_count} Dynamic World images in the extended range")
        
        if dw_count == 0:
            raise Exception("No Dynamic World data found for the selected area")
        
        # Get the corresponding Sentinel-2 collection
        s2_col = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
            .filterBounds(area_of_interest) \
            .filterDate(start_date, end_date)
        
        # Link DW and S2 source images if possible
        try:
            linked_col = dw_col.linkCollection(s2_col, s2_col.first().bandNames())
            linked_image = ee.Image(linked_col.first())
        except Exception as e:
            print(f"Error linking collections: {str(e)}")
            # Fallback to just using the most recent Dynamic World image
            linked_image = dw_col.sort('system:time_start', False).first()
        
        # Define class names and visualization palette
        class_names = [
            'water',
            'trees',
            'grass',
            'flooded_vegetation',
            'crops',
            'shrub_and_scrub',
            'built',
            'bare',
            'snow_and_ice',
        ]
        
        vis_palette = [
            '419bdf',
            '397d49',
            '88b053',
            '7a87c6',
            'e49635',
            'dfc35a',
            'c4281b',
            'a59b8f',
            'b39fe1',
        ]
        
        # Define a dictionary of class information
        class_info = {
            0: {'name': 'Water', 'color': '419bdf'},
            1: {'name': 'Trees', 'color': '397d49'},
            2: {'name': 'Grass', 'color': '88b053'},
            3: {'name': 'Flooded Vegetation', 'color': '7a87c6'},
            4: {'name': 'Crops', 'color': 'e49635'},
            5: {'name': 'Shrub and Scrub', 'color': 'dfc35a'},
            6: {'name': 'Built', 'color': 'c4281b'},
            7: {'name': 'Bare', 'color': 'a59b8f'},
            8: {'name': 'Snow and Ice', 'color': 'b39fe1'}
        }
        
        # Clip to the area of interest
        dw_image = linked_image.clip(area_of_interest)
        
        # Create visualization using the label band
        vis_params = {
            'bands': ['label'],
            'min': 0,
            'max': 8,
            'palette': vis_palette
        }
        
        # Get the map ID for display
        map_id = dw_image.select('label').getMapId(vis_params)
        
        # Extract timestamp from the image
        timestamp = dw_image.get('system:time_start').getInfo()
        image_date = datetime.fromtimestamp(timestamp / 1000)
        
        # Get statistics about the area using a histogram approach
        histogram = dw_image.select('label').reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=area_of_interest,
            scale=10,  # Dynamic World has 10m resolution
            maxPixels=1e9
        ).getInfo()
        
        print(f"Land cover histogram: {histogram}")
        
        # Process histogram to get areas for each class
        area_stats = {}
        total_area = 0
        
        if 'label' in histogram and histogram['label']:
            lc_data = histogram['label']
            
            # Convert histogram to percentages and areas
            for class_val_str, pixel_count in lc_data.items():
                # Class values in the histogram come as strings, convert to int
                class_value = int(float(class_val_str))
                
                if class_value in class_info:
                    # Calculate area in hectares (10m x 10m = 100m² per pixel)
                    area_hectares = (pixel_count * 100) / 10000
                    total_area += area_hectares
                    
                    area_stats[class_info[class_value]['name']] = {
                        'class_value': class_value,
                        'color': '#' + class_info[class_value]['color'],
                        'area_hectares': round(area_hectares, 2),
                        'pixel_count': pixel_count
                    }
        
        # If no data was found, try calculating probabilities directly
        if not area_stats:
            print("No data found with histogram method, trying probability calculation")
            
            # Dynamic World provides probability bands for each class
            for idx, class_name in enumerate(class_names):
                try:
                    # Calculate area with probability > 0.5 for this class
                    class_area = dw_image.select(class_name).gt(0.5)
                    
                    # Calculate area in pixels
                    area_pixels = class_area.reduceRegion(
                        reducer=ee.Reducer.sum(),
                        geometry=area_of_interest,
                        scale=10,
                        maxPixels=1e9
                    ).get(class_name).getInfo()
                    
                    if area_pixels is not None and area_pixels > 0:
                        # Convert pixel count to area in hectares (10m x 10m = 100m² per pixel)
                        area_hectares = (area_pixels * 100) / 10000
                        total_area += area_hectares
                        
                        area_stats[class_info[idx]['name']] = {
                            'class_value': idx,
                            'color': '#' + class_info[idx]['color'],
                            'area_hectares': round(area_hectares, 2),
                            'pixel_count': area_pixels
                        }
                except Exception as e:
                    print(f"Error calculating area for class {class_name}: {str(e)}")
        
        # Create a fallback with unclassified if no data found
        if not area_stats:
            # Create a generic entry for unclassified area
            total_area = area_size * 100  # convert sq km to hectares
            area_stats['Unclassified'] = {
                'class_value': -1,
                'color': '#808080',  # gray
                'area_hectares': round(total_area, 2),
                'pixel_count': 0,
                'percentage': 100.0
            }
            print("Warning: No specific land cover classes found in the selected area.")
        else:
            # Calculate percentages
            for stat in area_stats.values():
                stat['percentage'] = round((stat['area_hectares'] / total_area) * 100, 2) if total_area > 0 else 0
        
        return {
            'tile_url': map_id['tile_fetcher'].url_format,
            'date': image_date.strftime('%Y-%m-%d'),
            'area_stats': area_stats,
            'total_area_hectares': round(total_area, 2)
        }
        
    except ee.EEException as e:
        print(f"Earth Engine error: {str(e)}")
        # More detailed error info
        if "permission denied" in str(e).lower():
            raise Exception("Access to Earth Engine data denied. Please check your authentication.")
        elif "timeout" in str(e).lower():
            raise Exception("Request timed out. The selected area may be too large.")
        elif "quota" in str(e).lower():
            raise Exception("Quota exceeded. Please try again later or select a smaller area.")
        else:
            raise Exception(f"Earth Engine error: {str(e)}")
    except Exception as e:
        print(f"Error in Dynamic World classification: {str(e)}")
        raise Exception(f"Failed to retrieve land cover data: {str(e)}")

def get_dynamic_world_for_year(year, coordinates):
    """Get Dynamic World V1 land cover classification for a specific year."""
    try:
        # Convert coordinates to Earth Engine geometry
        area_of_interest = ee.Geometry.Polygon([coordinates])
        
        # Define date range for the specific year
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        # Filter the Dynamic World collection for the specified year
        dw_col = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1') \
            .filterBounds(area_of_interest) \
            .filterDate(start_date, end_date)
            
        # Check if we have any images
        dw_count = dw_col.size().getInfo()
        print(f"Found {dw_count} Dynamic World images for year {year}")
        
        if dw_count == 0:
            print(f"No images found for year {year}, returning empty result")
            return None
        
        # Get most probabilities image (composite)
        composite = dw_col.select(['label']).mode()
        
        # Clip to the area of interest
        dw_image = composite.clip(area_of_interest)
        
        # Define class names and visualization palette
        class_names = [
            'water',
            'trees',
            'grass',
            'flooded_vegetation',
            'crops',
            'shrub_and_scrub',
            'built',
            'bare',
            'snow_and_ice',
        ]
        
        vis_palette = [
            '419bdf',
            '397d49',
            '88b053',
            '7a87c6',
            'e49635',
            'dfc35a',
            'c4281b',
            'a59b8f',
            'b39fe1',
        ]
        
        # Define a dictionary of class information
        class_info = {
            0: {'name': 'Water', 'color': '419bdf'},
            1: {'name': 'Trees', 'color': '397d49'},
            2: {'name': 'Grass', 'color': '88b053'},
            3: {'name': 'Flooded Vegetation', 'color': '7a87c6'},
            4: {'name': 'Crops', 'color': 'e49635'},
            5: {'name': 'Shrub and Scrub', 'color': 'dfc35a'},
            6: {'name': 'Built', 'color': 'c4281b'},
            7: {'name': 'Bare', 'color': 'a59b8f'},
            8: {'name': 'Snow and Ice', 'color': 'b39fe1'}
        }
        
        # Create visualization using the label band
        vis_params = {
            'min': 0,
            'max': 8,
            'palette': vis_palette
        }
        
        # Get the map ID for display
        map_id = dw_image.getMapId(vis_params)
        
        # Get statistics about the area using a histogram approach
        histogram = dw_image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=area_of_interest,
            scale=10,  # Dynamic World has 10m resolution
            maxPixels=1e9
        ).getInfo()
        
        # Process histogram to get areas for each class
        area_stats = {}
        total_area = 0
        
        if 'label' in histogram and histogram['label']:
            lc_data = histogram['label']
            
            # Convert histogram to percentages and areas
            for class_val_str, pixel_count in lc_data.items():
                # Class values in the histogram come as strings, convert to int
                class_value = int(float(class_val_str))
                
                if class_value in class_info:
                    # Calculate area in hectares (10m x 10m = 100m² per pixel)
                    area_hectares = (pixel_count * 100) / 10000
                    total_area += area_hectares
                    
                    area_stats[class_info[class_value]['name']] = {
                        'class_value': class_value,
                        'color': '#' + class_info[class_value]['color'],
                        'area_hectares': round(area_hectares, 2),
                        'pixel_count': pixel_count
                    }
        
        # If no data was found, return None
        if not area_stats:
            return None
        
        # Calculate percentages
        for stat in area_stats.values():
            stat['percentage'] = round((stat['area_hectares'] / total_area) * 100, 2) if total_area > 0 else 0
        
        return {
            'tile_url': map_id['tile_fetcher'].url_format,
            'year': year,
            'date': f"{year}-01-01",  # Add date field for compatibility with display code
            'area_stats': area_stats,
            'total_area_hectares': round(total_area, 2)
        }
        
    except Exception as e:
        print(f"Error in Dynamic World classification for year {year}: {str(e)}")
        return None

def get_dynamic_world_timeseries(coordinates, start_year, end_year):
    """Get Dynamic World land cover classification for a range of years."""
    timeseries_data = []
    map_tiles = []
    
    for year in range(start_year, end_year + 1):
        try:
            print(f"Processing Dynamic World data for year {year}...")
            year_data = get_dynamic_world_for_year(year, coordinates)
            
            if year_data:
                timeseries_data.append(year_data)
                map_tiles.append({
                    'year': year,
                    'tile_url': year_data['tile_url']
                })
        except Exception as e:
            print(f"Error processing year {year}: {str(e)}")
    
    return timeseries_data, map_tiles

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/get_ndvi', methods=['POST'])
def get_ndvi():
    """Get NDVI data for the specified time range and area."""
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    coordinates = data.get('coordinates')
    
    if not coordinates:
        return jsonify({
            'success': False,
            'error': 'No area coordinates provided'
        })
    
    try:
        ndvi, statistics = calculate_ndvi(start_date, end_date, coordinates)
        
        # Create visualization parameters
        vis_params = {
            'min': -1,
            'max': 1,
            'palette': ['red', 'yellow', 'green']
        }
        
        # Get the NDVI map
        map_id = ndvi.getMapId(vis_params)
        
        return jsonify({
            'success': True,
            'tile_url': map_id['tile_fetcher'].url_format,
            'statistics': statistics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_igbp_land_cover', methods=['POST'])
def get_igbp():
    """Get IGBP Land Cover classification for the specified area."""
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    coordinates = data.get('coordinates')
    
    if not coordinates:
        return jsonify({
            'success': False,
            'error': 'No area coordinates provided'
        })
    
    try:
        igbp_data = get_igbp_land_cover(start_date, end_date, coordinates)
        
        return jsonify({
            'success': True,
            'igbp_data': igbp_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_esa_worldcover', methods=['POST'])
def get_worldcover():
    """Get ESA WorldCover classification for the specified area."""
    data = request.get_json()
    coordinates = data.get('coordinates')
    
    if not coordinates:
        return jsonify({
            'success': False,
            'error': 'No area coordinates provided'
        })
    
    try:
        worldcover_data = get_esa_worldcover(coordinates)
        
        return jsonify({
            'success': True,
            'worldcover_data': worldcover_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_dynamic_world', methods=['POST'])
def get_dynamic_world_route():
    """Get Dynamic World classification for the selected area."""
    data = request.get_json()
    coordinates = data.get('coordinates')
    
    if not coordinates:
        return jsonify({
            'success': False,
            'error': 'No area coordinates provided'
        })
    
    try:
        dynamicworld_data = get_dynamic_world(coordinates)
        return jsonify({
            'success': True,
            'dynamicworld_data': dynamicworld_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_dynamic_world_for_year', methods=['POST'])
def get_dynamic_world_for_year_route():
    """Get Dynamic World classification for a specific year."""
    data = request.get_json()
    coordinates = data.get('coordinates')
    year = data.get('year')
    
    if not coordinates:
        return jsonify({
            'success': False,
            'error': 'No area coordinates provided'
        })
    
    if not year:
        return jsonify({
            'success': False,
            'error': 'No year specified'
        })
    
    try:
        result = get_dynamic_world_for_year(year, coordinates)
        
        if result is None:
            return jsonify({
                'success': False,
                'error': f'No Dynamic World data found for year {year}'
            })
        
        return jsonify({
            'success': True,
            'dynamicworld_data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_dynamic_world_timeseries', methods=['POST'])
def get_dynamic_world_timeseries_route():
    """Get Dynamic World classification time series for the specified years."""
    data = request.get_json()
    coordinates = data.get('coordinates')
    start_year = data.get('start_year', datetime.now().year - 5)
    end_year = data.get('end_year', datetime.now().year)
    
    if not coordinates:
        return jsonify({
            'success': False,
            'error': 'No area coordinates provided'
        })
    
    try:
        timeseries_data, map_tiles = get_dynamic_world_timeseries(coordinates, start_year, end_year)
        
        if not timeseries_data:
            return jsonify({
                'success': False,
                'error': 'No Dynamic World data found for the specified time range'
            })
        
        return jsonify({
            'success': True,
            'timeseries_data': timeseries_data,
            'map_tiles': map_tiles
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_yearly_stats', methods=['POST'])
def get_yearly_stats():
    """Get NDVI statistics for multiple years."""
    data = request.get_json()
    coordinates = data.get('coordinates')
    start_year = data.get('start_year', datetime.now().year - 5)  # Default to 5 years ago
    end_year = data.get('end_year', datetime.now().year)
    
    if not coordinates:
        return jsonify({
            'success': False,
            'error': 'No area coordinates provided'
        })
    
    try:
        yearly_stats, map_tiles = get_yearly_ndvi_stats(coordinates, start_year, end_year)
        return jsonify({
            'success': True,
            'yearly_stats': yearly_stats,
            'map_tiles': map_tiles
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/save_area', methods=['POST'])
def save_area():
    """Save a user-defined area."""
    data = request.get_json()
    coords = data.get('coordinates')
    
    if not coords:
        return jsonify({'success': False, 'error': 'No coordinates provided'})
    
    return jsonify({'success': True, 'message': 'Area saved successfully'})

@app.route('/camsur.geojson')
def serve_camsur_geojson():
    """Serve the Camarines Sur GeoJSON file."""
    return send_file('camsur.geojson')

@app.route('/albay.geojson')
def serve_albay_geojson():
    """Serve the Albay GeoJSON file."""
    return send_file('albay.geojson')

@app.route('/waterways.geojson')
def serve_waterways_geojson():
    """Serve the Waterways GeoJSON file."""
    return send_file('waterways.geojson')

@app.route('/clip_waterways', methods=['POST'])
def clip_waterways():
    """Clip waterways to the selected area."""
    data = request.get_json()
    if not data or 'coordinates' not in data:
        return jsonify({'success': False, 'error': 'No coordinates provided'})
    
    try:
        # Create a GeoDataFrame from the selected area
        area_polygon = {
            'type': 'Polygon',
            'coordinates': [data['coordinates']]  # GeoJSON format expects a list of rings
        }
        area_gdf = gpd.GeoDataFrame(geometry=[shape(area_polygon)], crs="EPSG:4326")
        
        # Read the waterways GeoJSON
        waterways_gdf = gpd.read_file('waterways.geojson')
        
        # Clip waterways to the selected area
        clipped_waterways = gpd.clip(waterways_gdf, area_gdf)
        
        # Convert back to GeoJSON
        clipped_geojson = json.loads(clipped_waterways.to_json())
        
        return jsonify({
            'success': True, 
            'clipped_waterways': clipped_geojson
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True) 