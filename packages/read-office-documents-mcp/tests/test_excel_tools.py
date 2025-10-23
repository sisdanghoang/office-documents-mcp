import os
import asyncio
from read_office_documents_mcp.__main__ import list_excel_sheets, read_excel_sheet

# Update this path to point to a valid .xlsx file for testing
EXCEL_FILE_URI = "file:///path/to/test.xlsx"

async def test_list_sheets():
    sheets = await list_excel_sheets(EXCEL_FILE_URI)
    print("Sheet names:", sheets)

async def test_read_sheet():
    sheet_name = "Sheet1"  # Update as needed
    markdown = await read_excel_sheet(EXCEL_FILE_URI, sheet_name)
    print(f"Markdown for {sheet_name}:\n", markdown)

if __name__ == "__main__":
    asyncio.run(test_list_sheets())
    asyncio.run(test_read_sheet())
