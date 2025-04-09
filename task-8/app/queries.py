import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

import elasticsearch
from elasticsearch.helpers import bulk

import generate_data

logger = logging.getLogger("NewsApp")

class ElasticSearchQueries:
    def __init__(self, es_client):
        self.client = es_client
        self.index_name = "news"
        
    def print_query_result(self, title, query_func, *args, **kwargs):
        """Helper to print query results with formatting"""
        print("\n" + "="*80)
        print(f"QUERY: {title}")
        print("="*80)
        
        result = query_func(*args, **kwargs)
        if isinstance(result, dict) and 'query' in result:
            print(f"Query DSL:\n{json.dumps(result['query'], indent=2)}")
            
        if isinstance(result, dict) and 'result' in result:
            if isinstance(result['result'], dict):
                print(f"Result:\n{json.dumps(result['result'], indent=2)}")
            else:
                print(f"Result: {result['result']}")
        else:
            print(f"Result: {result}")
        
        print("-"*80)
        return result
    
    def insert_single_document(self, doc_id="1", doc=None):
        """Insert a single document with a specified ID"""
        if doc is None:
            doc = {
                "title": "Sample news article for direct insertion",
                "url": "https://www.example.com/news/sample-direct-insertion",
                "text": "This is a sample news article that was inserted directly via the Elasticsearch API.",
                "published_at": datetime.now().isoformat(),
                "section": "tech",
                "indexed_at": datetime.now().isoformat(),
                "author": "API User"
            }
        
        response = self.client.index(
            index=self.index_name,
            id=doc_id,
            document=doc,
            refresh=True
        )
        
        return {
            "query": {"index": {"_id": doc_id}},
            "result": {
                "result": response["result"],
                "id": response["_id"],
                "index": response["_index"]
            }
        }
    
    def basic_search(self, size=10):
        """Basic search query returning first documents"""
        response = self.client.search(
            index=self.index_name,
            query={"match_all": {}},
            size=size
        )
        
        return {
            "query": {"match_all": {}},
            "result": {
                "total": response["hits"]["total"]["value"],
                "sample_hits": [hit["_source"]["title"] for hit in response["hits"]["hits"]]
            }
        }
    
    def count_documents(self):
        """Count documents in the index"""
        response = self.client.count(index=self.index_name)
        
        return {
            "query": {"count": {"index": self.index_name}},
            "result": response["count"]
        }
    
    def get_batch(self, size=1000):
        """Get a larger batch of documents"""
        response = self.client.search(
            index=self.index_name,
            body={
                "query": {"match_all": {}},
                "size": size,
                "_source": ["title", "section", "author"]
            }
        )
        
        return {
            "query": {"match_all": {}},
            "result": {
                "total": response["hits"]["total"]["value"],
                "returned": len(response["hits"]["hits"]),
                "sample_hits": [hit["_source"]["title"] for hit in response["hits"]["hits"][:5]]
            }
        }
    
    def exact_phrase_match(self, phrase):
        """Search for documents with exact phrase match"""
        query = {
            "match_phrase": {
                "text": phrase
            }
        }
        
        response = self.client.search(
            index=self.index_name,
            query=query,
            size=10
        )
        
        return {
            "query": query,
            "result": {
                "total": response["hits"]["total"]["value"],
                "sample_hits": [hit["_source"]["title"] for hit in response["hits"]["hits"]]
            }
        }
    
    def fuzzy_match(self, phrase, fuzziness="AUTO"):
        """Search for documents with fuzzy matching"""
        query = {
            "query": {
                "match": {
                    "text": {
                        "query": phrase,
                        "fuzziness": fuzziness
                    }
                }
            },
            "size": 10
        }
        
        response = self.client.search(index=self.index_name, body=query)
        
        return {
            "query": query["query"],
            "result": {
                "total": response["hits"]["total"]["value"],
                "sample_hits": [hit["_source"]["title"] for hit in response["hits"]["hits"]]
            }
        }
    
    def time_bounded_search(self, phrase, start_date, end_date):
        """Search with time range and phrase"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"text": phrase}}
                    ],
                    "filter": [
                        {
                            "range": {
                                "published_at": {
                                    "gte": start_date,
                                    "lte": end_date
                                }
                            }
                        }
                    ]
                }
            },
            "size": 10
        }
        
        response = self.client.search(index=self.index_name, body=query)
        
        return {
            "query": query["query"],
            "result": {
                "total": response["hits"]["total"]["value"],
                "sample_hits": [
                    {
                        "title": hit["_source"]["title"],
                        "published_at": hit["_source"]["published_at"]
                    } for hit in response["hits"]["hits"]
                ]
            }
        }
    
    def section_aggregation(self):
        """Aggregate news by section"""
        query = {
            "size": 0,
            "aggs": {
                "sections": {
                    "terms": {
                        "field": "section",
                        "size": 20
                    }
                }
            }
        }
        
        response = self.client.search(index=self.index_name, body=query)
        
        return {
            "query": query["aggs"],
            "result": {
                "sections": [
                    {
                        "section": bucket["key"],
                        "count": bucket["doc_count"]
                    } for bucket in response["aggregations"]["sections"]["buckets"]
                ]
            }
        }
    
    def date_histogram_by_section(self, section):
        """Create date histogram for a specific section"""
        query = {
            "size": 0,
            "query": {
                "term": {
                    "section": section
                }
            },
            "aggs": {
                "articles_over_time": {
                    "date_histogram": {
                        "field": "published_at",
                        "calendar_interval": "day",
                        "format": "yyyy-MM-dd"
                    }
                }
            }
        }
        
        response = self.client.search(index=self.index_name, body=query)
        
        return {
            "query": {
                "filter": query["query"],
                "aggs": query["aggs"]
            },
            "result": {
                "section": section,
                "total": sum(bucket["doc_count"] for bucket in response["aggregations"]["articles_over_time"]["buckets"]),
                "histogram": [
                    {
                        "date": bucket["key_as_string"],
                        "count": bucket["doc_count"]
                    } for bucket in response["aggregations"]["articles_over_time"]["buckets"]
                    if bucket["doc_count"] > 0
                ][:10]
            }
        }
    
    def create_articles_index(self):
        """Create a new index with explicit mapping"""
        index_name = "articles"
        index_config = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "title": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "url": {
                        "type": "keyword"
                    },
                    "text": {
                        "type": "text"
                    },
                    "published_at": {
                        "type": "date"
                    },
                    "section": {
                        "type": "keyword"
                    },
                    "indexed_at": {
                        "type": "date"
                    },
                    "author": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "journal": {
                        "type": "keyword"
                    },
                    "doi": {
                        "type": "keyword"
                    }
                }
            }
        }
        
        if not self.client.indices.exists(index=index_name):
            result = self.client.indices.create(index=index_name, body=index_config)
            return {
                "query": index_config,
                "result": {
                    "acknowledged": result.get("acknowledged", False),
                    "index": index_name
                }
            }
        else:
            return {
                "query": index_config,
                "result": {
                    "status": "Index already exists",
                    "index": index_name
                }
            }
    
    def add_index_alias(self):
        """Add an alias to the news index"""
        alias_name = "recent_news"
        
        try:
            result = self.client.indices.put_alias(index=self.index_name, name=alias_name)
            return {
                "query": {"put_alias": {"index": self.index_name, "name": alias_name}},
                "result": {
                    "acknowledged": result.get("acknowledged", False),
                    "index": self.index_name,
                    "alias": alias_name
                }
            }
        except elasticsearch.exceptions.RequestError as e:
            return {
                "query": {"put_alias": {"index": self.index_name, "name": alias_name}},
                "result": {
                    "error": str(e),
                    "status": "Alias may already exist"
                }
            }
    
    def delete_by_section(self, section):
        """Delete all documents in a given section"""
        query = {
            "query": {
                "term": {
                    "section": section
                }
            }
        }
        
        try:
            result = self.client.delete_by_query(
                index=self.index_name,
                body=query,
                refresh=True
            )
            return {
                "query": query,
                "result": {
                    "deleted": result.get("deleted", 0),
                    "total": result.get("total", 0),
                    "section": section
                }
            }
        except Exception as e:
            return {
                "query": query,
                "result": {
                    "error": str(e)
                }
            }
    
    def update_add_text_length(self):
        """Add text_length field to all documents"""
        script = {
            "script": {
                "source": "ctx._source.text_length = ctx._source.text.length()",
                "lang": "painless"
            },
            "query": {
                "bool": {
                    "must_not": {
                        "exists": {
                            "field": "text_length"
                        }
                    }
                }
            }
        }
        
        try:
            result = self.client.update_by_query(
                index=self.index_name,
                body=script,
                refresh=True,
                wait_for_completion=False,
                timeout="10m"
            )
            return {
                "query": script,
                "result": {
                    "task_id": result.get("task"),
                    "status": "Operation started asynchronously, check _tasks API for status",
                    "message": "Running in background due to large document count"
                }
            }
        except Exception as e:
            return {
                "query": script,
                "result": {
                    "error": str(e)
                }
            }
    
    def text_length_histogram(self):
        """Create histogram of text lengths"""
        query = {
            "size": 0,
            "aggs": {
                "text_length_histogram": {
                    "histogram": {
                        "field": "text_length",
                        "interval": 1000
                    }
                }
            }
        }
        
        response = self.client.search(index=self.index_name, body=query)
        
        return {
            "query": query["aggs"],
            "result": {
                "histogram": [
                    {
                        "length_range": f"{int(bucket['key'])}-{int(bucket['key']) + 999}",
                        "count": bucket["doc_count"]
                    } for bucket in response["aggregations"]["text_length_histogram"]["buckets"]
                    if bucket["doc_count"] > 0
                ]
            }
        }
    
    def multi_index_date_histogram(self):
        """Aggregate date_histogram by indexed_at across multiple indices"""
        query = {
            "size": 0,
            "aggs": {
                "indexed_over_time": {
                    "date_histogram": {
                        "field": "indexed_at",
                        "calendar_interval": "day",
                        "format": "yyyy-MM-dd"
                    }
                }
            }
        }
        
        try:
            indices = ["news", "articles"]
            response = self.client.search(index=",".join(indices), body=query)
            
            return {
                "query": query["aggs"],
                "result": {
                    "indices": indices,
                    "total_buckets": len(response["aggregations"]["indexed_over_time"]["buckets"]),
                    "sample_data": [
                        {
                            "date": bucket["key_as_string"],
                            "count": bucket["doc_count"]
                        } for bucket in response["aggregations"]["indexed_over_time"]["buckets"][:10]
                    ]
                }
            }
        except Exception as e:
            return {
                "query": query["aggs"],
                "result": {
                    "error": str(e),
                    "message": "One of the indices might not exist or have the required field"
                }
            }
    
    def generate_articles_data(self, num_docs=100, batch_size=10):
        """Generate and index sample articles data for the articles index"""
        # Check if articles index exists
        if not self.client.indices.exists(index="articles"):
            self.create_articles_index()
        
        try:
            current_count = self.client.count(index="articles").get("count", 0)
            
            if current_count >= num_docs:
                return {
                    "query": "generate_articles_data",
                    "result": {
                        "status": f"Index 'articles' already contains {current_count} documents",
                        "requested": num_docs
                    }
                }
            
            total_indexed = 0
            
            for batch in generate_data.generate_data_generator(num_docs, batch_size, data_type="articles"):
                actions = [
                    {
                        "_index": "articles",
                        "_source": doc
                    } for doc in batch
                ]
                
                success, failed = bulk(self.client, actions, refresh=True, stats_only=True)
                total_indexed += success
                
                # Add progress logging
                percent_complete = (total_indexed / num_docs) * 100
                logger.info(f"Articles progress: {total_indexed}/{num_docs} documents ({percent_complete:.1f}%)")
                
                if failed > 0:
                    return {
                        "query": "generate_articles_data",
                        "result": {
                            "status": "Partial success",
                            "indexed": total_indexed,
                            "failed": failed,
                            "total": num_docs
                        }
                    }
            
            return {
                "query": "generate_articles_data",
                "result": {
                    "status": "Success",
                    "indexed": total_indexed,
                    "total": num_docs
                }
            }
            
        except Exception as e:
            return {
                "query": "generate_articles_data",
                "result": {
                    "status": "Error",
                    "error": str(e)
                }
            }
    
    def generate_news_data(self, num_docs=100000, batch_size=5000):
        """Generate and index sample news data for the news index"""
        if not self.client.indices.exists(index="news"):
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
            self.client.indices.create(index="news", body=mappings)
        
        try:
            current_count = self.client.count(index="news").get("count", 0)
            
            if current_count >= num_docs:
                return {
                    "query": "generate_news_data",
                    "result": {
                        "status": f"Index 'news' already contains {current_count} documents",
                        "requested": num_docs
                    }
                }
            
            total_indexed = 0
            start_time = time.time()
            
            for batch in generate_data.generate_data_generator(num_docs, batch_size, data_type="news"):
                actions = [
                    {
                        "_index": "news",
                        "_source": doc
                    } for doc in batch
                ]
                
                success, failed = bulk(self.client, actions, refresh=True, stats_only=True)
                total_indexed += success
                
                percent_complete = (total_indexed / num_docs) * 100
                elapsed_time = time.time() - start_time
                
                if total_indexed > batch_size:
                    docs_per_second = total_indexed / elapsed_time
                    remaining_docs = num_docs - total_indexed
                    estimated_seconds_left = remaining_docs / docs_per_second if docs_per_second > 0 else 0
                    estimated_time_str = f", estimated completion in {estimated_seconds_left:.0f} seconds"
                else:
                    estimated_time_str = ""
                
                logger.info(f"News progress: {total_indexed}/{num_docs} documents ({percent_complete:.1f}%){estimated_time_str}")
                
                if failed > 0:
                    return {
                        "query": "generate_news_data",
                        "result": {
                            "status": "Partial success",
                            "indexed": total_indexed,
                            "failed": failed,
                            "total": num_docs
                        }
                    }
            
            return {
                "query": "generate_news_data",
                "result": {
                    "status": "Success",
                    "indexed": total_indexed,
                    "total": num_docs
                }
            }
            
        except Exception as e:
            return {
                "query": "generate_news_data",
                "result": {
                    "status": "Error",
                    "error": str(e)
                }
            }

def search_by_text(client, text: str, size: int = 10) -> List[Dict[str, Any]]:
    query = {
        "query": {
            "multi_match": {
                "query": text,
                "fields": ["title^2", "text"],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        },
        "size": size
    }
    return client.search(index="news", body=query)

def search_by_section(client, section: str, size: int = 10) -> List[Dict[str, Any]]:
    query = {
        "query": {
            "term": {
                "section.keyword": section
            }
        },
        "size": size
    }
    return client.search(index="news", body=query)

def search_by_date_range(client, start_date: str, end_date: str, size: int = 10) -> List[Dict[str, Any]]:
    query = {
        "query": {
            "range": {
                "published_at": {
                    "gte": start_date,
                    "lte": end_date
                }
            }
        },
        "size": size
    }
    return client.search(index="news", body=query)

def search_by_author(client, author: str, size: int = 10) -> List[Dict[str, Any]]:
    query = {
        "query": {
            "match": {
                "author": author
            }
        },
        "size": size
    }
    return client.search(index="news", body=query)

def delete_by_section(client, section: str) -> Dict[str, Any]:
    query = {
        "query": {
            "term": {
                "section.keyword": section
            }
        }
    }
    return client.delete_by_query(index="news", body=query)

def print_query_result(query_name: str, query_func, *args, **kwargs):
    try:
        result = query_func(*args, **kwargs)
        hits = result.get('hits', {}).get('hits', [])
        
        print(f"\n{query_name} Results:")
        print("-" * 50)
        
        if not hits:
            print("No results found.")
            return
            
        for hit in hits:
            source = hit['_source']
            print(f"Title: {source['title']}")
            print(f"Section: {source['section']}")
            print(f"Published: {source['published_at']}")
            print(f"Author: {source['author']}")
            print("-" * 50)
            
    except Exception as e:
        logger.error(f"Error executing {query_name}: {str(e)}")
        print(f"Error: {str(e)}") 