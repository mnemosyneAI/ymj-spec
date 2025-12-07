#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["fastembed", "numpy", "pyyaml"]
# ///
#
# ymj_embed.py - Generate or update embeddings for YMJ files
#
# Usage:
#   uv run ymj_embed.py file.ymj           # Embed single file
#   uv run ymj_embed.py *.ymj              # Embed multiple files
#   uv run ymj_embed.py --gpu file.ymj     # Use GPU acceleration
#

import argparse
import json
import re
import sys
from pathlib import Path

import yaml


def parse_ymj(content: str) -> tuple[dict, str, dict | None]:
    """Parse YMJ file into components."""
    # Extract YAML header
    if not content.startswith("---"):
        raise ValueError("Missing YAML header")
    
    header_end = content.find("---", 3)
    if header_end == -1:
        raise ValueError("Unclosed YAML header")
    
    yaml_content = content[3:header_end].strip()
    header = yaml.safe_load(yaml_content)
    
    # Extract JSON footer if present
    rest = content[header_end + 3:]
    json_match = re.search(r'```json\s*\n(.*?)\n```', rest, re.DOTALL)
    
    if json_match:
        footer = json.loads(json_match.group(1))
        markdown = rest[:json_match.start()].strip()
    else:
        footer = None
        markdown = rest.strip()
    
    return header, markdown, footer


def embed_text(text: str, use_gpu: bool = False) -> list[float]:
    """Generate embedding for text."""
    from fastembed import TextEmbedding
    
    providers = ["CUDAExecutionProvider"] if use_gpu else None
    model = TextEmbedding(
        model_name="nomic-ai/nomic-embed-text-v1.5",
        providers=providers
    )
    
    return list(model.embed([text]))[0].tolist()


def process_file(path: Path, use_gpu: bool = False, force: bool = False) -> bool:
    """Process a single YMJ file."""
    content = path.read_text(encoding="utf-8")
    
    try:
        header, markdown, footer = parse_ymj(content)
    except ValueError as e:
        print(f"Error parsing {path}: {e}", file=sys.stderr)
        return False
    
    # Check if already embedded
    if footer and "index" in footer and "embedding" in footer["index"] and not force:
        print(f"Skipping {path} (already embedded, use --force to re-embed)")
        return True
    
    # Generate embedding from full content
    full_text = yaml.dump(header) + "\n" + markdown
    print(f"Embedding {path}...", end=" ", flush=True)
    
    embedding = embed_text(full_text, use_gpu)
    
    # Create or update footer
    new_footer = {
        "schema": 1,
        "index": {
            "tags": header.get("tags", []),
            "title": header.get("title", path.stem),
            "embedding": embedding
        }
    }
    
    # Rebuild file
    yaml_section = "---\n" + yaml.dump(header, default_flow_style=False) + "---\n"
    json_section = "\n```json\n" + json.dumps(new_footer, indent=2) + "\n```\n"
    
    new_content = yaml_section + "\n" + markdown + json_section
    path.write_text(new_content, encoding="utf-8")
    
    print("done")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for YMJ files")
    parser.add_argument("files", nargs="+", type=Path, help="YMJ files to process")
    parser.add_argument("--gpu", action="store_true", help="Use GPU acceleration")
    parser.add_argument("--force", action="store_true", help="Re-embed even if already done")
    
    args = parser.parse_args()
    
    success = 0
    for path in args.files:
        if path.suffix != ".ymj":
            print(f"Skipping {path} (not a .ymj file)")
            continue
        if process_file(path, args.gpu, args.force):
            success += 1
    
    print(f"\nProcessed {success}/{len(args.files)} files")


if __name__ == "__main__":
    main()
