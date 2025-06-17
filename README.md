# Database Query Optimizer AI Agent

An intelligent agent that analyzes SQL queries and provides optimization recommendations for database performance improvement.

## Features

- REST API endpoint for SQL query analysis
- Query structure analysis and parsing
- Database statistics collection
- Optimization recommendations including:
  - Query rewrite suggestions
  - Index recommendations
  - Partitioning strategies
  - View creation suggestions
  - Sharding recommendations

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your database configuration:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
```

4. Run the server:
```bash
uvicorn app.main:app --reload
```

## API Usage

Send a POST request to `/analyze` with the following JSON body:
```json
{
    "query": "SELECT * FROM users WHERE age > 25"
}
```

## Project Structure

```
.
├── app/
│   ├── main.py              # FastAPI application
│   │   ├── api/
│   │   │   └── routes.py        # API routes
│   │   ├── core/
│   │   │   ├── config.py        # Configuration
│   │   │   └── database.py      # Database connection
│   │   ├── services/
│   │   │   ├── query_analyzer.py    # SQL query analysis
│   │   │   ├── db_analyzer.py       # Database analysis
│   │   │   └── optimizer.py         # Optimization engine
│   │   └── models/
│   │       └── schemas.py       # Pydantic models
│   ├── requirements.txt
│   └── README.md
``` 
