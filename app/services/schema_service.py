from typing import Dict, List, Any, Optional
from sqlalchemy import text, inspect, MetaData
from sqlalchemy.exc import SQLAlchemyError
import json
import time
import traceback
import logging
from ..core.database import engine
from ..core.config import get_settings

# Setup logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler() if settings.LOG_TO_CONSOLE else logging.NullHandler(),
        logging.FileHandler('app.log') if settings.LOG_TO_FILE else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

class SchemaService:
    def __init__(self):
        self.inspector = inspect(engine)
        self.metadata = MetaData()
        self._schema_cache = None
        self._cache_timestamp = None
        self._cache_duration = settings.CACHE_TTL  # Use config TTL
        logger.info("SchemaService initialized with debug mode: %s", settings.DEBUG)

    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid."""
        if self._schema_cache is None or self._cache_timestamp is None:
            return False
        return (time.time() - self._cache_timestamp) < self._cache_duration

    def get_database_context(self) -> Dict[str, Any]:
        """Get comprehensive database context for LLM prompts."""
        logger.debug("Getting database context...")
        start_time = time.time()
        
        if self._is_cache_valid():
            logger.debug("Using cached database context")
            return self._schema_cache or {}

        try:
            logger.info("Cache miss, building database context...")
            context = {
                "tables": self._get_all_tables_info(),
                "relationships": self._get_table_relationships(),
                "sample_data": self._get_sample_data(),
                "constraints": self._get_constraints_info(),
                "statistics": self._get_database_statistics()
            }
            
            self._schema_cache = context
            self._cache_timestamp = time.time()
            
            duration = time.time() - start_time
            logger.info("Database context built successfully in %.3f seconds", duration)
            return context
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Failed to get database context after %.3f seconds: %s", duration, str(e))
            logger.error("Stack trace: %s", traceback.format_exc())
            return {"error": f"Failed to get database context: {str(e)}"}

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information for a specific table."""
        logger.debug("Getting table info for: %s", table_name)
        try:
            table_info = {
                "columns": self._get_table_columns(table_name),
                "indexes": self._get_table_indexes(table_name),
                "primary_keys": self.inspector.get_pk_constraint(table_name)["constrained_columns"],
                "foreign_keys": self._get_foreign_keys(table_name),
                "row_count": self._get_table_row_count(table_name),
                "description": self._get_table_description(table_name)
            }
            return table_info
        except Exception as e:
            logger.error("Failed to get table info for %s: %s", table_name, str(e))
            logger.error("Stack trace: %s", traceback.format_exc())
            return {"error": f"Failed to get table info: {str(e)}"}

    def refresh_cache(self, cache_type: str = "all") -> Dict[str, Any]:
        """Refresh the cache."""
        logger.info("Refreshing cache: %s", cache_type)
        try:
            if cache_type == "all":
                self._schema_cache = None
                self._cache_timestamp = None
                return {"message": "All caches refreshed"}
            else:
                return {"error": f"Unknown cache type: {cache_type}"}
        except Exception as e:
            logger.error("Failed to refresh cache: %s", str(e))
            return {"error": f"Failed to refresh cache: {str(e)}"}

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        logger.debug("Getting cache stats")
        try:
            stats = {
                "cache_enabled": True,
                "cache_type": "memory",
                "cache_valid": self._is_cache_valid(),
                "cache_age": time.time() - self._cache_timestamp if self._cache_timestamp else None,
                "cache_duration": self._cache_duration,
                "has_cached_data": self._schema_cache is not None
            }
            return stats
        except Exception as e:
            logger.error("Failed to get cache stats: %s", str(e))
            return {"error": f"Failed to get cache stats: {str(e)}"}

    def _get_all_tables_info(self) -> Dict[str, Any]:
        """Get information for all tables."""
        logger.debug("Getting all tables info")
        try:
            tables = {}
            for table_name in self.inspector.get_table_names():
                logger.debug("Processing table: %s", table_name)
                tables[table_name] = {
                    "columns": self._get_table_columns(table_name),
                    "indexes": self._get_table_indexes(table_name),
                    "primary_keys": self.inspector.get_pk_constraint(table_name)["constrained_columns"],
                    "foreign_keys": self._get_foreign_keys(table_name),
                    "row_count": self._get_table_row_count(table_name),
                    "description": self._get_table_description(table_name)
                }
            return tables
        except Exception as e:
            logger.error("Failed to get all tables info: %s", str(e))
            logger.error("Stack trace: %s", traceback.format_exc())
            return {}

    def _get_table_columns(self, table_name: str) -> Dict[str, Dict[str, Any]]:
        """Get column information for a table."""
        try:
            columns = {}
            for column in self.inspector.get_columns(table_name):
                columns[column['name']] = {
                    "type": str(column['type']),
                    "nullable": column['nullable'],
                    "default": column['default'],
                    "primary_key": column.get('primary_key', False)
                }
            return columns
        except Exception as e:
            logger.error("Failed to get columns for table %s: %s", table_name, str(e))
            return {}

    def _get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get index information for a table."""
        try:
            indexes = []
            for index in self.inspector.get_indexes(table_name):
                indexes.append({
                    "name": index['name'],
                    "columns": index['column_names'],
                    "unique": index['unique']
                })
            return indexes
        except Exception as e:
            logger.error("Failed to get indexes for table %s: %s", table_name, str(e))
            return []

    def _get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key information for a table."""
        try:
            foreign_keys = []
            for fk in self.inspector.get_foreign_keys(table_name):
                foreign_keys.append({
                    "constrained_columns": fk['constrained_columns'],
                    "referred_table": fk['referred_table'],
                    "referred_columns": fk['referred_columns']
                })
            return foreign_keys
        except Exception as e:
            logger.error("Failed to get foreign keys for table %s: %s", table_name, str(e))
            return []

    def _get_table_row_count(self, table_name: str) -> int:
        """Get the row count for a table."""
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                return int(count) if count is not None else 0
        except Exception as e:
            logger.error("Failed to get row count for table %s: %s", table_name, str(e))
            return 0

    def _get_table_description(self, table_name: str) -> str:
        """Get a description for a table."""
        # This could be enhanced with actual table comments from the database
        return f"Table containing {table_name} data"

    def _get_table_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get relationships between tables."""
        logger.debug("Getting table relationships")
        try:
            relationships = {}
            for table_name in self.inspector.get_table_names():
                relationships[table_name] = []
                
                # Get foreign keys (outgoing relationships)
                for fk in self.inspector.get_foreign_keys(table_name):
                    relationships[table_name].append({
                        "type": "references",
                        "table": fk['referred_table'],
                        "columns": fk['constrained_columns'],
                        "referred_columns": fk['referred_columns']
                    })
                
                # Get referenced by (incoming relationships)
                for other_table in self.inspector.get_table_names():
                    if other_table != table_name:
                        for fk in self.inspector.get_foreign_keys(other_table):
                            if fk['referred_table'] == table_name:
                                relationships[table_name].append({
                                    "type": "referenced_by",
                                    "table": other_table,
                                    "columns": fk['constrained_columns'],
                                    "referred_columns": fk['referred_columns']
                                })
            
            return relationships
        except Exception as e:
            logger.error("Failed to get table relationships: %s", str(e))
            logger.error("Stack trace: %s", traceback.format_exc())
            return {}

    def _get_sample_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get sample data from tables."""
        logger.debug("Getting sample data")
        try:
            sample_data = {}
            for table_name in self.inspector.get_table_names():
                try:
                    with engine.connect() as conn:
                        result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 3"))
                        columns = result.keys()
                        rows = [dict(zip(columns, row)) for row in result.fetchall()]
                        sample_data[table_name] = rows
                except Exception as e:
                    logger.warning("Failed to get sample data for table %s: %s", table_name, str(e))
                    sample_data[table_name] = []
            return sample_data
        except Exception as e:
            logger.error("Failed to get sample data: %s", str(e))
            return {}

    def _get_constraints_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get constraint information."""
        logger.debug("Getting constraints info")
        try:
            constraints = {}
            for table_name in self.inspector.get_table_names():
                constraints[table_name] = []
                
                # Primary key constraints
                pk_constraint = self.inspector.get_pk_constraint(table_name)
                if pk_constraint['constrained_columns']:
                    constraints[table_name].append({
                        "type": "primary_key",
                        "columns": pk_constraint['constrained_columns']
                    })
                
                # Foreign key constraints
                for fk in self.inspector.get_foreign_keys(table_name):
                    constraints[table_name].append({
                        "type": "foreign_key",
                        "columns": fk['constrained_columns'],
                        "referred_table": fk['referred_table'],
                        "referred_columns": fk['referred_columns']
                    })
            
            return constraints
        except Exception as e:
            logger.error("Failed to get constraints info: %s", str(e))
            return {}

    def _get_database_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        logger.debug("Getting database statistics")
        try:
            stats = {
                "total_tables": len(self.inspector.get_table_names()),
                "total_columns": 0,
                "total_indexes": 0,
                "total_foreign_keys": 0
            }
            
            for table_name in self.inspector.get_table_names():
                stats["total_columns"] += len(self.inspector.get_columns(table_name))
                stats["total_indexes"] += len(self.inspector.get_indexes(table_name))
                stats["total_foreign_keys"] += len(self.inspector.get_foreign_keys(table_name))
            
            return stats
        except Exception as e:
            logger.error("Failed to get database statistics: %s", str(e))
            return {}

    def get_schema_summary(self) -> str:
        """Get a human-readable summary of the database schema."""
        context = self.get_database_context()
        
        if "error" in context:
            return f"Error: {context['error']}"
        
        summary = "Database Schema Summary:\n\n"
        
        for table_name, table_info in context["tables"].items():
            summary += f"Table: {table_name}\n"
            summary += f"  Rows: {table_info['row_count']:,}\n"
            summary += f"  Columns: {', '.join(table_info['columns'].keys())}\n"
            
            if table_info['primary_keys']:
                summary += f"  Primary Key: {', '.join(table_info['primary_keys'])}\n"
            
            if table_info['foreign_keys']:
                summary += f"  Foreign Keys: {len(table_info['foreign_keys'])}\n"
            
            summary += "\n"
        
        return summary 
