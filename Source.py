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
import time
import warnings

# Suppress the RequestsDependencyWarning for a cleaner UI
warnings.filterwarnings("ignore", category=UserWarning, module='requests')

colorama.init()

# Styling
RESET = colorama.Style.RESET_ALL
GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW
CYAN = colorama.Fore.CYAN
RED = colorama.Fore.RED

BASE_URL = "https://news.google.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def init_db():
    conn = sqlite3.connect("scraper.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS articles 
                      (title TEXT, url TEXT UNIQUE, summary TEXT, sentiment REAL, 
                       author TEXT, image_url TEXT, category TEXT)''')
    conn.commit()
    conn.close()

def scrape_article_links():
    """Finds article links using the 2026 Google News pattern."""
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()

        # Look for any anchor tag containing the article path pattern
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            if "articles/" in href:
                # Clean and resolve relative URLs
                clean_href = href.lstrip('./')
                full_url = urljoin(BASE_URL, clean_href)
                links.add(full_url)
        
        return list(links)
    except Exception as e:
        print(f"{RED}❌ Scrape Error: {e}{RESET}")
        return []

def process_and_save(url):
    """Fetches, summarizes, and saves a single article."""
    try:
        # 1. Extract Content
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Try to find a clean title
        title = soup.title.string.split(" - ")[0] if soup.title else "Untitled Article"
        
        # Extract text from paragraphs, filtering out short snippets (ads/menus)
        paragraphs = soup.find_all('p')
        text = " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 60])
        
        if not text or len(text) < 300: 
            return # Skip if content is too thin for a summary

        # 2. AI Summarization
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        # Get a 2-sentence summary
        summary_sentences = summarizer(parser.document, 2)
        summary = " ".join([str(s) for s in summary_sentences])
        
        # 3. Sentiment & Category
        sentiment = TextBlob(text).sentiment.polarity
        
        category = "General"
        keywords = {
            "Technology": ["ai", "tech", "software", "google", "apple", "crypto", "silicon"],
            "Politics": ["government", "policy", "court", "election", "senate", "president"],
            "Sports": ["nba", "nfl", "football", "match", "win", "stadium", "olympics"],
            "Business": ["stocks", "market", "economy", "finance", "ceo", "banking"]
        }
        
        search_blob = (title + " " + text[:500]).lower()
        for cat, words in keywords.items():
            if any(w in search_blob for w in words):
                category = cat
                break

        # 4. Save to SQLite
        conn = sqlite3.connect("scraper.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (title, url, summary, sentiment, "Unknown", "N/A", category))
        conn.commit()
        conn.close()
        
        # Visual feedback for progress
        print(f"{GREEN}✔ Saved:{RESET} {title[:60]}...")

    except Exception:
        # We fail silently on individual articles to keep the multi-threaded loop moving
        pass

def main():
    init_db()
    while True:
        print(f"\n{CYAN}🚀 NEWS SCRAPER AI - 2026 EDITION{RESET}")
        print("1. Scrape & Analyze New Articles")
        print("2. View Saved Collection")
        print("3. Exit")
        
        choice = input(f"{YELLOW}Select an option: {RESET}")

        if choice == "1":
            links = scrape_article_links()
            if not links:
                print(f"{RED}❌ No links found. Check your internet connection.{RESET}")
                continue
                
            print(f"{YELLOW}🔎 Found {len(links)} links. Processing the top 10...{RESET}")
            
            # Use 5 threads to process articles in parallel
            with ThreadPoolExecutor(max_workers=5) as executor:
                executor.map(process_and_save, links[:10])
                
            print(f"{GREEN}✨ Done! Check 'View Saved' to see results.{RESET}")
            
        elif choice == "2":
            conn = sqlite3.connect("scraper.db")
            articles = conn.execute("SELECT title, category, sentiment, url FROM articles").fetchall()
            conn.close()
            
            if not articles:
                print(f"{RED}📭 Database is empty. Run a scrape first!{RESET}")
            else:
                print(f"\n{CYAN}📜 SAVED ARTICLES:{RESET}")
                for idx, (title, cat, sent, url) in enumerate(articles, 1):
                    # Pick an emoji based on sentiment
                    mood = "😊" if sent > 0.1 else "😠" if sent < -0.1 else "😐"
                    print(f"{idx}. {mood} [{cat}] {title}")
                    print(f"   🔗 {url}")
                
        elif choice == "3":
            print(f"{RED}Closing connection... Goodbye!{RESET}")
            break

if __name__ == "__main__":
    main()
