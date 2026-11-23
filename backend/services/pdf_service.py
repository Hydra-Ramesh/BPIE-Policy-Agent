import os
import hashlib
from typing import List, Dict, Any
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class PDFService:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )

    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA-256 hash of a file for integrity check.
        """
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def extract_and_chunk(self, file_path: str, document_title: str) -> List[Dict[str, Any]]:
        """
        Extract text from each page of a PDF and split into chunks with page metadata.
        Returns a list of dicts:
        [
          {
            "text": "...",
            "metadata": {
              "document_title": "...",
              "page": 1,
              "chunk_index": 0
            }
          }
        ]
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        reader = PdfReader(file_path)
        chunks_with_metadata = []
        global_chunk_idx = 0

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if not text:
                continue

            # Split text on this page
            page_chunks = self.text_splitter.split_text(text)
            for idx, chunk_text in enumerate(page_chunks):
                if not chunk_text.strip():
                    continue

                chunks_with_metadata.append({
                    "text": chunk_text.strip(),
                    "metadata": {
                        "document_title": document_title,
                        "page": page_num,
                        "chunk_index": global_chunk_idx,
                        "page_chunk_index": idx
                    }
                })
                global_chunk_idx += 1

        return chunks_with_metadata
