#!/usr/bin/env python3

import sys
import logging
from pathlib import Path
from fars_cleaner import FARSFetcher, load_pipeline

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger('fars_debug')

# Create temp directory for testing
test_dir = Path('./fars_test_data')
test_dir.mkdir(exist_ok=True)
logger.info(f"Using directory: {test_dir.absolute()}")

try:
    # Initialize the fetcher with debug info
    logger.info("Initializing FARSFetcher...")
    # Progress bar will be displayed automatically when downloading files
    fetcher = FARSFetcher(project_dir=test_dir, show_progress=True)
    logger.info(f"Cache path: {fetcher.cache_path}")
    

    # Process the data
    logger.info("Processing the downloaded data...")
    vehicles, accidents, people = load_pipeline(
        fetcher=fetcher,
        first_run=True,
        target_folder=test_dir,
        start_year=2018,
        end_year=2019,
    )
    
    # Print some basic info about the loaded data
    logger.info(f"Vehicles dataframe: {vehicles.shape} rows, {list(vehicles.columns[:5])}...")
    logger.info(f"Accidents dataframe: {accidents.shape} rows, {list(accidents.columns[:5])}...")
    logger.info(f"People dataframe: {people.shape} rows, {list(people.columns[:5])}...")
    
    logger.info("Debug run completed successfully")
    
except Exception as e:
    logger.error(f"Error encountered: {e}", exc_info=True)
    sys.exit(1)