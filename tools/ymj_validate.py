#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
#
# ymj_validate.py - Validate YMJ file structure
#
# Usage:
#   uv run ymj_validate.py file.ymj
#   uv run ymj_validate.py *.ymj
#   uv run ymj_validate.py --strict file.ymj  # Also check embedding presence
#

import argparse
import json
import re
import sys
from pathlib import Path

import yaml


def validate_file(path: Path, strict: bool = False) -> list[str]:
    """Validate a YMJ file. Returns list of errors."""
    errors = []
    
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Cannot read file: {e}"]
    
    # Check YAML header
    if not content.startswith("---"):
        errors.append("Missing YAML header (must start with ---)")
        return errors
    
    header_end = content.find("---", 3)
    if header_end == -1:
        errors.append("Unclosed YAML header (missing closing ---)")
        return errors
    
    # Parse YAML
    yaml_content = content[3:header_end].strip()
    try:
        header = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML: {e}")
        return errors
    
    if not isinstance(header, dict):
        errors.append("YAML header must be a mapping (dictionary)")
        return errors
    
    # Check required fields
    if "doc_type" not in header:
        errors.append("Missing required field: doc_type")
    if "title" not in header:
        errors.append("Missing required field: title")
    
    # Check JSON footer
    rest = content[header_end + 3:]
    json_match = re.search(r'```json\s*\n(.*?)\n```', rest, re.DOTALL)
    
    if json_match:
        try:
            footer = json.loads(json_match.group(1))
            
            if "schema" not in footer:
                errors.append("JSON index missing 'schema' field")
            if "index" not in footer:
                errors.append("JSON index missing 'index' field")
            elif "embedding" not in footer.get("index", {}):
                if strict:
                    errors.append("JSON index missing embedding (strict mode)")
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in footer: {e}")
    elif strict:
        errors.append("Missing JSON index block (strict mode)")
    
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate YMJ file structure")
    parser.add_argument("files", nargs="+", type=Path, help="YMJ files to validate")
    parser.add_argument("--strict", action="store_true", 
                       help="Require embedding to be present")
    
    args = parser.parse_args()
    
    all_valid = True
    for path in args.files:
        if path.suffix != ".ymj":
            print(f"⚠ {path}: Not a .ymj file, skipping")
            continue
        
        errors = validate_file(path, args.strict)
        
        if errors:
            print(f"✗ {path}:")
            for error in errors:
                print(f"  - {error}")
            all_valid = False
        else:
            print(f"✓ {path}: Valid")
    
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
