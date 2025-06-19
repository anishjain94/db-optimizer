# from typing import Dict, Any
# import openai
# from ..core.config import get_settings
# from ..core.database import engine
# from sqlalchemy import text

# class QueryGenerator:
#     def __init__(self):
#         self.settings = get_settings()
#         openai.api_key = self.settings.OPENAI_API_KEY

#     def generate_sql(self, natural_query: str) -> str:
#         """Convert natural language query to SQL using OpenAI."""
#         prompt = f"""
#         Convert the following natural language query to PostgreSQL SQL:
#         "{natural_query}"
        
#         Return ONLY the SQL query without any explanation or additional text.
#         """
        
#         client = openai.OpenAI(api_key=self.settings.OPENAI_API_KEY)
#         response = client.chat.completions.create(
#             model=self.settings.OPENAI_MODEL,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.1,
#             max_tokens=150
#         )
        
#         sql_query = response.choices[0].message.content.strip()
#         # Remove any markdown code block formatting if present
#         sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
#         return sql_query

#     def execute_query(self, sql_query: str) -> Dict[str, Any]:
#         """Execute the SQL query and return results."""
#         try:
#             with engine.connect() as conn:
#                 result = conn.execute(text(sql_query))
#                 columns = result.keys()
#                 rows = [dict(zip(columns, row)) for row in result.fetchall()]
#                 return {
#                     "sql_query": sql_query,
#                     "results": rows,
#                     "row_count": len(rows)
#                 }
#         except Exception as e:
#             return {
#                 "error": str(e),
#                 "sql_query": sql_query
#             } 
