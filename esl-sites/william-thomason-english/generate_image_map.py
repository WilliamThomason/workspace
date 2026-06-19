"""
generate_image_map.py
Scans Sliding In Images/ folder and creates sliding-in-image-map.json
mapping each topic slug + question index to its local image file.
Also generates ATTRIBUTION.md with proper credits.
"""
import json, os, glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "Sliding In Images")
PROGRESS_FILE = os.path.join(BASE_DIR, "download_progress.json")
MAP_FILE = os.path.join(BASE_DIR, "sliding-in-image-map.json")
ATTRIBUTION_FILE = os.path.join(IMAGE_DIR, "ATTRIBUTION.md")
KEYWORDS_FILE = os.path.join(BASE_DIR, "keywords.json")

def generate_image_map():
    """Build the image map from downloaded files."""
    image_map = {}
    
    # Scan for all jpg files matching {slug}_{index}.jpg pattern
    for filepath in glob.glob(os.path.join(IMAGE_DIR, "*.jpg")):
        filename = os.path.basename(filepath)
        name = filename.replace(".jpg", "")
        
        # Parse slug and index from filename
        # Format: {slug}_{qindex} — but slugs can have underscores
        # Strategy: find the last underscore followed by a number
        parts = name.rsplit("_", 1)
        if len(parts) == 2 and parts[1].isdigit():
            slug = parts[0]
            q_index = parts[1]
            
            if slug not in image_map:
                image_map[slug] = {}
            image_map[slug][q_index] = f"Sliding In Images/{filename}"
    
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(image_map, f, indent=2, ensure_ascii=False)
    
    total = sum(len(v) for v in image_map.values())
    print(f"Image map: {len(image_map)} topics, {total} images → {MAP_FILE}")
    return image_map

def generate_attribution():
    """Generate ATTRIBUTION.md from download progress data."""
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            progress = json.load(f)
    
    keywords = []
    if os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
            keywords = json.load(f)
    
    # Build lookup: key -> question text
    question_lookup = {}
    for k in keywords:
        key = f"{k['topic_slug']}_{k['q_index']}"
        question_lookup[key] = k["question"]
    
    # Group by source
    unsplash_entries = []
    pixabay_entries = []
    no_attribution = []
    
    for key, data in sorted(progress.items()):
        attr = data.get("attribution", {})
        source = attr.get("source", "Unknown")
        entry = {
            "key": key,
            "file": data.get("file", ""),
            "keyword": attr.get("keyword", ""),
            "question": question_lookup.get(key, ""),
            "photographer": attr.get("photographer", "Unknown"),
            "photographer_url": attr.get("photographer_url", ""),
            "photo_url": attr.get("photo_url", "")
        }
        
        if source == "Unsplash":
            unsplash_entries.append(entry)
        elif source == "Pixabay":
            pixabay_entries.append(entry)
        else:
            no_attribution.append(entry)
    
    # Write attribution file
    lines = [
        "# Image Attribution for Sliding In",
        "",
        "This file credits all photographers whose images are used in the",
        "Sliding In ESL question deck.",
        "",
        f"**Total images:** {len(progress)}",
        f"**Unsplash:** {len(unsplash_entries)}",
        f"**Pixabay:** {len(pixabay_entries)}",
        "",
        "---",
        "",
        "## Unsplash Images",
        "",
        "Images sourced from [Unsplash](https://unsplash.com).",
        "License: [Unsplash License](https://unsplash.com/license) — free to use,",
        "attribution appreciated but not required. Photographer credits provided below.",
        "",
    ]
    
    for e in unsplash_entries:
        lines.append(f"### {e['key']} — \"{e['keyword']}\"")
        lines.append(f"- **Question:** {e['question'][:80]}")
        lines.append(f"- **Photographer:** [{e['photographer']}]({e['photographer_url']})")
        lines.append(f"- **Photo:** [View on Unsplash]({e['photo_url']})")
        lines.append(f"- **File:** `{e['file']}`")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "## Pixabay Images",
        "",
        "Images sourced from [Pixabay](https://pixabay.com).",
        "License: [Pixabay Content License](https://pixabay.com/service/license-summary/) —",
        "free for commercial use, attribution not required but appreciated.",
        "",
    ])
    
    for e in pixabay_entries:
        lines.append(f"### {e['key']} — \"{e['keyword']}\"")
        lines.append(f"- **Question:** {e['question'][:80]}")
        lines.append(f"- **Photographer:** [{e['photographer']}]({e['photographer_url']})")
        lines.append(f"- **Photo:** [View on Pixabay]({e['photo_url']})")
        lines.append(f"- **File:** `{e['file']}`")
        lines.append("")
    
    if no_attribution:
        lines.extend([
            "---",
            "",
            "## Images Without Attribution Data",
            "",
            "These images were downloaded but source/photographer data was not recorded.",
            "",
        ])
        for e in no_attribution:
            lines.append(f"- `{e['file']}` — keyword: \"{e['keyword']}\"")
        lines.append("")
    
    with open(ATTRIBUTION_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"Attribution: {len(unsplash_entries)} Unsplash + {len(pixabay_entries)} Pixabay → {ATTRIBUTION_FILE}")

def main():
    print("Generating image map...")
    generate_image_map()
    print()
    print("Generating attribution file...")
    generate_attribution()
    print()
    print("Done!")

if __name__ == "__main__":
    main()
