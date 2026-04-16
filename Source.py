import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import sqlite3
from urllib.parse import urljoin
import colorama
from concurrent.futures import ThreadPoolExecutor

colorama.init()

# Styling
RESET = colorama.Style.RESET_ALL
GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW
CYAN = colorama.Fore.CYAN
RED = colorama.Fore.RED

BASE_URL = "https://news.google.com/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}

def init_db():
    conn = sqlite3.connect("scraper.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS articles 
                      (title TEXT, url TEXT UNIQUE, summary TEXT, sentiment REAL, 
                       author TEXT, image_url TEXT, category TEXT)''')
    conn.commit()
    conn.close()

def scrape_article_links():
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Google News uses specific classes for articles; finding all <a> tags is a good fallback
        links = set()
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            if href.startswith("./articles/"):
                full_url = urljoin(BASE_URL, href)
                links.add(full_url)
        
        return list(links)
    except Exception as e:
        print(f"{RED}❌ Scrape Error: {e}{RESET}")
        return []

def process_and_save(url):
    """Fetches, summarizes, and saves a single article."""
    try:
        # 1. Extract
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        title = soup.title.string.split(" - ")[0] if soup.title else "No Title"
        paragraphs = soup.find_all('p')
        text = " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 50])
        
        if not text or len(text) < 200: return # Skip thin content
        
        # 2. Analyze
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = " ".join([str(s) for s in summarizer(parser.document, 2)])
        sentiment = TextBlob(text).sentiment.polarity
        
        # 3. Categorize
        category = "General"
        keywords = {
            "Technology": ["AI", "tech", "software", "google", "apple", "data"],
            "Politics": ["government", "policy", "court", "election"],
            "Sports": ["nba", "nfl", "football", "match", "win"],
            "Finance": ["stocks", "market", "economy", "crypto"]
        }
        for cat, words in keywords.items():
            if any(w in title.lower() or w in text.lower()[:500] for w in words):
                category = cat
                break

        # 4. Save
        conn = sqlite3.connect("scraper.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (title, url, summary, sentiment, "Unknown", "N/A", category))
        conn.commit()
        conn.close()
        print(f"{GREEN}✅ Processed: {title[:50]}...{RESET}")

    except Exception:
        pass # Silently skip failed individual articles

def main():
    init_db()
    while True:
        print(f"\n{CYAN}--- News Scraper AI ---{RESET}")
        print("1. Scrape New Articles (Fast Multi-thread)")
        print("2. View All Saved")
        print("3. Exit")
        
        choice = input(f"{YELLOW}Choice: {RESET}")

        if choice == "1":
            links = scrape_article_links()
            print(f"{YELLOW}Found {len(links)} links. Processing top 10...{RESET}")
            with ThreadPoolExecutor(max_workers=5) as executor:
                executor.map(process_and_save, links[:10])
        elif choice == "2":
            conn = sqlite3.connect("scraper.db")
            for row in conn.execute("SELECT title, category, url FROM articles"):
                print(f"📌 {row[1]} | {row[0]}\n   🔗 {row[2]}")
            conn.close()
        elif choice == "3":
            break

if __name__ == "__main__":
    main()
