from fastapi import APIRouter, HTTPException
import time
import traceback
import logging
from ..models.schemas import QueryRequest, NaturalQueryRequest
from ..services.optimizer import QueryOptimizer
from ..services.query_generator import QueryGenerator
from ..services.schema_service import SchemaService
from ..core.config import get_settings

# Setup logging
settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter()
optimizer = QueryOptimizer()
query_generator = QueryGenerator()
schema_service = SchemaService()

@router.post("/optimize-query")
def optimize_query(request: QueryRequest):
    start_time = time.time()
    logger.info("Optimize query request received: %s", request.query[:100] + "..." if len(request.query) > 100 else request.query)
    
    try:
        result = optimizer.optimize(request.query)
        duration = time.time() - start_time
        logger.info("Optimize query completed successfully in %.3f seconds", duration)
        return {"data": result}
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Optimize query failed after %.3f seconds: %s", duration, str(e))
        logger.error("Stack trace: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@router.post("/natural-query")
def process_natural_query(request: NaturalQueryRequest):
    start_time = time.time()
    logger.info("Natural query request received: %s", request.query[:100] + "..." if len(request.query) > 100 else request.query)
    
    try:
        # Use the enhanced query generator with database context
        result = query_generator.process_natural_query(request.query)
        
        # Check if there's an actual error (not None or empty string)
        if "error" in result and result["error"] is not None and str(result["error"]).strip():
            duration = time.time() - start_time
            logger.error("Natural query failed after %.3f seconds: %s", duration, result["error"])
            raise HTTPException(status_code=500, detail=result["error"])
        
        duration = time.time() - start_time
        logger.info("Natural query completed successfully in %.3f seconds", duration)
        return result
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Natural query failed after %.3f seconds: %s", duration, str(e))
        logger.error("Stack trace: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.get("/schema")
def get_database_schema():
    """Get the database schema information."""
    start_time = time.time()
    logger.info("Schema request received")
    
    try:
        context = schema_service.get_database_context()
        if "error" in context and context["error"] is not None and str(context["error"]).strip():
            duration = time.time() - start_time
            logger.error("Schema request failed after %.3f seconds: %s", duration, context["error"])
            raise HTTPException(status_code=500, detail=context["error"])
        
        duration = time.time() - start_time
        logger.info("Schema request completed successfully in %.3f seconds", duration)
        return context
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Schema request failed after %.3f seconds: %s", duration, str(e))
        logger.error("Stack trace: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {str(e)}")

@router.get("/schema/summary")
def get_schema_summary():
    """Get a summary of the database schema."""
    start_time = time.time()
    logger.info("Schema summary request received")
    
    try:
        summary = schema_service.get_schema_summary()
        duration = time.time() - start_time
        logger.info("Schema summary completed successfully in %.3f seconds", duration)
        return {"summary": summary}
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Schema summary failed after %.3f seconds: %s", duration, str(e))
        logger.error("Stack trace: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get schema summary: {str(e)}")

@router.post("/generate-sql")
def generate_sql_only(request: NaturalQueryRequest):
    """Generate SQL from natural language without executing it."""
    try:
        result = query_generator.generate_sql(request.query)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL generation failed: {str(e)}")

@router.post("/execute-sql")
def execute_sql_query(request: QueryRequest):
    """Execute a raw SQL query (for testing generated queries)."""
    try:
        result = query_generator.execute_query(request.query)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

@router.post("/execute-query")
def execute_query(request: QueryRequest):
    """Execute a SQL query and return results."""
    start_time = time.time()
    logger.info("Execute query request received: %s", request.query[:100] + "..." if len(request.query) > 100 else request.query)
    
    try:
        result = query_generator.execute_query(request.query)
        if "error" in result and result["error"] is not None and str(result["error"]).strip():
            duration = time.time() - start_time
            logger.error("Execute query failed after %.3f seconds: %s", duration, result["error"])
            raise HTTPException(status_code=500, detail=result["error"])
        
        duration = time.time() - start_time
        logger.info("Execute query completed successfully in %.3f seconds", duration)
        return result
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Execute query failed after %.3f seconds: %s", duration, str(e))
        logger.error("Stack trace: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

@router.get("/cache/stats")
def get_cache_statistics():
    """Get cache statistics and performance metrics."""
    start_time = time.time()
    logger.info("Cache stats request received")
    
    try:
        stats = schema_service.get_cache_stats()
        if "error" in stats and stats["error"] is not None and str(stats["error"]).strip():
            duration = time.time() - start_time
            logger.error("Cache stats failed after %.3f seconds: %s", duration, stats["error"])
            raise HTTPException(status_code=500, detail=stats["error"])
        
        duration = time.time() - start_time
        logger.info("Cache stats completed successfully in %.3f seconds", duration)
        return {
            "cache_statistics": stats,
            "message": "Cache statistics retrieved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Cache stats failed after %.3f seconds: %s", duration, str(e))
        logger.error("Stack trace: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.post("/cache/refresh")
def refresh_cache(cache_type: str = "all"):
    """Refresh specific cache types or all caches."""
    start_time = time.time()
    logger.info("Cache refresh request received: %s", cache_type)
    
    try:
        result = schema_service.refresh_cache(cache_type)
        if "error" in result and result["error"] is not None and str(result["error"]).strip():
            duration = time.time() - start_time
            logger.error("Cache refresh failed after %.3f seconds: %s", duration, result["error"])
            raise HTTPException(status_code=400, detail=result["error"])
        
        duration = time.time() - start_time
        logger.info("Cache refresh completed successfully in %.3f seconds", duration)
        return result
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Cache refresh failed after %.3f seconds: %s", duration, str(e))
        logger.error("Stack trace: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to refresh cache: {str(e)}")

@router.get("/table/{table_name}")
def get_table_info(table_name: str):
    """Get detailed information for a specific table."""
    start_time = time.time()
    logger.info("Table info request received: %s", table_name)
    
    try:
        table_info = schema_service.get_table_info(table_name)
        if "error" in table_info and table_info["error"] is not None and str(table_info["error"]).strip():
            duration = time.time() - start_time
            logger.error("Table info failed after %.3f seconds: %s", duration, table_info["error"])
            raise HTTPException(status_code=404, detail=table_info["error"])
        
        duration = time.time() - start_time
        logger.info("Table info completed successfully in %.3f seconds", duration)
        return table_info
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Table info failed after %.3f seconds: %s", duration, str(e))
        logger.error("Stack trace: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get table info: {str(e)}") 
