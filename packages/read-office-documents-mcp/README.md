# read-office-documents-mcp

MCP server for reading office documents, with special support for Excel files:
- List sheet names in an Excel file
- Read and convert the content of a selected sheet to markdown
- Read PDF, PowerPoint, Word, and other files to markdown

## Installation

You need Python 3.8+ installed.

It is recommended to use a Python virtual environment:

```bash
# Create a new virtual environment (Windows)
python -m venv .venv

# Activate the virtual environment (Windows)
.venv\Scripts\activate

# On macOS/Linux, use:
# python3 -m venv .venv
# source .venv/bin/activate
```

Install all dependencies and the package itself:
```bash
pip install .
```
Or, if you want to install in editable mode for development:
```bash
pip install -e .
```

## Running the MCP Server

To run the server with HTTP/SSE transport (recommended for integration):
```bash
python -m read_office_documents_mcp --http --host 127.0.0.1 --port 3001
```
To run with STDIO transport (for direct CLI use):
```bash
python -m read_office_documents_mcp
```

## Tools Provided

- `list_excel_sheets(uri: str) -> list[str]`
- `read_excel_sheet(uri: str, sheet_name: str) -> str`
- `read_pdf_file(uri: str) -> str`
- `read_powerpoint_file(uri: str) -> str`
- `read_word_file(uri: str) -> str`
- `read_other_files(uri: str) -> str`

All tools currently support `file://` URIs. Example: `file:///path/to/document.xlsx`

## Example Usage

Python example for listing Excel sheets:
```python
import asyncio
from read_office_documents_mcp.__main__ import list_excel_sheets

uri = "file:///path/to/document.xlsx"
sheets = asyncio.run(list_excel_sheets(uri))
print(sheets)
```

Python example for reading a Word file:
```python
import asyncio
from read_office_documents_mcp.__main__ import read_word_file

uri = "file:///path/to/document.docx"
content = asyncio.run(read_word_file(uri))
print(content)
```

## Development

To run tests:
```bash
python packages/read-office-documents-mcp/tests/test_excel_tools.py
```

## License

MIT License
