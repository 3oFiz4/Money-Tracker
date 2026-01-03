from typing import Any, Dict, List, Optional, Sequence, Union
from supabase import Client

RowInput = Union[str, Sequence[Any], Dict[str, Any]]

class TableManager:
    """
    Thin helper over a Supabase table.
    """
    def __init__(
        self,
        client: Client,
        table_name: str,
        id_field: str = "id",
        position_field: Optional[str] = "position",
    ):
        self.client = client
        self.table = table_name
        self.id_field = id_field
        self.position_field = position_field

    # -------- Helpers --------
    def _parse_row(
        self,
        data: RowInput,
        columns: Optional[List[str]],
        separator: str,
    ) -> Dict[str, Any]:
        # Build row dict from string / list / dict
        if isinstance(data, dict):
            return dict(data)
        if isinstance(data, str):
            parts = [p.strip() for p in data.split(separator)]
        elif isinstance(data, (list, tuple)):
            parts = list(data)
        else:
            raise ValueError("Unsupported data type.")
        if not columns:
            raise ValueError("Columns must be provided for non-dict data.")
        if len(parts) != len(columns):
            raise ValueError("Data length and columns length differ.")
        return dict(zip(columns, parts))

    def _max_position(self) -> Optional[float]:
        if not self.position_field:
            return None
        res = (
            self.client.table(self.table)
            .select(self.position_field)
            .order(self.position_field, desc=True)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        return rows[0][self.position_field] if rows else None

    def _position_after_index(self, after_index: int) -> float:
        # Compute position to insert after given index (0-based)
        if self.position_field is None:
            return None
        res = (
            self.client.table(self.table)
            .select(self.position_field)
            .order(self.position_field, desc=False)
            .range(after_index, after_index + 1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            last = self._max_position()
            return (last + 1) if last is not None else 1
        curr_pos = rows[0][self.position_field]
        res_next = (
            self.client.table(self.table)
            .select(self.position_field)
            .order(self.position_field, desc=False)
            .range(after_index + 1, after_index + 1)
            .execute()
        )
        next_rows = res_next.data or []
        if not next_rows:
            return curr_pos + 1
        next_pos = next_rows[0][self.position_field]
        return (curr_pos + next_pos) / 2

    def _compute_insert_position(self, index: Union[str, int]) -> Optional[float]:
        if self.position_field is None:
            return None
        if isinstance(index, str):
            index = index.strip()
        if index in (None, "-", ""):
            last = self._max_position()
            return (last + 1) if last is not None else 1
        if isinstance(index, str) and index.endswith("+"):
            idx = int(index[:-1])
            return self._position_after_index(idx)
        if isinstance(index, int):
            return self._position_after_index(index)
        raise ValueError("Invalid index format.")

    # -------- Add --------
    def add_row(
        self,
        data: RowInput,
        columns: Optional[List[str]] = None,
        separator: str = ";",
        index: Union[str, int] = "-",
    ) -> Dict[str, Any]:
        # Add a row; dicts are accepted directly
        row = self._parse_row(data, columns, separator)
        pos = self._compute_insert_position(index)
        if pos is not None:
            row[self.position_field] = pos
        res = self.client.table(self.table).insert(row).execute()
        return res.data[0] if res.data else {}

    # -------- Remove --------
    def remove_by_id(self, row_id: Any) -> int:
        res = (
            self.client.table(self.table)
            .delete()
            .eq(self.id_field, row_id)
            .execute()
        )
        return res.count or 0

    def remove_by_range(self, start_index: int, end_index: int) -> int:
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        limit = end_index - start_index + 1
        ids_res = (
            self.client.table(self.table)
            .select(self.id_field)
            .order(self.position_field or self.id_field, desc=False)
            .range(start_index, start_index + limit - 1)
            .execute()
        )
        ids = [r[self.id_field] for r in (ids_res.data or [])]
        if not ids:
            return 0
        res = (
            self.client.table(self.table)
            .delete()
            .in_(self.id_field, ids)
            .execute()
        )
        return res.count or 0

    def remove_by_regex(
        self,
        pattern: str,
        column: str,
        clear_cell: bool = False,
    ) -> int:
        if clear_cell:
            res = (
                self.client.table(self.table)
                .update({column: None})
                .filter(column, "regex", pattern)
                .execute()
            )
            return res.count or 0
        res = (
            self.client.table(self.table)
            .delete()
            .filter(column, "regex", pattern)
            .execute()
        )
        return res.count or 0

    # -------- Patch --------
    def patch_by_id(self, row_id: Any, column: str, value: Any) -> int:
        res = (
            self.client.table(self.table)
            .update({column: value})
            .eq(self.id_field, row_id)
            .execute()
        )
        return res.count or 0

    def patch_by_regex(
        self,
        pattern: str,
        column: str,
        value: Any,
        match_column: Optional[str] = None,
    ) -> int:
        target_col = match_column or column
        res = (
            self.client.table(self.table)
            .update({column: value})
            .filter(target_col, "regex", pattern)
            .execute()
        )
        return res.count or 0

    # -------- Sort + paginate --------
    def sort_by(
        self,
        column: str,
        method: str = "Newest",
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        desc = method.lower() == "newest"
        start = (page - 1) * page_size
        end = start + page_size - 1
        res = (
            self.client.table(self.table)
            .select("*", count="exact")
            .order(column, desc=desc)
            .range(start, end)
            .execute()
        )
        return {
            "data": res.data or [],
            "total": res.count or 0,
            "page": page,
            "page_size": page_size,
        }

# ---------------- Usage example ----------------
    # Add via dict (no columns needed)
    # new_row = manager.add_row({"id": 1, "date": 20})
    # Add via string with columns
    # new_row = manager.add_row("1;2024-01-01", columns=["id", "date"], separator=";")
    # Add via list
    # new_row = manager.add_row([2, "2024-02-01"], columns=["id", "date"], index="0+")