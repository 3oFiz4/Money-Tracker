from utils.db import TableManager
from utils.args import Args
from utils.log import CLI
from supabase import create_client, Client
from utils.reader import Reader
import datetime
import json

##### Variable Initialization
with open('config.json', 'r') as conf:
    config = json.load(conf)
with open('snippet.json', 'r') as snip:
    snippet = json.load(snip)
SUPABASE_URL = config["secret"]["SUPABASE_URL"]
SUPABASE_KEY = config["secret"]["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

##### Class Initialization
CLI = CLI()
Args = Args()
Manager = TableManager(
    client=supabase,
    table_name="transactions",
    id_field="id",
    position_field="id",  # ensure this numeric column exists if you need index inserts
)

#### Commnds 
######## Snippets
@Args.ensnippet(snippet["simple_push"])
def simple_push(args):
    balance_after = supabase.table("transactions").select("balance_after").order("id", desc=True).limit(1).execute()
    balance_after = balance_after.data[0].get("balance_after")
    Manager.add_row({
    "id": 1, 
    "type": "buy",
    "mode": "liquid",
    "register": 'snack',
    "priority": "wants",
    "is_transfer": "no",
    "balance_before": balance_after,
    "balance_after": balance_after - args.amount,
    "description": args.description, 
    "amount": args.amount,
    })
    CLI.Log(f"[green]Result: Success[/]")
######## Built-In (Database Related)
@Args.command(
    name="v", 
    help_text="View records in Excel style", 
    section="Statistics",
    args_config=[
        {"flags": ["rows"], "type": int, "default": 10, "help": "Number of rows to show"},
        {"flags": ["cols"], "type": int, "default": 5, "help": "Number of columns to show"}
    ]
)
def view_data(args):
    raw_data = supabase.table("transactions").select('*').execute().data
    if not raw_data:
        CLI.Out("No data found in database.", color="red")
        return # Don't even start the reader if there is no data
    view = Reader(raw_data, row_limit=args.rows, col_limit=args.cols)
    view.show()
Args.run()