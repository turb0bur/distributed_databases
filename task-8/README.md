# Task - Elasticsearch News Application

This application demonstrates working with basic database functions such as full text search using Elasticsearch as an example.

## Requirements
- Learn Elasticsearch data modeling and query concepts
- Store and search news and scientific articles data
- Implement basic and advanced search operations
- Create aggregations for data analysis
- Use Kibana for visualization and querying

## Setup and Running

### Prerequisites
- Docker and Docker Compose
- Bash shell
- `jq` command-line tool (for JSON processing)

### Environment Variables
The application uses environment variables for configuration. These are defined in the `.env` file:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| ELASTIC_VERSION | Elasticsearch version | 8.16.5 |
| ELASTIC_PASSWORD | Password for the elastic user | changeme |
| ES_PORT | Port for Elasticsearch | 9200 |
| KIBANA_PORT | Port for Kibana | 5601 |
| ELASTICSEARCH_HOST | Elasticsearch host | localhost |
| ELASTICSEARCH_PORT | Elasticsearch port | 9200 |
| ELASTICSEARCH_USER | Elasticsearch username | elastic |
| ELASTICSEARCH_PASSWORD | Elasticsearch password | changeme |

For controlling the data generation:
| Variable | Description | Default Value |
|----------|-------------|---------------|
| SEED_NEWS | Flag to generate news data | "false" |
| NEWS_NUM_DOCS | Number of news docs to generate | 100000 |
| NEWS_BATCH_SIZE | Batch size for news indexing | 5000 |
| SEED_ARTICLES | Flag to generate articles data | "false" |
| ARTICLES_NUM_DOCS | Number of articles to generate | 500 |
| ARTICLES_BATCH_SIZE | Batch size for articles indexing | 50 |

### Running the Application

1. Clone the repository
2. Navigate to the project directory
3. Start the application with the run script:
   ```bash
   ./run.sh
   ```

4. Alternatively, use Docker Compose with specific parameters:
   ```bash
   # Start with default settings (no data generation)
   docker-compose up
   
   # Generate 100,000 news documents
   SEED_NEWS=true docker-compose up
   
   # Generate 500 scientific articles 
   SEED_ARTICLES=true docker-compose up
   
   # Generate both news and articles
   SEED_NEWS=true SEED_ARTICLES=true docker-compose up
   
   # Configure generation parameters
   SEED_NEWS=true NEWS_NUM_DOCS=50000 NEWS_BATCH_SIZE=1000 docker-compose up
   SEED_ARTICLES=true ARTICLES_NUM_DOCS=1000 ARTICLES_BATCH_SIZE=100 docker-compose up
   ```

5. Stopping the application:
   ```bash
   docker-compose down
   ```
   
   **Note**: The application is configured to persist both Elasticsearch data and Kibana state (including query history) using Docker volumes, so your data and queries will be preserved even after stopping and restarting the containers.

### Project Structure
```
.
├── docker-compose.yml    # Docker Compose configuration
├── run.sh                # Shell script to run the application
├── .env                  # Environment variables for the application
├── app/                  # Directory containing the application code
    ├── main.py           # Main application entry point
    ├── generate_data.py  # Generates sample news data
    ├── queries.py        # Contains Elasticsearch queries
```

## Implementation Details

### Data Model

1. News Index:
   ```json
   {
     "title": {"type": "text"},
     "url": {"type": "keyword"},
     "text": {"type": "text"},
     "published_at": {"type": "date"},
     "section": {"type": "keyword"},
     "indexed_at": {"type": "date"},
     "author": {"type": "text"}
   }
   ```

2. Articles Index:
   ```json
   {
     "title": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
     "url": {"type": "keyword"},
     "text": {"type": "text"},
     "published_at": {"type": "date"},
     "section": {"type": "keyword"},
     "indexed_at": {"type": "date"},
     "author": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
     "journal": {"type": "keyword"},
     "citations": {"type": "integer"}
   }
   ```

### Key Features
- Full-text search capabilities for news and article content
- Date-range filtering for time-based searches
- Fuzzy matching for error-tolerant searches
- Aggregations for data analysis
- Index aliases for logical grouping
- Field calculation using script-based updates

### Implemented Features

1. **Basic Operations**
   - `insert_single_document()` - Insert a single document into the news index
   - `basic_search()` - Simple search without parameters
   - `count_documents()` - Count documents in the index
   - `get_batch()` - Retrieve a batch of documents

2. **Search Operations**
   - `exact_phrase_match(phrase)` - Match an exact phrase in text
   - `fuzzy_match(phrase, fuzziness)` - Fuzzy search with tolerance
   - `time_bounded_search(phrase, start_date, end_date)` - Search with date range filter

3. **Aggregations**
   - `section_aggregation()` - Count documents by section
   - `date_histogram_by_section(section)` - Time-based histogram for a section

