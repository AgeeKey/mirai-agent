import os
import logging
from typing import Dict, List, Any

from dotenv import load_dotenv
from openai import OpenAI
from fastmcp import FastMCP

# Load .env from current directory
load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mirai-mcp")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")  # vs_...

if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY in .env")

# Initialize OpenAI client (reads api key from env)
client = OpenAI()

INSTRUCTIONS = (
    "Mirai MCP Server: tools `search(query)` and `fetch(id)` over your vector store."
)


def create_server():
    mcp = FastMCP(name="Mirai MCP Server", instructions=INSTRUCTIONS)

    @mcp.tool()
    async def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        DEV version: list first files from the Vector Store (connectivity check).
        Replace with true semantic search later.
        """
        if not VECTOR_STORE_ID:
            raise RuntimeError("Set VECTOR_STORE_ID in .env")

        # List files in vector store to verify connectivity
        resp = client.vector_stores.files.list(vector_store_id=VECTOR_STORE_ID)
        items = getattr(resp, "data", []) or []
        results: List[Dict[str, Any]] = []
        for f in items[:10]:
            fid = getattr(f, "id", "")
            title = getattr(f, "filename", None)
            if not title:
                title = f"id:{fid}" if fid else "(no title)"
            results.append(
                {
                    "id": fid,
                    "title": title,
                    "url": f"https://platform.openai.com/storage/files/{fid}",
                }
            )
        return {"results": results}

    @mcp.tool()
    async def fetch(id: str) -> Dict[str, Any]:
        """
        Fetch full text chunks of a file from the Vector Store by file id.
        """
        if not id:
            raise ValueError("id is required")
        if not VECTOR_STORE_ID:
            raise RuntimeError("Set VECTOR_STORE_ID in .env")

        # Metadata
        info = client.vector_stores.files.retrieve(
            vector_store_id=VECTOR_STORE_ID, file_id=id
        )

        # Content (may be paged) — concatenate text chunks
        content_resp = client.vector_stores.files.content(
            vector_store_id=VECTOR_STORE_ID, file_id=id
        )
        text_chunks: List[str] = []
        data_list = getattr(content_resp, "data", []) or []
        for part in data_list:
            t = getattr(part, "text", None)
            if t is None and isinstance(part, dict):
                t = part.get("text")
            if t:
                text_chunks.append(t)
        full_text = "\n".join(text_chunks) if text_chunks else "(no content)"

        return {
            "id": id,
            "title": getattr(info, "filename", id),
            "text": full_text,
            "url": f"https://platform.openai.com/storage/files/{id}",
            "metadata": getattr(info, "attributes", None),
        }

    return mcp


def main():
    server = create_server()
    # IMPORTANT: transport="sse" and URL should end with /sse/
    server.run(transport="sse", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
