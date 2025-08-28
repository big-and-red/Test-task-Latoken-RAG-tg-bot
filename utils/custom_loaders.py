from typing import Union, Iterator, Optional
from pathlib import Path

import openpyxl
from langchain_core.documents import Document
from langchain_community.document_loaders.base import BaseLoader


class ExcelLoader(BaseLoader):
    """Load Excel file (xlsx) and convert to Document format.

    Args:
        file_path: Path to the Excel file to load.
        sheet_name: Name of the sheet to load. If `None`, loads the first sheet.
        start_row: Row to start reading from. Defaults to 1 (first row).
    """

    def __init__(
            self,
            file_path: Union[str, Path],
            sheet_name: Optional[str] = None,
            start_row: int = 1,
    ):
        """Initialize with file path and optional sheet name."""
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.start_row = start_row

    def lazy_load(self) -> Iterator[Document]:
        """Lazy load documents from the Excel file."""
        workbook = openpyxl.load_workbook(self.file_path)
        sheet = workbook[self.sheet_name] if self.sheet_name else workbook.active

        rows = []
        for row in sheet.iter_rows(min_row=self.start_row, values_only=True):
            row_text = "\t".join([str(cell) if cell is not None else "" for cell in row])
            rows.append(row_text)

        combined_text = "\n".join(rows)
        metadata = {"source": str(self.file_path), "sheet": sheet.title}
        yield Document(page_content=combined_text, metadata=metadata)