4. **Advanced Operations**
   - `create_articles_index()` - Create a new index with explicit mapping
   - `add_index_alias()` - Add alias to an index
   - `generate_articles_data()` - Generate sample articles data
   - `delete_by_section(section)` - Delete documents by section
   - `update_add_text_length()` - Add calculated field to documents
   - `text_length_histogram()` - Histogram of text length values
   - `multi_index_date_histogram()` - Cross-index aggregation

## Kibana Queries

Once the application is running, navigate to Kibana Dev Tools (http://localhost:5601/app/dev_tools#/console) and execute the following queries:

### Basic Operations

1. **Insert one document into the news index**
   ```
   POST news/_doc/1
   {
     "title": "Custom News Article",
     "url": "https://example.com/news/custom-article",
     "text": "This is a custom news article created using Kibana Dev Tools.",
     "published_at": "2023-12-15T12:00:00",
     "section": "technology",
     "indexed_at": "2023-12-15T12:30:00",
     "author": "Kibana User"
   }
   ```

2. **Select data from the news index (basic search)**
   ```
   GET news/_search
   ```

3. **Select the number of documents in the index**
   ```
   GET news/_count
   ```

4. **Select 1000 documents from the news index**
   ```
   GET news/_search
   {
     "size": 1000
   }
   ```

### Search Operations

5. **Select documents with exact phrase match**
   ```
   GET news/_search
   {
     "query": {
       "match_phrase": {
         "text": "politics and economy"
       }
     }
   }
   ```

6. **Select documents with fuzzy match**
   ```
   GET news/_search
   {
     "query": {
       "match": {
         "text": {
           "query": "poltics",
           "fuzziness": "AUTO"
         }
       }
     }
   }
   ```

7. **Select documents with phrase and time period filter**
   ```
   GET news/_search
   {
     "query": {
       "bool": {
         "must": [
           {"match": {"text": "technology"}}
         ],
         "filter": [
           {
             "range": {
               "published_at": {
                 "gte": "now-6M",
                 "lte": "now"
               }
             }
           }
         ]
       }
     }
   }
   ```

### Aggregations

8. **Display news count by section (term aggregation)**
   ```
   GET news/_search
   {
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
   ```

9. **Display date histogram by published_at for a section**
   ```
   GET news/_search
   {
     "size": 0,
     "query": {
       "term": {
         "section": "politics"
       }
     },
     "aggs": {
       "articles_over_time": {
         "date_histogram": {
           "field": "published_at",
           "calendar_interval": "day"
         }
       }
     }
   }
   ```

### Advanced Operations

10. **Create a new articles index with explicit mapping**
    ```
    PUT articles
    {
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
                "type": "keyword",
                "ignore_above": 256
              }
            }
          },
          "journal": {
            "type": "keyword"
          },
          "citations": {
            "type": "integer"
          }
        }
      }
    }
    ```

11. **Add alias to index**
    ```
    POST /_aliases
    {
      "actions": [
        {
          "add": {
            "index": "articles",
            "alias": "scientific_publications"
          }
        }
      ]
    }
    ```

12. **Fill articles index with sample data**
    ```
    POST articles/_doc
    {
      "title": "Recent Advances in Natural Language Processing",
      "url": "https://doi.org/10.1234/abc123def",
      "text": "This paper discusses the recent development of transformer-based language models and their impact on various NLP tasks. We examine performance improvements across multiple benchmarks and discuss future research directions.",
      "published_at": "2023-06-15T09:30:00",
      "section": "computer_science",
      "indexed_at": "2023-06-16T14:20:00",
      "author": "Jane Smith, John Doe, et al.",
      "journal": "Journal of Data Science",
      "citations": 42
    }
    ```
    
    You can verify index has documents with:
    ```
    GET articles/_count
    ```

13. **Delete all documents by section**
    ```
    POST news/_delete_by_query
    {
      "query": {
        "term": {
          "section": "health"
        }
      }
    }
    ```

14. **Update all documents to add text_length field**
    ```
    POST news/_update_by_query?wait_for_completion=false&timeout=10m
    {
      "script": {
        "source": "ctx._source.text_length = ctx._source.text.length()",
        "lang": "painless"
      }
    }
    ```
    
    This will return a task ID that you can monitor with:
    ```
    GET _tasks/<task_id>
    ```

15. **Output histogram of text sizes**
    ```
    GET news/_search
    {
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
    ```

16. **Multi-index date histogram aggregation**
    ```
    GET news,articles/_search
    {
      "size": 0,
      "aggs": {
        "indexing_over_time": {
          "date_histogram": {
            "field": "indexed_at",
            "calendar_interval": "day"
          }
        }
      }
    }
    ```

## Troubleshooting

### Kibana Service Account Issues

If you encounter issues with Kibana not being able to connect to Elasticsearch, make sure:

1. The `KIBANA_TOKEN` in your `.env` file is correctly set
2. The token is valid and not expired
3. The Elasticsearch service is running and healthy