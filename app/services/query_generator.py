from typing import Dict, Any, Optional, List
import openai
import re
import time
import traceback
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from ..core.config import get_settings
from ..core.database import engine
from .schema_service import SchemaService

# Setup logging
settings = get_settings()
logger = logging.getLogger(__name__)

class QueryGenerator:
    def __init__(self):
        self.settings = get_settings()
        openai.api_key = self.settings.OPENAI_API_KEY
        self.schema_service = SchemaService()
        logger.info("QueryGenerator initialized with debug mode: %s", settings.DEBUG)

    def generate_sql(self, natural_query: str) -> Dict[str, Any]:
        """Convert natural language query to SQL using OpenAI with database context."""
        logger.info("Generating SQL for query: %s", natural_query[:100] + "..." if len(natural_query) > 100 else natural_query)
        start_time = time.time()
        
        try:
            # Get database context
            logger.debug("Getting database context...")
            db_context = self.schema_service.get_database_context()
            
            if "error" in db_context:
                logger.error("Failed to get database context: %s", db_context["error"])
                return {"error": f"Failed to get database context: {db_context['error']}"}

            # Create enhanced prompt with database context
            logger.debug("Creating contextual prompt...")
            prompt = self._create_contextual_prompt(natural_query, db_context)
            
            # Generate SQL using OpenAI
            logger.debug("Calling OpenAI API...")
            client = openai.OpenAI(api_key=self.settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            sql_query = response.choices[0].message.content
            if sql_query is None:
                logger.error("Empty response from OpenAI")
                return {"error": "Empty response from OpenAI"}
            
            sql_query = sql_query.strip()
            logger.info("Generated SQL: %s", sql_query)
            
            # Clean up the SQL query
            logger.debug("Cleaning SQL query...")
            sql_query = self._clean_sql_query(sql_query)
            
            # Validate the generated SQL
            logger.debug("Validating SQL query...")
            validation_result = self._validate_sql_query(sql_query, db_context)
            
            if not validation_result["is_valid"]:
                logger.error("SQL validation failed: %s", validation_result["error"])
                return {
                    "error": f"Generated SQL validation failed: {validation_result['error']}",
                    "generated_sql": sql_query,
                    "suggestions": validation_result.get("suggestions", [])
                }
            
            result = {
                "sql_query": sql_query,
                "natural_query": natural_query,
                "tables_used": self._extract_tables_from_sql(sql_query),
                "confidence": self._estimate_confidence(sql_query, natural_query)
            }
            
            duration = time.time() - start_time
            logger.info("SQL generation completed successfully in %.3f seconds", duration)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error("SQL generation failed after %.3f seconds: %s", duration, str(e))
            logger.error("Stack trace: %s", traceback.format_exc())
            return {"error": f"SQL generation failed: {str(e)}"}

    def _create_contextual_prompt(self, natural_query: str, db_context: Dict[str, Any]) -> str:
        """Create a comprehensive prompt with database context."""
        logger.debug("Creating contextual prompt...")
        try:
            # Create schema summary
            schema_summary = self._create_schema_summary(db_context)
            
            # Create sample data summary
            sample_data_summary = self._create_sample_data_summary(db_context)
            
            prompt = f"""
You are an expert SQL developer with deep knowledge of PostgreSQL. Your task is to convert natural language queries to accurate SQL statements.

DATABASE SCHEMA:
{schema_summary}

SAMPLE DATA:
{sample_data_summary}

NATURAL LANGUAGE QUERY:
"{natural_query}"

INSTRUCTIONS:
1. Analyze the natural language query carefully
2. Identify the relevant tables and columns from the schema
3. Generate a PostgreSQL SQL query that accurately answers the question
4. Use appropriate JOINs when multiple tables are needed
5. Apply proper WHERE conditions based on the query intent
6. Use appropriate aggregate functions (COUNT, SUM, AVG, etc.) when needed
7. Ensure the query is safe and only performs SELECT operations
8. Return ONLY the SQL query without any explanation or markdown formatting

IMPORTANT RULES:
- Only use tables and columns that exist in the schema
- Use proper table aliases when joining multiple tables
- Handle date comparisons properly (use DATE() function for date-only comparisons)
- Use appropriate data types for comparisons
- Avoid any destructive operations (DELETE, DROP, etc.)
- If the query is ambiguous, make reasonable assumptions and add comments

SQL QUERY:
"""
            logger.debug("Contextual prompt created successfully")
            return prompt
            
        except Exception as e:
            logger.error("Failed to create contextual prompt: %s", str(e))
            logger.error("Stack trace: %s", traceback.format_exc())
            raise

    def _create_schema_summary(self, db_context: Dict[str, Any]) -> str:
        """Create a concise schema summary for the prompt."""
        logger.debug("Creating schema summary...")
        try:
            summary = []
            
            for table_name, table_info in db_context["tables"].items():
                table_summary = f"Table: {table_name}"
                if table_info.get("description"):
                    table_summary += f" ({table_info['description']})"
                
                # Add columns with types
                columns = []
                for col_name, col_info in table_info["columns"].items():
                    col_type = col_info["type"]
                    if col_name in table_info.get("primary_keys", []):
                        columns.append(f"{col_name} ({col_type}) [PK]")
                    elif col_name in [fk["constrained_columns"][0] for fk in table_info.get("foreign_keys", [])]:
                        columns.append(f"{col_name} ({col_type}) [FK]")
                    else:
                        columns.append(f"{col_name} ({col_type})")
                
                table_summary += f"\n  Columns: {', '.join(columns)}"
                
                # Add relationships
                relationships = db_context["relationships"].get(table_name, [])
                if relationships:
                    rel_summary = []
                    for rel in relationships:
                        if rel["type"] == "references":
                            rel_summary.append(f"→ {rel['table']}({','.join(rel['referred_columns'])})")
                        elif rel["type"] == "referenced_by":
                            rel_summary.append(f"← {rel['table']}({','.join(rel['columns'])})")
                    if rel_summary:
                        table_summary += f"\n  Relationships: {' '.join(rel_summary)}"
                
                summary.append(table_summary)
            
            result = "\n\n".join(summary)
            logger.debug("Schema summary created successfully")
            return result
            
        except Exception as e:
            logger.error("Failed to create schema summary: %s", str(e))
            return "Error creating schema summary"

    def _create_sample_data_summary(self, db_context: Dict[str, Any]) -> str:
        """Create a sample data summary for the prompt."""
        logger.debug("Creating sample data summary...")
        try:
            summary = []
            
            for table_name, sample_data in db_context.get("sample_data", {}).items():
                if sample_data:
                    summary.append(f"Sample data from {table_name}:")
                    for i, row in enumerate(sample_data[:2]):  # Limit to 2 rows
                        summary.append(f"  Row {i+1}: {row}")
                    summary.append("")
            
            result = "\n".join(summary) if summary else "No sample data available"
            logger.debug("Sample data summary created successfully")
            return result
            
        except Exception as e:
            logger.error("Failed to create sample data summary: %s", str(e))
            return "Error creating sample data summary"

    def _clean_sql_query(self, sql_query: str) -> str:
        """Clean up the generated SQL query."""
        logger.debug("Cleaning SQL query...")
        try:
            # Remove markdown code blocks
            sql_query = re.sub(r'```sql\s*', '', sql_query)
            sql_query = re.sub(r'```\s*', '', sql_query)
            
            # Remove leading/trailing whitespace
            sql_query = sql_query.strip()
            
            # Remove semicolon at the end if present
            if sql_query.endswith(';'):
                sql_query = sql_query[:-1]
            
            logger.debug("SQL query cleaned successfully")
            return sql_query
            
        except Exception as e:
            logger.error("Failed to clean SQL query: %s", str(e))
            return sql_query

    def _validate_sql_query(self, sql_query: str, db_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated SQL query."""
        logger.debug("Validating SQL query...")
        try:
            validation = {
                "is_valid": True,
                "error": None,
                "suggestions": []
            }
            
            # Check if it's a SELECT query
            if not sql_query.upper().strip().startswith('SELECT'):
                validation["is_valid"] = False
                validation["error"] = "Only SELECT queries are allowed"
                return validation
            
            # Check for dangerous operations
            dangerous_keywords = ['DELETE', 'DROP', 'TRUNCATE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
            for keyword in dangerous_keywords:
                if keyword in sql_query.upper():
                    validation["is_valid"] = False
                    validation["error"] = f"Dangerous operation '{keyword}' detected"
                    return validation
            
            # Check if tables exist in schema
            tables_used = self._extract_tables_from_sql(sql_query)
            for table in tables_used:
                if table not in db_context["tables"]:
                    validation["suggestions"].append(f"Table '{table}' not found in schema")
            
            # Try to parse the query (basic syntax check)
            try:
                with engine.connect() as conn:
                    # Use EXPLAIN to validate without executing
                    conn.execute(text(f"EXPLAIN {sql_query}"))
            except SQLAlchemyError as e:
                validation["is_valid"] = False
                validation["error"] = f"SQL syntax error: {str(e)}"
            
            logger.debug("SQL validation completed")
            return validation
            
        except Exception as e:
            logger.error("Failed to validate SQL query: %s", str(e))
            return {
                "is_valid": False,
                "error": f"Validation error: {str(e)}",
                "suggestions": []
            }

    def _extract_tables_from_sql(self, sql_query: str) -> List[str]:
        """Extract table names from SQL query."""
        logger.debug("Extracting tables from SQL...")
        try:
            # Simple regex to extract table names from FROM and JOIN clauses
            tables = set()
            
            # Extract from FROM clause
            from_matches = re.findall(r'FROM\s+(\w+)', sql_query, re.IGNORECASE)
            tables.update(from_matches)
            
            # Extract from JOIN clauses
            join_matches = re.findall(r'JOIN\s+(\w+)', sql_query, re.IGNORECASE)
            tables.update(join_matches)
            
            result = list(tables)
            logger.debug("Extracted tables: %s", result)
            return result
            
        except Exception as e:
            logger.error("Failed to extract tables from SQL: %s", str(e))
            return []

    def _estimate_confidence(self, sql_query: str, natural_query: str) -> str:
        """Estimate confidence level of the generated SQL."""
        logger.debug("Estimating confidence...")
        try:
            # Simple heuristic based on query complexity and keywords
            confidence = "medium"
            
            # Check for common patterns that indicate high confidence
            if any(keyword in natural_query.lower() for keyword in ['count', 'how many', 'total']):
                if 'COUNT(' in sql_query.upper():
                    confidence = "high"
            
            if any(keyword in natural_query.lower() for keyword in ['date', 'after', 'before', 'since']):
                if any(func in sql_query.upper() for func in ['DATE(', '>', '<', 'BETWEEN']):
                    confidence = "high"
            
            # Check for complex operations that might reduce confidence
            if 'JOIN' in sql_query.upper() and 'JOIN' not in natural_query.upper():
                confidence = "medium"
            
            logger.debug("Confidence estimated as: %s", confidence)
            return confidence
            
        except Exception as e:
            logger.error("Failed to estimate confidence: %s", str(e))
            return "medium"

    def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """Execute the SQL query and return results."""
        logger.info("Executing SQL query: %s", sql_query)
        start_time = time.time()
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text(sql_query))
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                
                response = {
                    "sql_query": sql_query,
                    "results": rows,
                    "row_count": len(rows),
                    "columns": list(columns)
                }
                
                duration = time.time() - start_time
                logger.info("Query executed successfully in %.3f seconds, returned %d rows", duration, len(rows))
                return response
                
        except SQLAlchemyError as e:
            duration = time.time() - start_time
            logger.error("SQL execution failed after %.3f seconds: %s", duration, str(e))
            return {
                "error": str(e),
                "sql_query": sql_query
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Query execution failed after %.3f seconds: %s", duration, str(e))
            logger.error("Stack trace: %s", traceback.format_exc())
            return {
                "error": f"Execution error: {str(e)}",
                "sql_query": sql_query
            }

    def process_natural_query(self, natural_query: str) -> Dict[str, Any]:
        """Complete pipeline: natural language → SQL → execution → results."""
        logger.info("Processing natural query: %s", natural_query[:100] + "..." if len(natural_query) > 100 else natural_query)
        start_time = time.time()
        
        try:
            # Generate SQL
            generation_result = self.generate_sql(natural_query)
            
            if "error" in generation_result and generation_result["error"] is not None:
                duration = time.time() - start_time
                logger.error("Natural query processing failed after %.3f seconds: %s", duration, generation_result["error"])
                return generation_result
            
            # Execute the generated SQL
            execution_result = self.execute_query(generation_result["sql_query"])
            
            # Combine results
            result = {
                "natural_query": natural_query,
                "generated_sql": generation_result["sql_query"],
                "tables_used": generation_result.get("tables_used", []),
                "confidence": generation_result.get("confidence", "medium"),
                "results": execution_result.get("results", []),
                "row_count": execution_result.get("row_count", 0),
                "columns": execution_result.get("columns", [])
            }
            
            # Only add error field if there's an actual error
            if "error" in execution_result and execution_result["error"] is not None:
                result["error"] = execution_result["error"]
            
            duration = time.time() - start_time
            logger.info("Natural query processing completed successfully in %.3f seconds", duration)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Natural query processing failed after %.3f seconds: %s", duration, str(e))
            logger.error("Stack trace: %s", traceback.format_exc())
            return {"error": f"Query processing failed: {str(e)}"} 
