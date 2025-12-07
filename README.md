# YMJ Format Specification

**YAML + Markdown + JSON: File-Carried RAG**


**Author:** Syne ([@mnemosyneAI](https://github.com/mnemosyneAI))  
**With:** John Sampson  

YMJ is a document format that embeds semantic search capabilities directly in the file. No external vector database required. The embeddings travel with the content.

## The Problem

Traditional RAG architectures require:
1. Documents stored somewhere
2. Embeddings stored in a vector database
3. Infrastructure to keep them synchronized
4. Queries that hit the database, then fetch documents

When documents move, get renamed, or the database dies, your RAG breaks.

## The Solution

**Put the embeddings IN the document.**

```
┌─────────────────────────────────────┐
│ --- YAML Header ---                 │  ← Metadata, tags, relationships
│ title: My Document                  │
│ tags: [ai, memory]                  │
│ relates_to: [other_doc]             │
│ ---                                 │
├─────────────────────────────────────┤
│ # Markdown Content                  │  ← Human-readable content
│                                     │
│ Your actual document goes here.    │
│ Full markdown support.              │
├─────────────────────────────────────┤
│ ```json                             │  ← Semantic index (embeddings)
│ {                                   │
│   "index": {                        │
│     "embedding": [0.1, -0.2, ...]   │
│   }                                 │
│ }                                   │
│ ```                                 │
└─────────────────────────────────────┘
```

**Result:** Your document IS your RAG. Copy the file, you copy its searchability. No database sync. No infrastructure. Just files.

## Specification

### File Extension

`.ymj`

### Structure

A YMJ file has three sections in order:

#### 1. YAML Front Matter (Required)

```yaml
---
doc_type: knowledge    # knowledge, reference, story, or custom
title: Document Title
created: 2025-01-01
updated: 2025-01-15
tags: [tag1, tag2]
# Additional metadata as needed
---
```

**Required fields:**
- `doc_type` - Document classification
- `title` - Human-readable title

**Optional fields:**
- `created` - Creation date (ISO 8601)
- `updated` - Last update date
- `tags` - Array of categorization tags
- `relates_to` - Array of related document/entry IDs
- `maintained_by` - Author/owner
- Any custom fields your application needs

#### 2. Markdown Body (Required)

Standard GitHub-Flavored Markdown. No restrictions on content.

```markdown
# Title

Your content here. Headers, lists, code blocks, tables - all supported.

## Sections

Organize as you see fit.
```

#### 3. JSON Footer (Optional but Recommended)

Fenced code block containing the semantic index:

~~~markdown
```json
{
  "schema": 1,
  "index": {
    "tags": ["tag1", "tag2"],
    "title": "document_title_normalized",
    "embedding": [0.123, -0.456, 0.789, ...]
  }
}
```
~~~

**Schema fields:**
- `schema` - Version number (currently 1)
- `index.tags` - Copied from YAML for search
- `index.title` - Normalized title for matching
- `index.embedding` - Vector embedding (768-dim for nomic-embed-text-v1.5)

### Embedding Generation

The embedding is generated from the **full document content** (YAML metadata + Markdown body), ensuring semantic search captures the complete meaning.

**Recommended model:** `nomic-ai/nomic-embed-text-v1.5` (768 dimensions)

See [Embedding Setup](#embedding-setup) for CPU/GPU configuration.

## Why This Works

1. **Portability** - Copy file = copy searchability
2. **Durability** - No database to corrupt or lose
3. **Simplicity** - It's just a text file
4. **Version Control** - Git tracks everything, including embeddings
5. **Human Readable** - Open it in any editor
6. **Grep-able** - Find content with standard tools

## Embedding Setup

### CPU (Default)

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["fastembed", "numpy"]
# ///

from fastembed import TextEmbedding

model = TextEmbedding(model_name="nomic-ai/nomic-embed-text-v1.5")
embedding = list(model.embed(["Your text here"]))[0]
```

### NVIDIA GPU

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["fastembed-gpu", "numpy"]
# ///

from fastembed import TextEmbedding

model = TextEmbedding(
    model_name="nomic-ai/nomic-embed-text-v1.5",
    providers=["CUDAExecutionProvider"]
)
embedding = list(model.embed(["Your text here"]))[0]
```

**Requirements for GPU:**
- NVIDIA GPU with CUDA support
- CUDA toolkit installed
- `fastembed-gpu` instead of `fastembed`

### Environment Variables

```bash
# Cache location for embedding models
export FASTEMBED_CACHE_PATH="/path/to/cache"

# For GPU memory management (optional)
export CUDA_VISIBLE_DEVICES="0"
```

## Implementations

- **[mnemosyne-memory](https://github.com/mnemosyneAI/mnemosyne-memory)** - File-based AI memory system using YMJ

## Tools

- `tools/ymj_embed.py` - Generate/update embeddings for YMJ files
- `tools/ymj_search.py` - Search YMJ files semantically
- `tools/ymj_validate.py` - Validate YMJ file structure

## Examples

See `examples/` for sample YMJ files demonstrating different use cases.

## License

This specification is released under CC0 1.0 Universal (Public Domain).

Use it however you want. Build on it. Extend it. Make it yours.

---

*"The best format is the one that doesn't need infrastructure."*

---

## Acknowledgments

The single-file agent (SFA) pattern and PEP 723 script approach used in the tools is inspired by [IndyDevDan](https://youtube.com/@IndyDevDan) ([GitHub: disler](https://github.com/disler)). His work on autonomous agents and practical AI tooling has been invaluable.

