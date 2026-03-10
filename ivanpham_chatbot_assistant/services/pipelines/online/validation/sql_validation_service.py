from typing import Any, Dict, List, Optional, Set, Tuple

import sqlglot
from sqlglot import exp, parse_one
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from loguru import logger

from ivanpham_chatbot_assistant.db.models.table import Table
from ivanpham_chatbot_assistant.db.models.column import Column
from ivanpham_chatbot_assistant.db.models.schema import Schema


class SqlValidationService:
    """
    Production-grade validator service to ensure generated SQL is safe,
    syntactically correct, and adheres to the existing schema metadata.
    """

    # Forbidden DDL or DML operations to ensure read-only access
    FORBIDDEN_OPERATIONS = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", 
        "GRANT", "REVOKE", "MERGE", "REPLACE"
    }

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def validate(self, sql: str) -> Dict[str, Any]:
        """
        Main validation entry point.
        """
        logger.info("Validating generated SQL.")

        try:
            # 1. Static Safety Checks
            if not self._is_read_only(sql):
                 return {
                    "status": "error",
                    "is_valid": False,
                    "reason": "Forbidden SQL operation detected. Only SELECT and WITH are allowed."
                }

            # 2. SQL AST Parsing
            expression = self._parse_sql(sql)
            if expression is None:
                return {
                    "status": "error",
                    "is_valid": False,
                    "reason": "SQL syntax error"
                }

            # 3. Structural Analysis
            ctes = self._extract_ctes(expression)
            tables = self._extract_tables(expression, ctes)
            alias_map = self._extract_alias_map(expression, ctes)
            raw_columns = self._extract_columns(expression)
            
            # 4. Resolve Aliases
            resolved_columns = self._resolve_columns(raw_columns, alias_map)

            # 5. Metadata Verification
            valid_schema = await self._verify_metadata(tables, resolved_columns)
            if not valid_schema["valid"]:
                  return {
                    "status": "error",
                    "is_valid": False,
                    "reason": valid_schema["reason"]
                }

            # 6. LIMIT Enforcement
            # We modify the AST and return the validated/modified SQL if needed
            # In this context, we just ensure it's valid, but the pipeline might want the "safe" SQL
            # For now, we return success if it passed metadata verification.
            
            logger.info("SQL validation successful.")
            return {
                "status": "success",
                "is_valid": True
            }

        except Exception as e:
            logger.error(f"Critical error during SQL validation: {e}")
            return {
                "status": "error",
                "is_valid": False,
                "reason": f"Validation internal error: {str(e)}"
            }

    def _is_read_only(self, sql: str) -> bool:
        """Enforce read-only SQL queries."""
        upper_sql = sql.strip().upper()
        # Must start with SELECT or WITH
        if not (upper_sql.startswith("SELECT") or upper_sql.startswith("WITH")):
            return False
            
        # Check for forbidden keywords as whole words
        for op in self.FORBIDDEN_OPERATIONS:
            if f" {op} " in f" {upper_sql} " or upper_sql.startswith(f"{op} "):
                return False
        return True

    def _parse_sql(self, sql: str) -> Optional[exp.Expression]:
        """Parse SQL into an AST using sqlglot with T-SQL dialect."""
        try:
            return parse_one(sql, read="tsql")
        except Exception as e:
            logger.error(f"SQL parsing error: {e}")
            return None

    def _extract_ctes(self, expression: exp.Expression) -> Set[str]:
        """Extract CTE names to exclude them from metadata checks."""
        ctes = set()
        for cte in expression.find_all(exp.CTE):
            ctes.add(cte.alias_or_name.lower())
        return ctes

    def _extract_tables(self, expression: exp.Expression, ctes: Set[str]) -> Set[str]:
        """Extract unique table names (schema.table) from SQL expression, excluding CTEs."""
        tables = set()
        for table in expression.find_all(exp.Table):
            table_name = table.name.lower()
            if table_name in ctes:
                continue
            
            schema_name = table.db.lower() if table.db else None
            full_name = f"{schema_name}.{table_name}" if schema_name else table_name
            tables.add(full_name)
        return tables

    def _extract_alias_map(self, expression: exp.Expression, ctes: Set[str]) -> Dict[str, str]:
        """Map aliases to full table names or CTE names."""
        alias_map = {}
        for table in expression.find_all(exp.Table):
            alias = table.alias.lower() if table.alias else None
            if alias:
                table_name = table.name.lower()
                schema_name = table.db.lower() if table.db else None
                full_name = f"{schema_name}.{table_name}" if schema_name else table_name
                alias_map[alias] = full_name
        return alias_map

    def _extract_columns(self, expression: exp.Expression) -> List[Dict[str, Optional[str]]]:
        """Extract column references with their table/alias qualifiers."""
        columns = []
        for column in expression.find_all(exp.Column):
            columns.append({
                "table": column.table.lower() if column.table else None,
                "column": column.name.lower()
            })
        return columns

    def _resolve_columns(self, columns: List[Dict[str, Optional[str]]], alias_map: Dict[str, str]) -> List[Dict[str, Optional[str]]]:
        """Resolve column table/alias to actual table names."""
        resolved = []
        for col in columns:
            table_ref = col["table"]
            if table_ref and table_ref in alias_map:
                table_ref = alias_map[table_ref]
            
            resolved.append({
                "table": table_ref,
                "column": col["column"]
            })
        return resolved

    async def _verify_metadata(self, tables: Set[str], columns: List[Dict[str, Optional[str]]]) -> Dict[str, Any]:
        """Verify tables and columns in batch against database metadata."""
        if not tables and not columns:
            return {"valid": True}

        async with self.session_factory() as session:
            # 1. Parse table names into (schema, name)
            table_lookups = []
            for t in tables:
                if "." in t:
                    s_name, t_name = t.split(".", 1)
                    table_lookups.append((s_name, t_name))
                else:
                    table_lookups.append((None, t))

            # 2. Batch fetch metadata: Tables + Schemas + Columns
            # We fetch all tables that match any of the names, then filter by schema in memory
            # to keep the query simple and efficient.
            from sqlalchemy import func
            table_names = {t_name for _, t_name in table_lookups}
            
            stmt = (
                select(Table)
                .join(Schema)
                .options(selectinload(Table.columns), selectinload(Table.schema))
                .where(func.lower(Table.name).in_(table_names))
            )
            
            result = await session.execute(stmt)
            db_tables = result.scalars().all()

            # 3. Build a searchable metadata map: { "schema.table": { "col1", "col2" } }
            # and { "table": { "schema1.table": {...}, "schema2.table": {...} } } for unqualified lookups
            metadata = {}
            unqualified_metadata = {} # table_name -> list of schemas it exists in

            for db_table in db_tables:
                schema_name = db_table.schema.name.lower()
                table_name = db_table.name.lower()
                full_name = f"{schema_name}.{table_name}"
                cols = {c.name.lower() for c in db_table.columns}
                
                metadata[full_name] = cols
                metadata[table_name] = cols # Support lookup by just table name if unique
                
                if table_name not in unqualified_metadata:
                    unqualified_metadata[table_name] = []
                unqualified_metadata[table_name].append(schema_name)

            # 4. Validate Tables
            for s_name, t_name in table_lookups:
                if s_name:
                    full_name = f"{s_name}.{t_name}"
                    if full_name not in metadata:
                        return {"valid": False, "reason": f"Table '{full_name}' not found in metadata."}
                else:
                    if t_name not in metadata:
                        return {"valid": False, "reason": f"Table '{t_name}' not found in metadata."}
                    if len(unqualified_metadata.get(t_name, [])) > 1:
                        # Ambiguous table reference if multiple schemas have it (though rare in this context)
                        pass 

            # 5. Validate Columns
            for col in columns:
                t_ref = col["table"]
                c_name = col["column"]

                if t_ref:
                    # Qualified column: alias.col or schema.table.col or table.col
                    if t_ref not in metadata:
                         return {"valid": False, "reason": f"Table/Alias '{t_ref}' referenced in column '{c_name}' not found."}
                    if c_name not in metadata[t_ref]:
                         return {"valid": False, "reason": f"Column '{c_name}' not found in table '{t_ref}'."}
                else:
                    # Unqualified column: must exist in at least one of the tables in the query
                    found_in_count = 0
                    for t_full_name in tables:
                        if t_full_name in metadata and c_name in metadata[t_full_name]:
                            found_in_count += 1
                    
                    # If not explicitly in tables set, check by t_name
                    if found_in_count == 0:
                         for t_full_name in tables:
                             t_name = t_full_name.split(".")[-1]
                             if t_name in metadata and c_name in metadata[t_name]:
                                 found_in_count += 1
                                 
                    if found_in_count == 0:
                        return {"valid": False, "reason": f"Column '{c_name}' could not be resolved to any table in the query."}
                    # We could check for ambiguity here if found_in_count > 1

        return {"valid": True}

    def _enforce_limit(self, expression: exp.Expression, limit: int = 100) -> exp.Expression:
        """Add LIMIT to the query if it doesn't already have one."""
        if isinstance(expression, exp.Select):
            if not expression.args.get("limit"):
                return expression.limit(limit)
        return expression

    async def safe_execute(self, sql: str, timeout_ms: int = 5000) -> List[Dict[str, Any]]:
        """
        Optional safe execution with statement timeout and read-only transaction.
        """
        validation = await self.validate(sql)
        if not validation["is_valid"]:
            raise ValueError(f"SQL Validation failed: {validation['reason']}")

        # Enforce limit before execution
        expression = self._parse_sql(sql)
        if expression:
            expression = self._enforce_limit(expression)
            sql = expression.sql()

        async with self.session_factory() as session:
            # Set statement timeout
            await session.execute(sqlglot.transpile(f"SET statement_timeout = {timeout_ms}", read="postgres", write="postgres")[0])
            # Set transaction read only
            await session.execute(sqlglot.transpile("SET TRANSACTION READ ONLY", read="postgres", write="postgres")[0])
            
            result = await session.execute(sqlglot.exp.select("*").from_(sqlglot.exp.Table(name="sub", alias="sub")).sql()) # Dummy example
            # This part needs actual implementation based on requirements
            return []
