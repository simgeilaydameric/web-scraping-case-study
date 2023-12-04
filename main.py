from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging

# GLOBAL VARIABLES
# Variable to store the combined text content from scraped articles
all_text = ""

# Define the log file name
log_file = "logs.log"

# Configure logging to write messages to the specified log file
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')


def generate_bar_chart(top_words):
    try:
        # Unpack the top_words tuple into separate lists for words and counts
        words, counts = zip(*top_words)

        # Create a bar chart using Matplotlib
        plt.figure(figsize=(10, 5))
        plt.bar(words, counts, color='skyblue')

        # Set labels and title for the chart
        plt.xlabel('Words')
        plt.ylabel('Usage Frequency')
        plt.title('Top 10 Most Used Words')

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')

        # Adjust layout for better spacing
        plt.tight_layout()

        # Save the chart as an image file
        plt.savefig("barchart.png", bbox_inches='tight', pad_inches=0.1)

        plt.show()

    except Exception as e:
        print(f"An error occurred while generating the bar chart: {e}")
        logging.error(f"An error occurred while generating the bar chart: {e}")


def connect_to_mongodb():
    try:
        # Connect to MongoDB server running on localhost at port 27017
        client = MongoClient("mongodb://localhost:27017")
        print("Database connection established")

        # Access or create a database named 'simge_ilayda_meric'
        db = client['simge_ilayda_meric']

        return client, db
    except Exception as e:
        logging.error(f"An error occurred while connecting to MongoDB: {e}")


def scrape_data(url):
    try:
        # Fetch the HTML content from the given URL
        html_text = requests.get(url).text

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_text, 'lxml')

        # Find all news articles on the page with the specified class
        news_list = soup.find_all('article', class_='col-12')
        data_list = []
        global all_text

        for news in news_list:
            # Extract link to the full article
            link = news.find('a', class_='post-link')['href']

            # Fetch the HTML content of the full article
            article_html_text = requests.get(link).text
            article_soup = BeautifulSoup(article_html_text, 'lxml')

            # Extract header and summary of the article
            header = article_soup.find('h1', class_='single_title').text.strip()
            summary = article_soup.find('p').text.strip()

            # Extract and join text content of the article
            text_elements = article_soup.select('.yazi_icerik')
            text = " ".join(paragraph.text.strip() for paragraph in text_elements)
            all_text += text

            # Extract image URLs from the article
            img_tags = article_soup.select("#homecontent > div:nth-child(2) > div.row > div.col-12.col-lg-8 > div img")
            img_url_list = [img_tag.get("data-src") for img_tag in img_tags if img_tag.get("data-src")]

            # Extract and format publish and update dates
            publish_date_tag = article_soup.find('time')
            if publish_date_tag and 'datetime' in publish_date_tag.attrs:
                publish_date = publish_date_tag['datetime'].split()[0]
            else:
                publish_date = None

            update_date_tag = article_soup.find('time')
            if update_date_tag and 'datetime' in update_date_tag.attrs:
                update_date = update_date_tag['datetime'].split()[0]
            else:
                update_date = None

            # Append the extracted data to the list
            data_list.append({
                'url': link,
                'header': header,
                'summary': summary,
                'text': text,
                'img_url_list': img_url_list,
                'publish_date': publish_date,
                'update_date': update_date
            })
        return data_list
    except requests.exceptions.RequestException as e:
        print(f"An error occurred:  {e}")
        logging.error(f"An error occurred:  {e}")
        return []


def scrape_and_store_data_worker(args):
    # Unpack arguments
    db, total_pages, page_number = args

    # Construct the URL for the current page
    base_url = 'https://turkishnetworktimes.com/kategori/gundem/page/'
    url = f'{base_url}{page_number}/'

    try:
        # Call the scrape_data function to retrieve data from the URL
        data = scrape_data(url)

        # Log the current URL being processed
        logging.info(f"Su an islenen URL:{url}")

        # Initialize success and failure counts
        success_count = 1
        fail_count = 0
    except requests.exceptions.RequestException:
        # Handle an exception if it occurs during data scraping
        success_count = 0
        fail_count = 1

        # Log the URL where the error occurred
        logging.info(f"URL:{url} islenirken hata meydana geldi")

    # Iterate through the scraped data and update/insert into the MongoDB collection
    for entry in data:
        filter_criteria = {'url': entry['url']}

        # Update or insert the entry into the 'news' collection in MongoDB
        db.news.update_one(filter_criteria, {'$set': entry}, upsert=True)

    return success_count, fail_count, len(data)


