from sqlalchemy import text, inspect
from typing import Dict, List, Any
import pandas as pd
from ..core.database import engine

class DatabaseAnalyzer:
    def __init__(self):
        self.inspector = inspect(engine)

    def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """Get statistics for a specific table"""
        stats = {}
        
        # Get row count
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            stats['row_count'] = result.scalar()
            
            # Get table size
            result = conn.execute(text(f"""
                SELECT pg_size_pretty(pg_total_relation_size('{table_name}')) as size
            """))
            stats['table_size'] = result.scalar()
            
            # Get column statistics
            stats['columns'] = self._get_column_statistics(table_name)
            
            # Get index information
            stats['indexes'] = self._get_index_information(table_name)
            
        return stats

    def _get_column_statistics(self, table_name: str) -> Dict[str, Any]:
        """Get statistics for each column in the table"""
        columns = {}
        for column in self.inspector.get_columns(table_name):
            col_name = column['name']
            columns[col_name] = {
                'type': str(column['type']),
                'nullable': column['nullable'],
                'default': str(column['default']) if column['default'] else None
            }
            
            # Get distinct values count
            with engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT COUNT(DISTINCT {col_name}) 
                    FROM {table_name}
                """))
                columns[col_name]['distinct_values'] = result.scalar()
                
        return columns

    def _get_index_information(self, table_name: str) -> List[Dict[str, Any]]:
        """Get information about indexes on the table"""
        indexes = []
        for index in self.inspector.get_indexes(table_name):
            indexes.append({
                'name': index['name'],
                'columns': index['column_names'],
                'unique': index['unique']
            })
        return indexes

    def analyze_table_for_partitioning(self, table_name: str) -> Dict[str, Any]:
        """Analyze if a table would benefit from partitioning"""
        stats = self.get_table_statistics(table_name)
        analysis = {
            'recommended': False,
            'reason': '',
            'suggested_partition_key': None,
            'estimated_benefit': 'low'
        }
        
        # Check if table is large enough for partitioning
        if stats['row_count'] > 1000000:  # 1 million rows
            analysis['recommended'] = True
            analysis['reason'] = 'Table has more than 1 million rows'
            
            # Look for potential partition keys
            for col_name, col_stats in stats['columns'].items():
                if col_stats['distinct_values'] > 10 and col_stats['distinct_values'] < 1000:
                    analysis['suggested_partition_key'] = col_name
                    analysis['estimated_benefit'] = 'high'
                    break
        
        return analysis

    def get_table_usage_statistics(self, table_name: str) -> Dict[str, Any]:
        """Get usage statistics for a table from PostgreSQL system tables"""
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT 
                    schemaname,
                    relname,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch,
                    n_live_tup,
                    n_dead_tup
                FROM pg_stat_user_tables
                WHERE relname = '{table_name}'
            """))
            row = result.fetchone()
            
            if row:
                return {
                    'sequential_scans': row[2],
                    'sequential_tuples_read': row[3],
                    'index_scans': row[4],
                    'index_tuples_fetched': row[5],
                    'live_tuples': row[6],
                    'dead_tuples': row[7]
                }
            return {} 
