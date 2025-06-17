import sqlglot
from sqlglot import exp
from typing import List, Dict, Set
from ..models.schemas import QueryAnalysis

class QueryAnalyzer:
    def __init__(self):
        self.supported_dialects = ["postgres"]

    def analyze_query(self, query: str) -> QueryAnalysis:
        try:
            # Parse the query
            parsed = sqlglot.parse_one(query, dialect="postgres")
            
            # Extract tables and columns
            tables_used = self._extract_tables(parsed)
            columns_accessed = self._extract_columns(parsed)
            
            # Analyze query complexity
            complexity = self._analyze_complexity(parsed)
            
            # Estimate query cost (simplified version)
            estimated_cost = self._estimate_query_cost(parsed)
            
            return QueryAnalysis(
                tables_used=list(tables_used),
                columns_accessed=columns_accessed,
                query_complexity=complexity,
                estimated_cost=estimated_cost
            )
        except Exception as e:
            raise ValueError(f"Failed to analyze query: {str(e)}")

    def _extract_tables(self, parsed: exp.Expression) -> Set[str]:
        tables = set()
        for table in parsed.find_all(exp.Table):
            tables.add(table.name)
        return tables

    def _extract_columns(self, parsed: exp.Expression) -> Dict[str, List[str]]:
        columns_by_table = {}
        for column in parsed.find_all(exp.Column):
            table_name = column.table if column.table else "unknown"
            if table_name not in columns_by_table:
                columns_by_table[table_name] = []
            columns_by_table[table_name].append(column.name)
        return columns_by_table

    def _analyze_complexity(self, parsed: exp.Expression) -> str:
        # Count the number of joins
        join_count = len(list(parsed.find_all(exp.Join)))
        
        # Count the number of subqueries
        subquery_count = len(list(parsed.find_all(exp.Subquery)))
        
        # Count the number of aggregations
        agg_count = len(list(parsed.find_all(exp.Agg)))
        
        total_complexity = join_count + subquery_count + agg_count
        
        if total_complexity <= 2:
            return "simple"
        elif total_complexity <= 5:
            return "moderate"
        else:
            return "complex"

# TODO: Implement a more accurate cost estimation, maybe use explain plan analysis.
    def _estimate_query_cost(self, parsed: exp.Expression) -> float:
        # This is a simplified cost estimation
        # In a real implementation, this would use database statistics
        base_cost = 1.0
        
        # Add cost for joins
        join_cost = len(list(parsed.find_all(exp.Join))) * 2.0
        
        # Add cost for subqueries
        subquery_cost = len(list(parsed.find_all(exp.Subquery))) * 3.0
        
        # Add cost for aggregations
        agg_cost = len(list(parsed.find_all(exp.Agg))) * 1.5
        
        return base_cost + join_cost + subquery_cost + agg_cost 
