from fastapi import APIRouter, HTTPException
from ..models.schemas import QueryRequest, NaturalQueryRequest
from ..services.optimizer import QueryOptimizer
# from ..services.query_generator import QueryGenerator

router = APIRouter()
optimizer = QueryOptimizer()
# query_generator = QueryGenerator()

@router.post("/optimize-query")
def optimize_query(request: QueryRequest):
    try:
        result = optimizer.optimize(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")
    return {"data": result}

# @router.post("/natural-query")
# def process_natural_query(request: NaturalQueryRequest):
#     try:
#         # Generate SQL from natural language
#         sql_query = query_generator.generate_sql(request.query)
        
#         # Execute the generated SQL
#         result = query_generator.execute_query(sql_query)
        
#         if "error" in result:
#             raise HTTPException(status_code=500, detail=result["error"])
            
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}") 
