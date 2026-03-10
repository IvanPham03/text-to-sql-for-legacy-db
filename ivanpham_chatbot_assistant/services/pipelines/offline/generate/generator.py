import asyncio
import time
from typing import Any, Dict, List, Optional
from ivanpham_chatbot_assistant.log import logger
from ivanpham_chatbot_assistant.services.llm.llm_service import LLMService
from ivanpham_chatbot_assistant.services.utils.prompt_renderer import PromptRenderer

class DescriptionGenerator:
    """
    Production-grade generator that uses LLM to infer semantic meanings 
    for database tables and columns based on metadata and samples.
    """
    def __init__(self, llm_service: LLMService, templates_dir: str, max_concurrency: int = 5):
        self.llm_service = llm_service
        self.renderer = PromptRenderer(templates_dir)
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def generate_table_description(self, table_name: str, columns: List[Dict[str, Any]]) -> str:
        """
        Generates a concise semantic description for a table.
        """
        context = {
            "table_name": table_name,
            "columns": columns # List of {name, data_type, sample_values}
        }
        prompt = self.renderer.render("table_description.jinja2", context)
        
        start_time = time.perf_counter()
        try:
            async with self.semaphore:
                logger.info(f"Generating description for table: {table_name}")
                response = await self.llm_service.generate(prompt, temperature=0.1)
                description = response["text"].strip()
                
                latency = time.perf_counter() - start_time
                logger.info(f"Table description generated for {table_name} in {latency:.2f}s")
                return description
        except Exception as e:
            logger.error(f"Failed to generate table description for {table_name}: {e}")
            return f"Table {table_name} metadata."

    async def generate_column_descriptions(
        self, 
        table_name: str, 
        table_description: str, 
        columns: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Generates semantic descriptions for all columns in a table in parallel.
        """
        descriptions = {}
        tasks = []

        for col in columns:
            sibling_columns = [
                {"name": c["name"], "data_type": c["data_type"]} 
                for c in columns if c["name"] != col["name"]
            ]
            # Cap sibling columns to avoid prompt bloat
            sibling_columns = sibling_columns[:15] 
            
            tasks.append(self._generate_single_column_description(
                table_name, table_description, col, sibling_columns
            ))

        results = await asyncio.gather(*tasks)
        for col_name, desc in results:
            descriptions[col_name] = desc
            
        return descriptions

    async def _generate_single_column_description(
        self, 
        table_name: str, 
        table_description: str, 
        column: Dict[str, Any], 
        sibling_columns: List[Dict[str, Any]]
    ) -> tuple[str, str]:
        """
        Helper for parallel column description generation.
        """
        col_name = column["name"]
        context = {
            "table_name": table_name,
            "table_description": table_description,
            "column_name": col_name,
            "data_type": column["data_type"],
            "sample_values": column.get("sample_values", [])[:5], # Cap sample values
            "sibling_columns": sibling_columns
        }
        prompt = self.renderer.render("column_description.jinja2", context)
        
        start_time = time.perf_counter()
        try:
            async with self.semaphore:
                response = await self.llm_service.generate(prompt, temperature=0.1)
                desc = response["text"].strip()
                latency = time.perf_counter() - start_time
                logger.debug(f"Column description generated for {table_name}.{col_name} in {latency:.2f}s")
                return col_name, desc
        except Exception as e:
            logger.warning(f"Failed to generate column description for {table_name}.{col_name}: {e}")
            return col_name, f"Reference for {col_name}."
