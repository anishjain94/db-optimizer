from typing import List
from ..models.schemas import QueryAnalysis, OptimizationSuggestion
from .db_analyzer import DatabaseAnalyzer

class QueryOptimizer:
    def __init__(self):
        self.db_analyzer = DatabaseAnalyzer()

    def optimize(self, query_analysis: QueryAnalysis) -> List[OptimizationSuggestion]:
        suggestions = []
        # Query rewrite suggestions
        suggestions += self.suggest_query_rewrite(query_analysis)
        # Index suggestions
        suggestions += self.suggest_indexes(query_analysis)
        # View suggestions
        suggestions += self.suggest_views(query_analysis)
        # Partitioning suggestions
        suggestions += self.suggest_partitioning(query_analysis)
        # Sharding suggestions
        suggestions += self.suggest_sharding(query_analysis)
        return suggestions

    def suggest_query_rewrite(self, query_analysis: QueryAnalysis) -> List[OptimizationSuggestion]:
        suggestions = []
        # Example: Suggest adding WHERE clause if missing
        if query_analysis.query_complexity != "simple" and not any(
            col for cols in query_analysis.columns_accessed.values() for col in cols if col.lower() == 'id'):
            suggestions.append(OptimizationSuggestion(
                type="query_rewrite",
                description="Consider adding more selective WHERE clauses to reduce scanned rows.",
                impact="high",
                implementation_steps=["Add WHERE clauses to filter data as early as possible."],
                estimated_improvement="Can significantly reduce query execution time."
            ))
        # TODO: Add more sophisticated rewrite suggestions
        return suggestions

    def suggest_indexes(self, query_analysis: QueryAnalysis) -> List[OptimizationSuggestion]:
        suggestions = []
        for table, columns in query_analysis.columns_accessed.items():
            if table == "unknown":
                continue
            stats = self.db_analyzer.get_table_statistics(table)
            indexed_columns = {col for idx in stats.get('indexes', []) for col in idx['columns']}
            for col in columns:
                if col not in indexed_columns:
                    suggestions.append(OptimizationSuggestion(
                        type="index",
                        description=f"Consider creating an index on {table}({col}) for faster lookups.",
                        impact="medium",
                        implementation_steps=[f"CREATE INDEX idx_{table}_{col} ON {table}({col});"],
                        estimated_improvement="Improves query performance for lookups and joins."
                    ))
        return suggestions

    def suggest_views(self, query_analysis: QueryAnalysis) -> List[OptimizationSuggestion]:
        suggestions = []
        # Example: Suggest a view for complex queries
        if query_analysis.query_complexity == "complex":
            suggestions.append(OptimizationSuggestion(
                type="view",
                description="Consider creating a materialized view for this complex query.",
                impact="medium",
                implementation_steps=["CREATE MATERIALIZED VIEW ... AS <your query>"],
                estimated_improvement="Reduces computation for repetitive complex queries."
            ))
        return suggestions

    def suggest_partitioning(self, query_analysis: QueryAnalysis) -> List[OptimizationSuggestion]:
        suggestions = []
        for table in query_analysis.tables_used:
            partition_analysis = self.db_analyzer.analyze_table_for_partitioning(table)
            if partition_analysis['recommended']:
                suggestions.append(OptimizationSuggestion(
                    type="partition",
                    description=f"Table {table} is large. Consider partitioning by {partition_analysis['suggested_partition_key']}.",
                    impact="high",
                    implementation_steps=[f"ALTER TABLE {table} PARTITION BY RANGE ({partition_analysis['suggested_partition_key']});"],
                    estimated_improvement="Improves query performance and manageability for large tables."
                ))
        return suggestions

    def suggest_sharding(self, query_analysis: QueryAnalysis) -> List[OptimizationSuggestion]:
        suggestions = []
        # Example: Suggest sharding for very large tables
        for table in query_analysis.tables_used:
            stats = self.db_analyzer.get_table_statistics(table)
            if stats.get('row_count', 0) > 10000000:  # 10 million rows
                suggestions.append(OptimizationSuggestion(
                    type="sharding",
                    description=f"Table {table} is extremely large. Consider sharding across multiple servers.",
                    impact="high",
                    implementation_steps=["Implement sharding logic in your application or use a sharding extension."],
                    estimated_improvement="Improves scalability and performance for massive datasets."
                ))
        return suggestions 
