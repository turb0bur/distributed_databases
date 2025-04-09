import argparse
import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from faker import Faker

from generate_data import generate_news_item
from queries import ElasticSearchQueries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NewsApp")

def parse_args():
    parser = argparse.ArgumentParser(description='Elasticsearch News Application')
    
    # News data generation arguments
    parser.add_argument('--seed-news', action='store_true', help='Generate and index news data')
    parser.add_argument('--news-num-docs', type=int, default=100000, help='Number of news documents to generate (default: 100000)')
    parser.add_argument('--news-batch-size', type=int, default=5000, help='Batch size for news indexing (default: 5000)')
    
    # Articles data generation arguments
    parser.add_argument('--seed-articles', action='store_true', help='Generate and index articles data')
    parser.add_argument('--articles-num-docs', type=int, default=500, help='Number of articles to generate (default: 500)')
    parser.add_argument('--articles-batch-size', type=int, default=50, help='Batch size for articles indexing (default: 50)')
    
    return parser.parse_args()

def connect_to_elasticsearch():
    load_dotenv()
    
    es_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
    es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
    es_user = os.getenv("ELASTICSEARCH_USER", "elastic")
    es_pass = os.getenv("ELASTICSEARCH_PASSWORD", "changeme")
    
    try:
        client = Elasticsearch(
            f"http://{es_host}:{es_port}",
            basic_auth=(es_user, es_pass),
            verify_certs=False
        )
        
        if client.ping():
            logger.info("Successfully connected to Elasticsearch")
            return client
        else:
            logger.error("Could not connect to Elasticsearch")
            return None
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {str(e)}")
        return None

def setup_index(client):
    index_name = "news"
    
    if client.indices.exists(index=index_name):
        logger.info(f"Index {index_name} already exists")
        return
    
    mappings = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "url": {"type": "keyword"},
                "text": {"type": "text"},
                "published_at": {"type": "date"},
                "section": {"type": "keyword"},
                "indexed_at": {"type": "date"},
                "author": {"type": "text"}
            }
        }
    }
    
    try:
        client.indices.create(index=index_name, body=mappings)
        logger.info(f"Created index {index_name} with mappings")
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")

def run_queries(queries):
    """Run example queries to demonstrate Elasticsearch functionality"""
    
    logger.info("\n" + "="*80)
    logger.info("BASIC OPERATIONS")
    logger.info("="*80)
    
    # Basic operations
    queries.print_query_result("Insert a single document", queries.insert_single_document)
    queries.print_query_result("Basic search", queries.basic_search)
    queries.print_query_result("Count documents", queries.count_documents)
    queries.print_query_result("Get 1000 documents", queries.get_batch)
    
    logger.info("\n" + "="*80)
    logger.info("SEARCH OPERATIONS")
    logger.info("="*80)
    
    # Search operations
    queries.print_query_result("Exact phrase match", queries.exact_phrase_match, "news about politics")
    queries.print_query_result("Fuzzy match", queries.fuzzy_match, "poltics", "AUTO")
    
    now = datetime.now()
    three_months_ago = (now - timedelta(days=90)).isoformat()
    one_month_ago = (now - timedelta(days=30)).isoformat()
    queries.print_query_result(
        "Time-bounded search", 
        queries.time_bounded_search,
        "technology",
        three_months_ago,
        one_month_ago
    )
    
    logger.info("\n" + "="*80)
    logger.info("AGGREGATIONS")
    logger.info("="*80)
    
    # Aggregations
    queries.print_query_result("Section aggregation", queries.section_aggregation)
    queries.print_query_result("Date histogram by section", queries.date_histogram_by_section, "politics")
    
    logger.info("\n" + "="*80)
    logger.info("ADVANCED OPERATIONS")
    logger.info("="*80)
    
    # Advanced operations
    queries.print_query_result("Create articles index", queries.create_articles_index)
    queries.print_query_result("Add index alias", queries.add_index_alias)
    queries.print_query_result("Update text_length field", queries.update_add_text_length)
    queries.print_query_result("Text length histogram", queries.text_length_histogram)
    queries.print_query_result("Multi-Index Date Histogram", queries.multi_index_date_histogram)

def main():
    args = parse_args()
    
    client = connect_to_elasticsearch()
    if not client:
        return
    
    queries = ElasticSearchQueries(client)
    
    should_seed_news = os.getenv("SEED_NEWS", "false").lower() == "true" or args.seed_news
    news_num_docs = int(os.getenv("NEWS_NUM_DOCS", str(args.news_num_docs)))
    news_batch_size = int(os.getenv("NEWS_BATCH_SIZE", str(args.news_batch_size)))
    
    if should_seed_news:
        logger.info(f"Seeding news index with {news_num_docs} documents (batch size: {news_batch_size})")
        result = queries.generate_news_data(news_num_docs, news_batch_size)
        logger.info(f"News seeding result: {result}")
    
    should_seed_articles = os.getenv("SEED_ARTICLES", "false").lower() == "true" or args.seed_articles
    articles_num_docs = int(os.getenv("ARTICLES_NUM_DOCS", str(args.articles_num_docs)))
    articles_batch_size = int(os.getenv("ARTICLES_BATCH_SIZE", str(args.articles_batch_size)))
    
    if should_seed_articles:
        logger.info(f"Generating articles data: {articles_num_docs} documents with batch size {articles_batch_size}")
        result = queries.generate_articles_data(articles_num_docs, articles_batch_size)
        logger.info(f"Articles data generation result: {result}")
    
    logger.info("Running queries on existing data")
    run_queries(queries)

if __name__ == "__main__":
    main() 