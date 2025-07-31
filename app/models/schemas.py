from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class QueryRequest(BaseModel):
    query: str

class OptimizationSuggestion(BaseModel):
    type: str  # "query_rewrite", "index", "partition", "view", "sharding"
    description: str
    impact: str  # "high", "medium", "low"
    implementation_steps: List[str]
    estimated_improvement: Optional[str]

class QueryAnalysis(BaseModel):
    tables_used: List[str]
    columns_accessed: Dict[str, List[str]]
    query_complexity: str  # "simple", "moderate", "complex"
    estimated_cost: Optional[float]

class OptimizationResponse(BaseModel):
    query_analysis: QueryAnalysis
    suggestions: List[OptimizationSuggestion]
    current_performance_metrics: Optional[Dict[str, Any]]
    estimated_performance_improvement: Optional[Dict[str, Any]]

class NaturalQueryRequest(BaseModel):
    query: str

class NaturalQueryResponse(BaseModel):
    natural_query: str
    generated_sql: str
    tables_used: List[str]
    confidence: str  # "high", "medium", "low"
    results: List[Dict[str, Any]]
    row_count: int
    columns: List[str]
    error: Optional[str] = None

class SQLGenerationResponse(BaseModel):
    sql_query: str
    natural_query: str
    tables_used: List[str]
    confidence: str
    error: Optional[str] = None
    suggestions: Optional[List[str]] = None

class SchemaResponse(BaseModel):
    tables: Dict[str, Any]
    relationships: Dict[str, List[Dict[str, Any]]]
    sample_data: Dict[str, List[Dict[str, Any]]]
    constraints: Dict[str, List[Dict[str, Any]]]
    statistics: Dict[str, Any]

class SchemaSummaryResponse(BaseModel):
    summary: str 
