# News Scraper AI

A Python-based news scraper that fetches, summarizes, analyzes sentiment, and categorizes news articles from Google News.

## Features
- **Scrape News Articles**: Automatically fetch latest news articles.
- **Summarization**: Extracts key points from articles using LSA summarization.
- **Sentiment Analysis**: Determines the sentiment of each article.
- **Categorization**: Assigns articles to categories such as Technology, Politics, Sports, Business, and Health.
- **Database Storage**: Saves articles in an SQLite database.
- **Search Functionality**: Retrieve articles by category.
- **Interactive CLI**: User-friendly menu for interacting with stored articles.

## Requirements
- Python 3.x
- `requests`
- `beautifulsoup4`
- `textblob`
- `sumy`
- `sqlite3`
- `colorama`

## Installation
1. Clone this repository:
   ```sh
   git clone https://github.com/yourusername/news-scraper-ai.git
   cd news-scraper-ai
   ```
2. Install required dependencies:
   ```sh
   pip install requests beautifulsoup4 textblob sumy colorama
   ```

## Usage
1. Run the script:
   ```sh
   python scraper.py
   ```
2. Choose an option from the menu:
   - **1️⃣ Scrape & Save New Articles**
   - **2️⃣ View Saved Articles**
   - **3️⃣ Search Articles by Category**
   - **4️⃣ Exit**

## Database Structure
The scraper stores articles in `scraper.db` with the following fields:
- **title**: The article title.
- **url**: The article URL.
- **summary**: Shortened version of the article.
- **sentiment**: Sentiment score (-1 to 1).
- **author**: Author of the article.
- **image_url**: URL of an associated image.
- **category**: Article category (Technology, Politics, Sports, Business, Health, or General).

## Future Improvements
- Add multi-language support.
- Improve article extraction techniques.
- Implement a web-based interface.

## License
This project is licensed under the MIT License.