def scrape_and_store_data(db, total_pages):
    # Generate a list of arguments for each page number
    args_list = [(db, total_pages, page_number) for page_number in range(1, total_pages + 1)]

    # Use ThreadPoolExecutor to concurrently execute scrape_and_store_data_worker for each page
    with ThreadPoolExecutor() as executor:
        # Map the function onto the list of arguments and collect the results
        results = executor.map(scrape_and_store_data_worker, args_list)

    # Unpack the results into separate lists for success, failure, and total counts
    success_count, fail_count, total_count = zip(*results)

    return sum(success_count), sum(fail_count), sum(total_count)


def analyze_and_store_word_frequency(db):
    # Convert all_text to lowercase for case-insensitive word frequency analysis
    global all_text
    all_text = all_text.lower()

    # Convert all_text to lowercase for case-insensitive word frequency analysis
    word_counts = Counter(all_text.split())

    # Extract the 10 most common words and their counts
    most_common_words = word_counts.most_common(10)

    # Generate and display a bar chart of the most common words
    generate_bar_chart(most_common_words)

    # Iterate through the most common words and store them in the 'word_frequency' collection in MongoDB
    for word, count in most_common_words:
        db.word_frequency.insert_one({
            "word": word,
            "count": int(count)
        })


def group_and_display_by_update_date(db):
    try:
        # Define an aggregation pipeline to group documents by 'update_date'
        pipeline = [
            {"$group": {"_id": "$update_date", "data": {"$push": "$$ROOT"}}},
            {"$sort": {"_id": 1}} # Sort the groups by update_date in ascending order
        ]

        # Execute the aggregation pipeline on the 'news' collection in MongoDB
        grouped_data = list(db.news.aggregate(pipeline))

        # Check if there are grouped data
        if grouped_data:
            print("Data grouped by update dates:")
            print("---------------------------------------------")

            # Iterate through each group and display information
            for group in grouped_data:
                update_date = group['_id']
                print(f"Tarih: {update_date}")

                # Display individual entries in the group
                for entry in group['data']:
                    print(entry)

                print("---------------------------------------------")
        else:
            print("No data grouped by update dates found.")

    except Exception as e:
        print(f"Error occurred during grouping: {e}")


def update_stats_collection(db, success_count, fail_count, total_count, start_time):
    # Get the current timestamp for the end time
    end_time = datetime.now()

    # Calculate the elapsed time in seconds
    elapsed_time = (end_time - start_time).total_seconds()

    # Get the current date and time in a formatted string
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Insert a document into the 'stats' collection in MongoDB with relevant statistics
    db.stats.insert_one({
        "elapsed_time": elapsed_time,       # Elapsed time for the entire process
        "count": total_count,               # Total count of processed items
        "date": date,                       # Current date and time
        "success_count": success_count,     # Count of successful operations
        "fail_count": fail_count,           # Count of failed operations
    })


def main():
    try:
        # Record the start time for measuring the total execution time
        start_time = datetime.now()

        # Establish a connection to the MongoDB database
        client, db = connect_to_mongodb()

        # Set the total number of pages to scrape
        total_pages = 50

        # Scrape and store data, and obtain counts for success, failure, and total processed items
        success_count, fail_count, total_count = scrape_and_store_data(db, total_pages)

        # Analyze word frequency in the collected text and store the results in MongoDB
        analyze_and_store_word_frequency(db)

        # Group and display data by update date from the 'news' collection
        group_and_display_by_update_date(db)

        # Update statistics collection in MongoDB with relevant information
        update_stats_collection(db, success_count, fail_count, total_count, start_time)
    except Exception as e:
        print(f"An error occurred: {e}")
        logging.error("An error occurred.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
