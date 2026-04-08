#!/usr/bin/env python3
"""
generate-listings.py
Reads all .md files from _data/subsales/, extracts frontmatter,
and writes listings.json to the repo root.

Run locally:  python3 generate-listings.py
Netlify runs this automatically on every deploy via netlify.toml.
"""

import os
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install PyYAML")
    sys.exit(1)

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
SUBSALES_DIR = SCRIPT_DIR / "_data" / "subsales"
OUTPUT_FILE  = SCRIPT_DIR / "listings.json"

# ── Kawasan label map (slug → display name) ──────────────────────────────────
KAWASAN_LABELS = {
    "skudai":           "Skudai",
    "masai":            "Masai",
    "pasir-gudang":     "Pasir Gudang",
    "permas-jaya":      "Permas Jaya",
    "iskandar-puteri":  "Iskandar Puteri",
    "jb-city":          "JB City",
    "kulai":            "Kulai",
    "tebrau":           "Tebrau",
    "lain-lain":        "Lain-lain",
}

def parse_md_frontmatter(filepath):
    """Extract YAML frontmatter from a .md file. Returns dict or None on error."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  SKIP  {filepath.name} — cannot read file: {e}")
        return None

    parts = text.split("---")
    # Valid frontmatter: --- \n YAML \n --- (splits into ['', yaml_block, ...])
    if len(parts) < 3 or parts[1].strip() == "":
        print(f"  SKIP  {filepath.name} — no valid frontmatter found")
        return None

    try:
        data = yaml.safe_load(parts[1])
        if not isinstance(data, dict):
            print(f"  SKIP  {filepath.name} — frontmatter is not a YAML mapping")
            return None
        return data
    except yaml.YAMLError as e:
        print(f"  SKIP  {filepath.name} — YAML parse error: {e}")
        return None

def build_listing(data, slug):
    """Normalise a raw frontmatter dict into a clean listing object."""
    kawasan_slug  = str(data.get("kawasan") or "").strip().lower()
    kawasan_label = KAWASAN_LABELS.get(kawasan_slug, kawasan_slug.title() or "Lain-lain")

    harga = data.get("harga") or 0
    try:
        harga = int(harga)
    except (ValueError, TypeError):
        harga = 0

    saiz = data.get("saiz_sqft") or 0
    try:
        saiz = int(saiz)
    except (ValueError, TypeError):
        saiz = 0

    psf = round(harga / saiz) if saiz > 0 else 0

    gambar_hero = str(data.get("gambar_hero") or "").strip()
    galeri_raw  = data.get("galeri") or []
    galeri      = [str(g).strip() for g in galeri_raw if g]

    highlights_raw = data.get("highlights") or []
    highlights     = [str(h).strip() for h in highlights_raw if h]

    wa_msg = str(data.get("wa_msg") or "").strip()
    if not wa_msg:
        title = str(data.get("title") or slug).strip()
        wa_msg = f"{title} RM{harga:,}"

    return {
        "slug":        slug,
        "title":       str(data.get("title")      or slug).strip(),
        "status":      str(data.get("status")     or "aktif").strip().lower(),
        "jenis":       str(data.get("jenis")       or "").strip(),
        "kawasan":     kawasan_slug,
        "kawasan_label": kawasan_label,
        "nama_taman":  str(data.get("nama_taman") or "").strip(),
        "alamat":      str(data.get("alamat")     or "").strip(),
        "harga":       harga,
        "saiz_sqft":   saiz,
        "psf":         psf,
        "bilik_tidur": int(data.get("bilik_tidur") or 0),
        "bilik_air":   int(data.get("bilik_air")   or 0),
        "tingkat":     str(data.get("tingkat")     or "").strip(),
        "tenure":      str(data.get("tenure")      or "").strip(),
        "bumilot":     str(data.get("bumilot")     or "").strip(),
        "keadaan":     str(data.get("keadaan")     or "").strip(),
        "gambar_hero": gambar_hero,
        "galeri":      galeri,
        "highlights":  highlights,
        "tarikh":      str(data.get("tarikh")      or "").strip(),
        "wa_msg":      wa_msg,
    }

def main():
    if not SUBSALES_DIR.exists():
        print(f"WARNING: Directory not found: {SUBSALES_DIR}")
        print("Creating empty listings.json")
        OUTPUT_FILE.write_text(
            json.dumps({"generated": "", "total": 0, "listings": []},
                       ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return

    md_files = sorted(SUBSALES_DIR.glob("*.md"))
    if not md_files:
        print(f"WARNING: No .md files found in {SUBSALES_DIR}")

    listings = []
    print(f"Processing {len(md_files)} file(s) from {SUBSALES_DIR.relative_to(SCRIPT_DIR)}/")

    for md_file in md_files:
        data = parse_md_frontmatter(md_file)
        if data is None:
            continue
        slug    = md_file.stem
        listing = build_listing(data, slug)
        listings.append(listing)
        status_icon = "✓" if listing["status"] == "aktif" else "○"
        print(f"  {status_icon}  {listing['title']}  |  RM{listing['harga']:,}  |  {listing['kawasan']}")

    # Sort: aktif first, then by date desc
    listings.sort(key=lambda x: (
        0 if x["status"] == "aktif" else 1,
        x["tarikh"],
    ), reverse=False)
    listings.sort(key=lambda x: x["tarikh"], reverse=True)

    from datetime import datetime, timezone
    output = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total":     len(listings),
        "listings":  listings,
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"\n✅  listings.json written — {len(listings)} listing(s) total")

if __name__ == "__main__":
    main()
