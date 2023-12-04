# Project Title

A Python program for web scraping, MongoDB interaction, data analysis, and statistics collection.

## Overview

This Python script performs various operations such as scraping news articles from a website, storing data in MongoDB, analyzing word frequency, and collecting statistics.

## Functionality Summary

### Data Scraping

- The `scrape_data` function extracts news articles from a specified website.
- The `scrape_and_store_data_worker` function retrieves data from a specific page and stores it in MongoDB.
- The `scrape_and_store_data` function retrieves and processes data from a range of pages in parallel.

### MongoDB Interaction

- The `connect_to_mongodb` function establishes a connection to a MongoDB database.
- The `scrape_and_store_data_worker` function adds the scraped data to MongoDB.
- The `group_and_display_by_update_date` function groups data in MongoDB based on update dates.

### Data Analysis

- The `analyze_and_store_word_frequency` function analyzes word frequency in the text content of scraped articles.
- It generates bar charts for the top 10 most used words and stores the results in MongoDB.

### Statistics Collection

- The `update_stats_collection` function collects statistics such as elapsed time, success and failure counts, and stores them in MongoDB.

### Main Program

- The `main` function orchestrates the above functionalities in sequence.

### Error Handling and Logging

- `try-except` blocks handle potential errors during execution, and errors are logged in the `logs.log` file.

## Installation Instructions

1. Clone the repository to your local machine.
2. Install the required dependencies using `pip install -r requirements.txt`.
3. Make sure you have MongoDB installed and running on your local machine.

## Usage

1. Run the `main` function to execute the entire data processing workflow.

## Dependencies

- BeautifulSoup
- requests
- pymongo
- matplotlib
- datetime
- concurrent.futures
- logging

## Analysis Results

- The word frequency analysis results are stored in MongoDB.
- Bar charts for the top 10 most used words can be found in the project directory (`barchart.png`).  
![Bar Chart](https://github.com/simgeilaydameric/web-scraping-case-study/blob/main/assets/barchart.png)
- Log information is available in the `logs.log` file.

## Important Notes

- Ensure compliance with the terms of use of the website being scraped.
- Be aware of legal regulations related to web scraping.

## License

This project is licensed under the [MIT License](LICENSE).





