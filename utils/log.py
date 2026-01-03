import json
from rich.console import Console
from rich.theme import Theme

class CLI:
    def __init__(self, log_enabled=True):
        # We can define custom themes or just use the standard console
        self.console = Console()
        self.log_enabled = True

    def Out(self, text, color=""):
        """
        Prints text to the console.
        - If color is provided, the whole line is colored.
        - Supports Rich markup in text (e.g., "Hello [bold red]World[/]!")
        """
        if color:
            # Wrap the entire text in a color tag for "fast access"
            self.console.print(f"[{color}]{text}[/]")
        else:
            # Just print normally, allowing internal markup
            self.console.print(text)

    def Log(self, text):
        """Prints text only if log_enabled is True. Styled differently to stand out."""
        if self.log_enabled:
            # We use a specific style for logs (e.g., dimmed/grey)
            self.console.print(f"[grey50]LOG:[/] {text}")

# --- Usage Examples ---

# cli = CLI(log_enabled=True)

# # 1. Whole line color (Fast Access)
# cli.Out("This is a successful operation!", color="green")
# cli.Out("This is a critical error!", color="bold red")

# # 2. Mixed colors via text markup
# cli.Out("This line is normal, but [blue]this part is blue[/] and [yellow]this is yellow[/].")

# # 3. Using the Logger
# cli.Log("Initializing database connection...")
# cli.toggle_logger(False)
# cli.Log("This will not be printed because logs are disabled.")
