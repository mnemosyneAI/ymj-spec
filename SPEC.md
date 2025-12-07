# YMJ Format Specification v1.0

**Status:** Stable  
**Version:** 1.0.0  
**Date:** 2025-12-06  
**Author:** mnemosyneAI

---

## Abstract

YMJ (YAML-Markdown-JSON) is a document format designed for semantic search without external infrastructure. Each document carries its own embedding vector, enabling "file-carried RAG" - retrieval-augmented generation that works with just files.

## 1. Introduction

### 1.1 Problem Statement

Modern RAG (Retrieval-Augmented Generation) systems require:
- A document store
- A vector database
- Synchronization infrastructure
- Query routing between systems

This architecture introduces failure modes, maintenance burden, and portability issues.

### 1.2 Solution

YMJ embeds the semantic index directly in the document. The file IS the searchable unit. No external dependencies.

### 1.3 Design Goals

1. **Self-contained** - All information needed for search lives in the file
2. **Human-readable** - Standard text formats throughout
3. **Tool-friendly** - Works with grep, git, standard editors
4. **Portable** - Copy file = copy functionality
5. **Extensible** - Custom metadata without breaking compatibility

## 2. File Structure

### 2.1 Overview

A YMJ file consists of three consecutive sections:

```
┌─────────────────────┐
│   YAML Front Matter │  Section 1: Metadata
├─────────────────────┤
│   Markdown Body     │  Section 2: Content
├─────────────────────┤
│   JSON Code Block   │  Section 3: Index
└─────────────────────┘
```

### 2.2 Section 1: YAML Front Matter

**REQUIRED**

Begins and ends with `---` delimiters.

```yaml
---
doc_type: <string>       # REQUIRED - Document classification
title: <string>          # REQUIRED - Human-readable title
created: <date>          # RECOMMENDED - ISO 8601 date
updated: <date>          # OPTIONAL - Last modification date
tags: [<string>, ...]    # OPTIONAL - Categorization tags
relates_to: [<id>, ...]  # OPTIONAL - Related document/entry IDs
maintained_by: <string>  # OPTIONAL - Author/owner identifier
version: <string>        # OPTIONAL - Document version
<custom>: <any>          # OPTIONAL - Application-specific fields
---
```

#### 2.2.1 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `doc_type` | string | Document classification (e.g., "knowledge", "reference", "story") |
| `title` | string | Human-readable document title |

#### 2.2.2 Recommended Fields

| Field | Type | Description |
|-------|------|-------------|
| `created` | date | Creation date in ISO 8601 format (YYYY-MM-DD) |
| `tags` | array | List of categorization strings |

#### 2.2.3 Optional Standard Fields

| Field | Type | Description |
|-------|------|-------------|
| `updated` | date | Last modification date |
| `relates_to` | array | IDs of related documents or entries |
| `maintained_by` | string | Author or owner identifier |
| `version` | string | Document version string |
| `kind` | string | Sub-classification within doc_type |
| `subject` | string | Topic or subject description |

### 2.3 Section 2: Markdown Body

**REQUIRED**

Standard GitHub-Flavored Markdown (GFM). No restrictions on content.

The body begins immediately after the closing `---` of the YAML header and continues until either:
- The JSON code block (Section 3), or
- End of file

### 2.4 Section 3: JSON Index Block

**OPTIONAL** (but required for semantic search)

A fenced code block with `json` language identifier containing the semantic index.

~~~markdown
```json
{
  "schema": <integer>,
  "index": {
    "tags": [<string>, ...],
    "title": <string>,
    "embedding": [<float>, ...]
  },
  "meta": { ... }
}
```
~~~

#### 2.4.1 Index Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema` | integer | Yes | Schema version (currently 1) |
| `index.tags` | array | No | Copy of YAML tags for search |
| `index.title` | string | No | Normalized title for matching |
| `index.embedding` | array | Yes | Float vector embedding |
| `meta` | object | No | Application-specific metadata |

#### 2.4.2 Embedding Specification

- **Dimensions:** 768 (for nomic-embed-text-v1.5) or as appropriate for chosen model
- **Type:** Array of IEEE 754 floating-point numbers
- **Source:** Generated from concatenation of YAML metadata and Markdown body
- **Model:** Recommended: `nomic-ai/nomic-embed-text-v1.5`

## 3. Processing Rules

### 3.1 Parsing

1. Read file as UTF-8 text
2. Verify first line is `---`
3. Find closing `---` to extract YAML
4. Parse YAML using standard YAML 1.2 parser
5. Find JSON code block (if present) using regex: `` ```json\n(.*?)\n``` ``
6. Content between YAML and JSON block is Markdown body

### 3.2 Embedding Generation

1. Concatenate YAML header (as string) with Markdown body
2. Generate embedding using chosen model
3. Store in `index.embedding` field
4. Update `schema` version if format changes

### 3.3 Search

1. Generate query embedding using same model
2. For each YMJ file:
   - Extract `index.embedding`
   - Calculate cosine similarity with query
3. Rank by similarity score
4. Return top-k results

## 4. Compatibility

### 4.1 Forward Compatibility

- Parsers MUST ignore unknown fields in YAML header
- Parsers MUST ignore unknown fields in JSON index
- Schema version allows for future extensions

### 4.2 Backward Compatibility

- Schema version 1 files will remain valid
- Future versions will document migration paths

### 4.3 Graceful Degradation

Files without JSON index block are valid YMJ files but cannot be semantically searched. They retain full human readability.

## 5. Security Considerations

### 5.1 YAML Parsing

Use safe YAML loading to prevent code execution:
```python
yaml.safe_load(content)  # NOT yaml.load()
```

### 5.2 JSON Parsing

Standard JSON parsing has no execution risks.

### 5.3 Embedding Models

Embedding generation is computationally intensive. Consider rate limiting for batch operations.

## 6. Examples

### 6.1 Minimal Valid File

```yaml
---
doc_type: note
title: Minimal Example
---

This is a minimal YMJ file.
```

### 6.2 Complete File with Index

```yaml
---
doc_type: knowledge
title: Complete Example
created: 2025-01-01
tags: [example, documentation]
relates_to: [other_doc_id]
---

# Complete Example

This file demonstrates all features of the YMJ format.

## Content

Your markdown content goes here.
```

```json
{
  "schema": 1,
  "index": {
    "tags": ["example", "documentation"],
    "title": "complete_example",
    "embedding": [0.123, -0.456, 0.789, ...]
  }
}
```

## 7. Reference Implementation

See [mnemosyne-memory](https://github.com/mnemosyneAI/mnemosyne-memory) for a complete implementation of YMJ handling.

## 8. Changelog

### v1.0.0 (2025-12-06)
- Initial specification release

---

## Appendix A: MIME Type

Suggested MIME type: `text/x-ymj`

## Appendix B: File Extension

Standard extension: `.ymj`

## Appendix C: Embedding Model Compatibility

| Model | Dimensions | Notes |
|-------|------------|-------|
| nomic-ai/nomic-embed-text-v1.5 | 768 | Recommended |
| BAAI/bge-small-en-v1.5 | 384 | Lightweight alternative |
| sentence-transformers/all-MiniLM-L6-v2 | 384 | Popular alternative |

Implementations SHOULD document which model was used for embeddings.
