from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import argparse
import sys



class Args:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Money Growth", add_help=False)
        self.parser.add_argument("-h", "--help", action="store_true", help="Show this help message")
        self.subparsers = self.parser.add_subparsers(dest="command")
        self.registry = {}

        # Sections
        self.sections = {
            "Snippets": [],
            "Commands": [],
            "Statistics": []
        }
        self.console = Console()

    def _register_to_section(self, section_name, name, help_text):
        """Helper to track which command goes where."""
        if section_name in self.sections:
            self.sections[section_name].append((name, help_text))

    def command(self, name, help_text, section="Commands", args_config=None):
        def decorator(func):
            sub = self.subparsers.add_parser(name, help=help_text, add_help=True)
            if args_config:
                for arg in args_config:
                    # Using .copy() to avoid modifying original dicts
                    cfg = arg.copy()
                    flags = cfg.pop("flags")
                    sub.add_argument(*flags, **cfg)
            
            self.registry[name] = func
            self._register_to_section(section, name, help_text)
            return func
        return decorator

    def ensnippet(self, snippet_data, section="Snippets"):
        def decorator(func):
            name = snippet_data["name"]
            help_msg = snippet_data.get('description2', 'No description')
            
            sub = self.subparsers.add_parser(name, help=help_msg)
            type_map = {"int": int, "str": str, "float": float}
            
            for arg in snippet_data["args_config"]:
                cfg = arg.copy()
                flags = cfg.pop("flags")
                cfg["type"] = type_map.get(cfg["type"], str)
                if "modify" in flags:
                    cfg["nargs"] = "?"
                    cfg["default"] = ""
                sub.add_argument(*flags, **cfg)

            def wrapper(args):
                modify_raw = getattr(args, 'modify', "") or "" 
                normalized = {}
                if modify_raw.strip():
                    pairs = [item.split('=') for item in modify_raw.split(';') if '=' in item]
                    normalized = {k.strip(): v.strip() for k, v in pairs}
                args.normalized_modify = normalized
                return func(args)

            self.registry[name] = wrapper
            self._register_to_section(section, name, help_msg)
            return func
        return decorator

    def _print_custom_help(self):
        """Prints a sectioned help menu using Rich."""
        self.console.print(Panel("[bold green]Money Growth CLI[/]", subtitle="v1.0"))
        self.console.print("Usage: python main.py [COMMAND] [ARGS]\n")

        for section, commands in self.sections.items():
            if not commands: continue
            
            table = Table(title=f"[bold cyan]{section}[/]", show_header=False, box=None, padding=(0, 2))
            table.add_column("Command", style="bold yellow", width=15)
            table.add_column("Description", style="white")
            
            for cmd_name, cmd_help in commands:
                table.add_row(cmd_name, cmd_help.split('\n')[0]) # Only first line of help
            
            self.console.print(table)
            self.console.print("") # Spacer

    def run(self):
        # Handle help cmd
        if len(sys.argv) == 1 or sys.argv[1] in ["-h", "--help", "help"]:
            self._print_custom_help()
            return

        # Parse args
        args = self.parser.parse_args()

        # Execute if command exist in registry
        if args.command in self.registry:
            self.registry[args.command](args)
        else:
            # 4. If command is unknown or empty, show help
            self.console.print(f"[red]Unknown command:[/][bold white] {args.command}[/]\n")
            self._print_custom_help()

# @Args.command(
#     name="power",
#     help_text="Calculate base to the power of exponent",
#     args_config=[
#         {"flags": ["base"], "type": int},
#         {"flags": ["exponent"], "type": int}
#     ]
# )
# def external_power_command(args):
#     print(f"Result: {args.base ** args.exponent}")