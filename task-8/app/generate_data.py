import logging
import random
import uuid
from datetime import datetime, timedelta

from faker import Faker
from tqdm import tqdm

logger = logging.getLogger("NewsApp")
fake = Faker()

# News generation constants
SECTIONS = [
    "politics", "technology", "business", "entertainment", 
    "sports", "health", "science", "world"
]
MIN_TEXT_LENGTH = 50
MAX_TEXT_LENGTH = 10000
MAX_TITLE_LENGTH = 200
DOMAINS = ["example.com", "news.com", "dailynews.org", "globalnews.net", "thenews.io"]

# Article generation constants
JOURNALS = [
    "Journal of Data Science", "AI Research Quarterly", 
    "Computational Biology Today", "Modern Physics Review",
    "Sustainable Engineering", "Chemical Innovations", 
    "Psychology Studies", "Economics Trends"
]
ARTICLE_SECTIONS = [
    "computer_science", "biology", "physics", "chemistry", 
    "psychology", "economics", "engineering", "mathematics"
]

def generate_news_item():
    """Generate a single news item with realistic data"""
    now = datetime.now()
    published_at = fake.date_time_between(
        start_date="-1y",
        end_date="now"
    )
    
    time_diff = now - published_at
    indexed_at = published_at + timedelta(seconds=random.randint(1, int(time_diff.total_seconds())))
    
    text_length = random.randint(MIN_TEXT_LENGTH, MAX_TEXT_LENGTH)
    text = fake.paragraph(nb_sentences=20)
    while len(text) < text_length:
        text += " " + fake.paragraph(nb_sentences=10)
    text = text[:MAX_TEXT_LENGTH]
    
    title = fake.sentence(nb_words=6)
    
    domain = random.choice(DOMAINS)
    url_path = "-".join(title.lower().split()[:5])
    url = f"https://www.{domain}/news/{url_path}-{str(uuid.uuid4())[:8]}"
    
    author = fake.name()
    section = random.choice(SECTIONS)
    
    return {
        "title": title,
        "url": url,
        "text": text,
        "published_at": published_at.isoformat(),
        "section": section,
        "indexed_at": indexed_at.isoformat(),
        "author": author
    }

def generate_article():
    """Generate a single scientific article document"""
    now = datetime.now()
    published_at = fake.date_time_between(start_date="-2y", end_date="-30d")
    
    time_diff = now - published_at
    indexed_at = published_at + timedelta(seconds=random.randint(1, int(time_diff.total_seconds())))
    
    paragraphs = [fake.paragraph(nb_sentences=15) for _ in range(random.randint(5, 15))]
    text = "\n\n".join(paragraphs)
    
    title = fake.sentence(nb_words=random.randint(5, 12))
    journal = random.choice(JOURNALS)
    section = random.choice(ARTICLE_SECTIONS)
    author = fake.name() + ", " + fake.name() + ", et al."
    
    return {
        "title": title,
        "url": f"https://doi.org/10.{random.randint(1000, 9999)}/{uuid.uuid4().hex[:8]}",
        "text": text,
        "published_at": published_at.isoformat(),
        "section": section,
        "indexed_at": indexed_at.isoformat(),
        "author": author,
        "journal": journal,
        "citations": random.randint(0, 500)
    }

def generate_news_batch(batch_size=1000):
    """Generate a batch of news items"""
    return [generate_news_item() for _ in range(batch_size)]

def generate_articles_batch(batch_size=50):
    """Generate a batch of scientific articles"""
    return [generate_article() for _ in range(batch_size)]

def generate_data_generator(num_docs, batch_size, data_type="news"):
    """Generator to yield batches of data (news or articles)"""
    generate_func = generate_news_item if data_type == "news" else generate_article
    
    for i in range(0, num_docs, batch_size):
        current_batch_size = min(batch_size, num_docs - i)
        batch = [generate_func() for _ in range(current_batch_size)]
        yield batch

if __name__ == "__main__":
    # Test news generation
    print("=== NEWS SAMPLE ===")
    for item in [generate_news_item() for _ in range(1)]:
        print(f"Title: {item['title']}")
        print(f"URL: {item['url']}")
        print(f"Section: {item['section']}")
        print(f"Published: {item['published_at']}")
        print(f"Indexed: {item['indexed_at']}")
        print(f"Author: {item['author']}")
        print(f"Text length: {len(item['text'])}")
        print("---")
    
    # Test article generation
    print("\n=== ARTICLE SAMPLE ===")
    for item in [generate_article() for _ in range(1)]:
        print(f"Title: {item['title']}")
        print(f"URL: {item['url']}")
        print(f"Section: {item['section']}")
        print(f"Journal: {item['journal']}")
        print(f"Citations: {item['citations']}")
        print(f"Published: {item['published_at']}")
        print(f"Indexed: {item['indexed_at']}")
        print(f"Author: {item['author']}")
        print(f"Text length: {len(item['text'])}")
        print("---") 