# Natural Language to SQL Query Feature

This feature allows users to query the database using natural language instead of writing SQL queries. The system uses AI to understand the intent and convert natural language to SQL, then executes the query and returns results.

## Features

### 🎯 Core Functionality
- **Natural Language Processing**: Convert human-readable queries to SQL
- **Database Context Awareness**: Uses actual database schema and sample data
- **Query Validation**: Ensures generated SQL is safe and syntactically correct
- **Confidence Scoring**: Provides confidence levels for generated queries
- **Schema Exploration**: Browse database structure and relationships

### 🔒 Safety Features
- **Read-Only Operations**: Only SELECT queries are allowed
- **Dangerous Operation Detection**: Blocks DELETE, DROP, UPDATE, etc.
- **Schema Validation**: Ensures tables and columns exist
- **Syntax Validation**: Validates SQL before execution

### 📊 Enhanced Capabilities
- **Relationship Mapping**: Understands foreign key relationships
- **Sample Data Analysis**: Uses actual data patterns for better understanding
- **Index Awareness**: Considers existing indexes for optimization
- **Caching**: Schema information is cached for performance

## API Endpoints

### 1. Natural Language Query Processing
```http
POST /natural-query
Content-Type: application/json

{
  "query": "how many users were registered after 20th april"
}
```

**Response:**
```json
{
  "natural_query": "how many users were registered after 20th april",
  "generated_sql": "SELECT COUNT(*) FROM users WHERE registration_date > '2024-04-20'",
  "tables_used": ["users"],
  "confidence": "high",
  "results": [{"count": 150}],
  "row_count": 1,
  "columns": ["count"],
  "error": null
}
```

### 2. SQL Generation Only
```http
POST /generate-sql
Content-Type: application/json

{
  "query": "show me all orders from last month"
}
```

**Response:**
```json
{
  "sql_query": "SELECT * FROM orders WHERE order_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')",
  "natural_query": "show me all orders from last month",
  "tables_used": ["orders"],
  "confidence": "medium",
  "error": null
}
```

### 3. Database Schema Information
```http
GET /schema
```

**Response:**
```json
{
  "tables": {
    "users": {
      "columns": {
        "id": {"type": "INTEGER", "nullable": false, "sample_values": [1, 2, 3]},
        "name": {"type": "VARCHAR", "nullable": false, "sample_values": ["John", "Jane"]},
        "registration_date": {"type": "DATE", "nullable": false, "sample_values": ["2024-01-01"]}
      },
      "primary_keys": ["id"],
      "foreign_keys": [],
      "row_count": 1000
    }
  },
  "relationships": {
    "users": [
      {
        "type": "referenced_by",
        "table": "orders",
        "columns": ["user_id"],
        "referred_columns": ["id"]
      }
    ]
  },
  "sample_data": {
    "users": [
      {"id": 1, "name": "John Doe", "registration_date": "2024-01-01"}
    ]
  }
}
```

### 4. Schema Summary
```http
GET /schema/summary
```

**Response:**
```json
{
  "summary": "Database Schema Summary:\n\nTable: users\n  Rows: 1,000\n  Columns: id (INTEGER) [PK], name (VARCHAR), registration_date (DATE)\n  Foreign Keys: 0\n\nTable: orders\n  Rows: 5,000\n  Columns: id (INTEGER) [PK], user_id (INTEGER) [FK], order_date (DATE)\n  Foreign Keys: 1\n  Relationships: → users(id)"
}
```

## Technical Implementation

### Architecture Overview

```
Natural Language Query
         ↓
   Schema Service
   (Database Context)
         ↓
   Query Generator
   (AI + Validation)
         ↓
   SQL Execution
         ↓
   Results + Metadata
```

### Key Components

#### 1. SchemaService (`app/services/schema_service.py`)
- **Database Context Extraction**: Gathers table schemas, relationships, and sample data
- **Caching**: Implements intelligent caching to avoid repeated schema queries
- **Relationship Mapping**: Identifies foreign key relationships between tables
- **Sample Data Collection**: Gathers representative data for better AI understanding

