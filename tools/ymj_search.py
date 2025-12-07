#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["fastembed", "numpy"]
# ///
#
# ymj_search.py - Semantic search across YMJ files
#
# Usage:
#   uv run ymj_search.py "search query" ./docs/
#   uv run ymj_search.py "search query" ./docs/ --top 5
#   uv run ymj_search.py "search query" ./docs/ --gpu
#

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def extract_embedding(content: str) -> list[float] | None:
    """Extract embedding from YMJ file content."""
    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    if not json_match:
        return None
    
    try:
        data = json.loads(json_match.group(1))
        return data.get("index", {}).get("embedding")
    except json.JSONDecodeError:
        return None


def embed_query(query: str, use_gpu: bool = False) -> np.ndarray:
    """Generate embedding for search query."""
    from fastembed import TextEmbedding
    
    providers = ["CUDAExecutionProvider"] if use_gpu else None
    model = TextEmbedding(
        model_name="nomic-ai/nomic-embed-text-v1.5",
        providers=providers
    )
    
    return list(model.embed([query]))[0]


def search(query: str, directory: Path, top_k: int = 10, use_gpu: bool = False):
    """Search YMJ files in directory."""
    print(f"Searching: {query}\n", file=sys.stderr)
    
    query_embedding = embed_query(query, use_gpu)
    
    results = []
    for path in directory.rglob("*.ymj"):
        content = path.read_text(encoding="utf-8")
        embedding = extract_embedding(content)
        
        if embedding is None:
            continue
        
        score = cosine_similarity(query_embedding, np.array(embedding))
        results.append((path, score))
    
    results.sort(key=lambda x: -x[1])
    
    for path, score in results[:top_k]:
        print(f"[{score:.3f}] {path}")


def main():
    parser = argparse.ArgumentParser(description="Search YMJ files semantically")
    parser.add_argument("query", help="Search query")
    parser.add_argument("directory", type=Path, help="Directory to search")
    parser.add_argument("--top", type=int, default=10, help="Number of results")
    parser.add_argument("--gpu", action="store_true", help="Use GPU acceleration")
    
    args = parser.parse_args()
    search(args.query, args.directory, args.top, args.gpu)


if __name__ == "__main__":
    main()
