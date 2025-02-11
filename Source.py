import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import sqlite3
from urllib.parse import urljoin
import os
import colorama  # ✅ Fix Colors for Windows
colorama.init()

# ✅ Fix Colors using colorama (Works on all OS)
RESET = colorama.Style.RESET_ALL
GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW
CYAN = colorama.Fore.CYAN
RED = colorama.Fore.RED

# ✅ Correct Google News URL
BASE_URL = "https://news.google.com/"

# ✅ Function to scrape articles
def scrape_articles():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(BASE_URL, headers=headers)

    if response.status_code != 200:
        print(f"{RED}❌ Failed to retrieve data!{RESET}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []

    for tag in soup.find_all('a', href=True):
        link = tag['href']
        if link.startswith("./"):  # ✅ Convert relative URLs to full URLs
            link = urljoin(BASE_URL, link[1:])  # Remove leading `.`
        
        articles.append(link)

    print(f"{GREEN}✅ Total articles found: {len(articles)}{RESET}")
    return articles

# ✅ Extract article details (title, summary, etc.)
def extract_article_details(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string if soup.title else "No Title"
        text = " ".join(p.text for p in soup.find_all('p'))
        author = soup.find('meta', attrs={'name': 'author'})
        author = author['content'] if author else "Unknown"
        image = soup.find('meta', property='og:image')
        image_url = image['content'] if image else "No Image Found"

        return title, text, author, image_url

    except Exception as e:
        print(f"{RED}⚠️ Error fetching article: {url} | {e}{RESET}")
        return "No Title", "", "Unknown", "No Image Found"

# ✅ Summarize the article
def summarize_text(text):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, 2)
    return " ".join([str(sentence) for sentence in summary])

# ✅ Analyze sentiment
def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity

# ✅ Categorize articles
def categorize_article(title, text):
    categories = {
        "Technology": ["AI", "tech", "software", "computer", "science"],
        "Politics": ["election", "government", "president", "policy"],
        "Sports": ["game", "tournament", "player", "team"],
        "Business": ["stocks", "market", "finance", "economy"],
        "Health": ["virus", "vaccine", "doctor", "medicine"],
    }

    for category, keywords in categories.items():
        for word in keywords:
            if word.lower() in title.lower() or word.lower() in text.lower():
                return category
    return "General"

# ✅ Save data to SQLite
def save_to_db(title, url, summary, sentiment, author, image_url, category):
    conn = sqlite3.connect("scraper.db")
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS articles 
                      (title TEXT, url TEXT, summary TEXT, sentiment REAL, 
                       author TEXT, image_url TEXT, category TEXT)''')

    cursor.execute("INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)", 
                   (title, url, summary, sentiment, author, image_url, category))
    
    conn.commit()
    conn.close()

# ✅ View saved articles with clickable links
def view_saved_articles():
    conn = sqlite3.connect("scraper.db")
    cursor = conn.cursor()

    cursor.execute("SELECT title, url, category FROM articles")
    articles = cursor.fetchall()

    if not articles:
        print(f"{RED}❌ No articles saved yet!{RESET}")
    else:
        print(f"{YELLOW}\n📜 Saved Articles:{RESET}")
        for i, (title, url, category) in enumerate(articles, 1):
            print(f"{CYAN}{i}. {title} ({category}){RESET}")
            print(f"   🔗 {GREEN}\033]8;;{url}\033\\{url}\033]8;;\033\\{RESET}")

    conn.close()

# ✅ Search articles by category
def search_articles_by_category():
    category = input(f"{YELLOW}🔎 Enter category (Technology, Politics, Sports, Business, Health, General): {RESET}").capitalize()

    conn = sqlite3.connect("scraper.db")
    cursor = conn.cursor()

    cursor.execute("SELECT title, url FROM articles WHERE category=?", (category,))
    articles = cursor.fetchall()

    if not articles:
        print(f"{RED}❌ No articles found in this category!{RESET}")
    else:
        print(f"{YELLOW}\n📂 Articles in {category}:{RESET}")
        for i, (title, url) in enumerate(articles, 1):
            print(f"{CYAN}{i}. {title}{RESET}")
            print(f"   🔗 {GREEN}\033]8;;{url}\033\\{url}\033]8;;\033\\{RESET}")

    conn.close()

# ✅ Interactive Menu
def main():
    while True:
        print(f"\n{GREEN}🔹 News Scraper AI Menu:{RESET}")
        print("1️⃣ Scrape & Save New Articles")
        print("2️⃣ View Saved Articles")
        print("3️⃣ Search Articles by Category")
        print("4️⃣ Exit")

        choice = input(f"{YELLOW}Enter your choice (1-4): {RESET}")

        if choice == "1":
            article_links = scrape_articles()

            for link in article_links[:5]:  # ✅ Limit to first 5 articles
                title, text, author, image_url = extract_article_details(link)

                if text:
                    summary = summarize_text(text)
                    sentiment = analyze_sentiment(summary)
                    category = categorize_article(title, text)

                    save_to_db(title, link, summary, sentiment, author, image_url, category)

                    print(f"\n{GREEN}✅ Article Saved:{RESET}")
                    print(f"📰 {title}")
                    print(f"🔗 {GREEN}\033]8;;{link}\033\\{link}\033]8;;\033\\{RESET}")  # ✅ Clickable link
                    print(f"✍️ {author}")
                    print(f"🖼️ {image_url}")
                    print(f"📖 {summary}")
                    print(f"📊 Sentiment Score: {sentiment:.2f}")
                    print(f"📌 Category: {category}")
                    print("-" * 60)

        elif choice == "2":
            view_saved_articles()

        elif choice == "3":
            search_articles_by_category()

        elif choice == "4":
            print(f"{RED}🚪 Exiting... Goodbye!{RESET}")
            break

        else:
            print(f"{RED}⚠️ Invalid choice! Enter a number between 1 and 4.{RESET}")

if __name__ == "__main__":
    main()
