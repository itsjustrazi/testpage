#!/usr/bin/env python3
"""
Run this script to regenerate listings.json from _data/subsales/*.md
Usage: python3 generate-listings.py
Netlify will run this as build command if configured.
"""
import os, json, re
from pathlib import Path

listings = []
subsales_dir = Path("_data/subsales")

for md_file in sorted(subsales_dir.glob("*.md")):
    content = md_file.read_text(encoding="utf-8")
    # Extract frontmatter
    parts = content.split("---")
    if len(parts) < 3:
        continue
    fm_text = parts[1]
    
    # Simple YAML-like parse (safe for our format)
    import yaml
    try:
        data = yaml.safe_load(fm_text)
        data["slug"] = md_file.stem
        listings.append(data)
    except Exception as e:
        print(f"ERROR parsing {md_file.name}: {e}")
        continue

# Sort by date desc
listings.sort(key=lambda x: str(x.get("tarikh", "")), reverse=True)

output = {"listings": listings, "total": len(listings)}
with open("listings.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

print(f"Generated listings.json with {len(listings)} listings")
