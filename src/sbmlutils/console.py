"""Rich console for logging."""
from rich import pretty
from rich.console import Console
from rich.theme import Theme


pretty.install()
custom_theme = Theme(
    {
        "success": "green",
        "info": "blue",
        "warning": "orange3",
        "error": "red",
    }
)

console = Console(record=True, theme=custom_theme)
