from typing import List
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import json
from ..core.database import engine
from ..models.schemas import OptimizationSuggestion
from .db_analyzer import DatabaseAnalyzer
from ..core.config import get_settings
import openai
from sqlglot import parse_one, exp

class QueryOptimizer:
    def __init__(self):
        self.db_analyzer = DatabaseAnalyzer()
        self.settings = get_settings()
        openai.api_key = self.settings.OPENAI_API_KEY

    def get_explain_plan(self, query: str) -> str:
        """Run EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) and return the plan as a JSON string."""
        try:
            from ..core.database import get_db_connection
            with get_db_connection() as conn:
                result = conn.execute(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"))
                row = result.fetchone()
                if row is None:
                    return json.dumps({"error": "No explain plan returned"})
                explain_json = row[0]
                if isinstance(explain_json, str):
                    return explain_json
                else:
                    return json.dumps(explain_json)
        except SQLAlchemyError as e:
            return json.dumps({"error": str(e)})

    def get_schema_stats(self, query: str) -> str:
        """Get comprehensive schema statistics for tables used in the query."""
        try:
            # Parse the query using sqlglot
            parsed = parse_one(query)
            
            # Extract tables and their aliases
            tables = {}
            for table in parsed.find_all(exp.Table):
                table_name = table.name
                alias = table.alias
                tables[table_name] = {
                    "alias": alias,
                    "is_joined": False,
                    "join_type": None,
                    "join_conditions": []
                }

            print(tables)
            
            # Extract JOIN information
            for join in parsed.find_all(exp.Join):
                table_name = join.this.name
                if table_name in tables:
                    tables[table_name]["is_joined"] = True
                    tables[table_name]["join_type"] = str(join.side) if hasattr(join, 'side') else "INNER"
                    # Extract join conditions
                    if join.on:
                        tables[table_name]["join_conditions"].append(str(join.on))
            
            print(tables)
            # Get statistics for each table
            stats = {}
            for table_name, table_info in tables.items():
                # Get table statistics
                table_stats = self.db_analyzer.get_table_statistics(table_name)
                
                # Get table usage statistics
                usage_stats = self.db_analyzer.get_table_usage_statistics(table_name)
                
                # Get partitioning analysis
                partition_analysis = self.db_analyzer.analyze_table_for_partitioning(table_name)
                
                # Get join-specific statistics
                join_stats = self._get_join_statistics(table_name, table_info["join_conditions"])
                
                stats[table_name] = {
                    "table_info": {
                        "alias": table_info["alias"],
                        "is_joined": table_info["is_joined"],
                        "join_type": table_info["join_type"],
                        "join_conditions": table_info["join_conditions"]
                    },
                    "table_stats": table_stats,
                    "usage_stats": usage_stats,
                    "partition_analysis": partition_analysis,
                    "join_stats": join_stats
                }
            
            return json.dumps(stats, indent=2)
        except Exception as e:
            return f"Error getting schema stats: {str(e)}"

    def _get_join_statistics(self, table_name: str, join_conditions: list) -> dict:
        """Get statistics specific to JOIN optimization."""
        try:
            from ..core.database import get_db_connection
            with get_db_connection() as conn:
                join_stats = {
                    "join_columns": {},
                    "join_selectivity": {},
                    "join_cardinality": {}
                }
                
                # For each join condition, get statistics about the join columns
                for condition in join_conditions:
                    # Extract column names from join condition (simple regex for now)
                    import re
                    columns = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)', condition)
                    
                    for col1, col2 in columns:
                        # Get statistics for join columns
                        for col in [col1, col2]:
                            if col not in join_stats["join_columns"]:
                                # Get column statistics
                                result = conn.execute(text(f"""
                                    SELECT 
                                        COUNT(DISTINCT {col}) as distinct_values,
                                        COUNT(*) FILTER (WHERE {col} IS NULL) as null_count,
                                        COUNT(*) as total_rows
                                    FROM {table_name}
                                """))
                                row = result.fetchone()
                                if row:
                                    join_stats["join_columns"][col] = {
                                        "distinct_values": row[0],
                                        "null_ratio": row[1] / row[2] if row[2] > 0 else 0,
                                        "total_rows": row[2]
                                    }
                
                return join_stats
        except Exception as e:
            return {"error": str(e)}

    def call_llm_for_optimization(self, sql_query: str, explain_json: str, schema_stats: str) -> dict:
        prompt = f"""
You are a PostgreSQL database optimization expert. Given the following information, provide actionable suggestions to optimize the SQL query. For each suggestion, specify the type (query_rewrite, index, view, partition, sharding), a description, and, if possible, a rewritten query or DDL statement.

SQL Query:
{sql_query}

EXPLAIN ANALYZE Output (JSON):
{explain_json}

Table Schema and Statistics:
{schema_stats}

Return your response as a JSON object with the following structure:
{{
  "query_optimization_suggestions": {{
    "query": "<rewritten_optimized_query_if_any>",
    "reason": "<explanation_of_why_this_optimization_helps>"
  }},
  "index_suggestions": [
    {{
      "query": "CREATE INDEX ...",
      "reason": "<explanation_of_why_this_index_would_help>"
    }},
    ...
  ],
  "view_suggestions": [
    {{
      "query": "CREATE MATERIALIZED VIEW ...",
      "reason": "<explanation_of_why_this_view_would_help>"
    }},
    ...
  ],
  "partitioning_strategy": {{
    "strategy": "<partitioning_recommendation>",
    "reason": "<explanation_of_why_partitioning_would_help>"
  }},
  "sharding_strategy": {{
    "strategy": "<sharding_recommendation>",
    "reason": "<explanation_of_why_sharding_would_help>"
  }},
  "other_suggestions": [
    {{
      "suggestion": "...",
      "reason": "<explanation_of_why_this_suggestion_helps>"
    }},
    ...
  ]
}}
"""
        client = openai.OpenAI(api_key=self.settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=self.settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1200
        )
        content = response.choices[0].message.content
        if content is None:
            return {"error": "Empty response from OpenAI"}
        try:
            return json.loads(content)
        except Exception:
            # Try to extract JSON from the response if LLM adds extra text
            import re
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                return json.loads(match.group(0))
            return {"error": "Failed to parse LLM response", "raw": content}

    def optimize(self, query: str) -> dict:
        explain_json = self.get_explain_plan(query)
        schema_stats = self.get_schema_stats(query)
        llm_response = self.call_llm_for_optimization(query, explain_json, schema_stats)
        return llm_response
