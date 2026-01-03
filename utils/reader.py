import pandas as pd
import os
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class Reader:
    def __init__(self, raw_data, row_limit=15, col_limit=5):
        # Handle cases where data is empty or None
        if not raw_data:
            self.df = pd.DataFrame([{"System": "No data found"}])
        else:
            self.df = pd.DataFrame(raw_data)
        
        self.row_limit = row_limit
        self.col_limit = col_limit
        self.current_row = 0
        self.current_col = 0
        self.console = Console()

    def _get_table(self):
        # Calculate slices for pagination
        row_end = min(self.current_row + self.row_limit, len(self.df))
        col_end = min(self.current_col + self.col_limit, len(self.df.columns))
        
        subset = self.df.iloc[self.current_row:row_end, self.current_col:col_end]
        
        table = Table(
            header_style="bold magenta",
            border_style="bright_blue",
            expand=True,
            box=None # Minimalist look
        )

        for column in subset.columns:
            table.add_column(str(column), justify="left", no_wrap=True)

        for _, row in subset.iterrows():
            # Convert all items to string to avoid NotRenderableError
            table.add_row(*[str(item) if item is not None else "" for item in row.values])
        
        return table

    def show(self):
        """Interactive loop for pagination and column scrolling."""
        while True:
            # Clear screen based on OS
            os.system('cls' if os.name == 'nt' else 'clear')
            
            stats = (f"Rows: {self.current_row+1}-{min(self.current_row+self.row_limit, len(self.df))} of {len(self.df)} | "
                     f"Cols: {self.current_col+1}-{min(self.current_col+self.col_limit, len(self.df.columns))} of {len(self.df.columns)}")
            
            self.console.print(Panel(self._get_table(), title="Database Viewer", subtitle=stats))
            
            self.console.print("\n[bold yellow]Controls:[/]")
            self.console.print("[cyan][+][/][cyan][-][/] Rows | [cyan][>][/][cyan][<][/] Columns | [red](x)[/] Exit")
            
            try:
                choice = input("\nAction: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                # Handle Ctrl+C or Ctrl+D cleanly
                return

            if choice == "x":
                return # Exit the function immediately
            
            elif choice == "+":
                if self.current_row + self.row_limit < len(self.df):
                    self.current_row += self.row_limit
            elif choice == "-":
                self.current_row = max(0, self.current_row - self.row_limit)
            elif choice in [">", ".", "d"]: # 'd' for right
                if self.current_col + self.col_limit < len(self.df.columns):
                    self.current_col += self.col_limit
            elif choice in ["<", ",", "a"]: # 'a' for left
                self.current_col = max(0, self.current_col - self.col_limit)