#### 2. Enhanced QueryGenerator (`app/services/query_generator.py`)
- **Contextual Prompting**: Creates rich prompts with database schema information
- **Query Validation**: Ensures generated SQL is safe and syntactically correct
- **Confidence Estimation**: Provides confidence levels based on query complexity
- **Error Handling**: Comprehensive error handling and suggestions

#### 3. API Layer (`app/api/optimizer_api.py`)
- **Multiple Endpoints**: Separate endpoints for different use cases
- **Error Handling**: Proper HTTP status codes and error messages
- **Response Formatting**: Consistent JSON response structure

### Database Context Features

#### Schema Information
- Table names and descriptions
- Column names, types, and constraints
- Primary and foreign key relationships
- Index information
- Sample data from each table

#### Relationship Mapping
- Foreign key constraints
- Referential integrity
- Join path suggestions
- Table dependency graphs

#### Sample Data Analysis
- Representative data values
- Data type patterns
- Null value ratios
- Distinct value counts

## Usage Examples

### Basic Query
```python
import requests

# Natural language query
response = requests.post("http://localhost:8000/natural-query", 
                        json={"query": "how many users were registered after 20th april"})

result = response.json()
print(f"Generated SQL: {result['generated_sql']}")
print(f"Results: {result['results']}")
```

### SQL Generation Only
```python
# Generate SQL without execution
response = requests.post("http://localhost:8000/generate-sql",
                        json={"query": "show me all orders from last month"})

result = response.json()
print(f"SQL: {result['sql_query']}")
print(f"Confidence: {result['confidence']}")
```

### Schema Exploration
```python
# Get database schema
response = requests.get("http://localhost:8000/schema")
schema = response.json()

# Get human-readable summary
response = requests.get("http://localhost:8000/schema/summary")
summary = response.json()
print(summary['summary'])
```

## Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:password@localhost/dbname

# Optional
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
```

### Dependencies
```txt
openai>=1.0.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
fastapi>=0.100.0
uvicorn>=0.20.0
requests>=2.28.0
```

## Testing

### Run the Test Script
```bash
python test_natural_query.py
```

### Manual Testing with curl
```bash
# Test natural language query
curl -X POST "http://localhost:8000/natural-query" \
     -H "Content-Type: application/json" \
     -d '{"query": "how many users were registered after 20th april"}'

# Get schema summary
curl "http://localhost:8000/schema/summary"
```

## Best Practices

### Query Formulation
- **Be Specific**: "users registered after April 20th" vs "users after date"
- **Use Clear Language**: "how many" for counts, "show me" for data retrieval
- **Include Context**: "orders from last month" vs "orders"

### Error Handling
- Check for `error` field in responses
- Handle confidence levels appropriately
- Validate generated SQL before execution
- Provide fallback options for low-confidence queries

### Performance Considerations
- Schema cache expires after 5 minutes
- Large databases may need longer processing times
- Consider query complexity limits
- Monitor API response times

## Limitations and Future Enhancements

### Current Limitations
- Only supports SELECT queries
- Requires OpenAI API access
- Limited to PostgreSQL databases
- No support for complex aggregations
- Schema cache may be stale for rapidly changing databases

### Future Enhancements
- **Multi-Database Support**: MySQL, SQLite, etc.
- **Complex Queries**: INSERT, UPDATE with validation
- **Query Templates**: Pre-defined query patterns
- **Learning System**: Improve based on user feedback
- **Offline Mode**: Local LLM integration
- **Query History**: Track and analyze query patterns
- **Performance Optimization**: Query result caching
- **Advanced Analytics**: Query complexity analysis

## Troubleshooting

### Common Issues

#### 1. "Failed to get database context"
- Check database connection
- Verify database permissions
- Ensure tables exist in the database

#### 2. "Generated SQL validation failed"
- Review the natural language query
- Check if referenced tables/columns exist
- Verify date formats and data types

#### 3. "OpenAI API error"
- Verify API key is correct
- Check API quota and limits
- Ensure internet connectivity

#### 4. "Schema cache issues"
- Restart the application
- Check database connectivity
- Verify schema permissions

### Debug Mode
Enable debug mode to get detailed error information:
```bash
export API_DEBUG=true
python -m app.main
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
