import contextlib
import sys
import os
from collections.abc import AsyncIterator
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
import pandas as pd
import uvicorn

# Initialize FastMCP server for read-office-documents
mcp = FastMCP("read-office-documents")

@mcp.tool()
async def list_excel_sheets(uri: str) -> list[str]:
    """
    List all sheet names in an Excel file (.xlsx).
    Supports file:// URIs.
    """
    import os

    if uri.startswith("file://"):
        file_path = uri[7:]
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        excel = pd.ExcelFile(file_path, engine="openpyxl")
        return excel.sheet_names
    else:
        raise ValueError("Only file:// URIs are currently supported.")

@mcp.tool()
async def read_excel_sheet(uri: str, sheet_name: str) -> str:
    """
    Read the content of a specific sheet in an Excel file (.xlsx) and return as markdown.
    Supports file:// URIs.
    """
    import os

    if uri.startswith("file://"):
        file_path = uri[7:]
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
        html_table = df.to_html(index=False)
        try:
            from markdownify import markdownify as md
            markdown = md(html_table)
        except ImportError:
            markdown = f"HTML table for sheet '{sheet_name}':\n\n{html_table}"
        return markdown
    else:
        raise ValueError("Only file:// URIs are currently supported.")

@mcp.tool()
async def read_pdf_file(uri: str) -> str:
    """
    Read the content of a PDF file and return as markdown.
    Supports file:// URIs.
    """
    import os
    if uri.startswith("file://"):
        file_path = uri[7:]
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        try:
            import PyPDF2
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
            return text
        except ImportError:
            return "PyPDF2 is not installed."
    else:
        raise ValueError("Only file:// URIs are currently supported.")

@mcp.tool()
async def read_powerpoint_file(uri: str) -> str:
    """
    Read the content of a PowerPoint file (.pptx) and return as markdown.
    Supports file:// URIs.
    """
    import os
    if uri.startswith("file://"):
        file_path = uri[7:]
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        try:
            from pptx import Presentation
            prs = Presentation(file_path)
            slides_md = []
            for i, slide in enumerate(prs.slides):
                slide_md = f"## Slide {i+1}\n"
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        slide_md += shape.text + "\n"
                slides_md.append(slide_md)
            return "\n\n".join(slides_md)
        except ImportError:
            return "python-pptx is not installed."
    else:
        raise ValueError("Only file:// URIs are currently supported.")

@mcp.tool()
async def read_word_file(uri: str) -> str:
    """
    Read the content of a Word file (.docx) and return as markdown.
    Supports file:// URIs.
    """
    import os
    if uri.startswith("file://"):
        file_path = uri[7:]
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        try:
            import docx
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except ImportError:
            return "python-docx is not installed."
    else:
        raise ValueError("Only file:// URIs are currently supported.")

@mcp.tool()
async def read_other_files(uri: str) -> str:
    """
    Read the content of other files (plain text, csv, etc.) and return as markdown.
    Supports file:// URIs.
    """
    import os
    if uri.startswith("file://"):
        file_path = uri[7:]
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error reading file: {e}"
    else:
        raise ValueError("Only file:// URIs are currently supported.")

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    sse = SseServerTransport("/messages/")
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        event_store=None,
        json_response=True,
        stateless=True,
    )

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            print("Application started with StreamableHTTP session manager!")
            try:
                yield
            finally:
                print("Application shutting down...")

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/mcp", app=handle_streamable_http),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        lifespan=lifespan,
    )

def main():
    import argparse

    mcp_server = mcp._mcp_server

    parser = argparse.ArgumentParser(description="Run a read-office-documents MCP server")

    parser.add_argument(
        "--http",
        action="store_true",
        help="Run the server with Streamable HTTP and SSE transport rather than STDIO (default: False)",
    )
    parser.add_argument(
        "--sse",
        action="store_true",
        help="(Deprecated) An alias for --http (default: False)",
    )
    parser.add_argument(
        "--host", default=None, help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=None, help="Port to listen on (default: 3001)"
    )
    args = parser.parse_args()

    use_http = args.http or args.sse

    if not use_http and (args.host or args.port):
        parser.error(
            "Host and port arguments are only valid when using streamable HTTP or SSE transport (see: --http)."
        )
        sys.exit(1)

    if use_http:
        starlette_app = create_starlette_app(mcp_server, debug=True)
        uvicorn.run(
            starlette_app,
            host=args.host if args.host else "127.0.0.1",
            port=args.port if args.port else 3001,
        )
    else:
        mcp.run()

if __name__ == "__main__":
    main()
