from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class PromptRenderer:
    """
    Production-grade prompt renderer using Jinja2 with template caching.
    """

    def __init__(self, templates_dir: str):
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml", "jinja2"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._cache = {}

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Renders a template with the given context.
        """
        if template_name not in self._cache:
            self._cache[template_name] = self.env.get_template(template_name)

        template = self._cache[template_name]
        return template.render(**context)


# Singleton instance or factory method can be added as needed
