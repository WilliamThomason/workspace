"""
download_images.py
Downloads one real photo per question keyword from Pexels (primary) + Pixabay (fallback).
Pexels: 200 req/hr free tier. Pixabay: 100 req/min free tier.
Tracks attribution for every image. Resume-safe (skips existing files).

Usage:
    python download_images.py              # Download all missing images
    python download_images.py --pexabay    # Only download via Pixabay
    python download_images.py --verify     # Check which images are still missing
"""
import json, os, sys, subprocess, time, re
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import quote

# ── Config ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_FILE = os.path.join(BASE_DIR, "keywords.json")
PROGRESS_FILE = os.path.join(BASE_DIR, "download_progress.json")
ATTRIBUTION_FILE = os.path.join(BASE_DIR, "Sliding In Images", "ATTRIBUTION.md")
IMAGE_DIR = os.path.join(BASE_DIR, "Sliding In Images")

PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "")

# Pexels rate limit: 200/hr = 1 per 18 seconds
PEXELS_DELAY = 18  # seconds between requests

# ── Helpers ─────────────────────────────────────────────────────────────
def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def download_file(url, dest_path):
    """Download a file using curl (no pip packages needed)."""
    try:
        result = subprocess.run(
            ["curl", "-L", "-s", "--max-time", "30", "-o", dest_path, url],
            capture_output=True, text=True, timeout=35
        )
        if result.returncode == 0 and os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
            return True
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False
    except Exception:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False

def search_pexels(keyword):
    """Search Pexels for a keyword. Returns (image_url, attribution_dict, rate_limited)."""
    if not PEXELS_KEY:
        return None, None, False
    
    encoded = quote(keyword)
    url = f"https://api.pexels.com/v1/search?query={encoded}&per_page=1&orientation=landscape"
    
    try:
        req = Request(url, headers={"Authorization": PEXELS_KEY})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        if data.get("photos"):
            result = data["photos"][0]
            img_url = result["src"]["large2x"]  # 2880px wide, good quality
            attribution = {
                "source": "Pexels",
                "photographer": result["photographer"],
                "photographer_url": result["photographer_url"],
                "photo_url": result["url"],
                "keyword": keyword
            }
            return img_url, attribution, False
        return None, None, False
    except HTTPError as e:
        if e.code == 429:
            return None, None, True  # Rate limited
        return None, None, False
    except Exception as e:
        print(f"    [PEXELS ERROR: {e}]")
        return None, None, False

def search_pixabay(keyword):
    """Search Pixabay for a keyword. Returns (image_url, attribution_dict) or (None, None)."""
    if not PIXABAY_KEY:
        return None, None
    
    encoded = quote(keyword)
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={encoded}&image_type=photo&orientation=horizontal&per_page=3&safesearch=true"
    
    try:
        with urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        if data.get("hits"):
            result = data["hits"][0]
            img_url = result["largeImageURL"]
            attribution = {
                "source": "Pixabay",
                "photographer": result.get("user", "Unknown"),
                "photographer_url": f"https://pixabay.com/users/{result.get('user', 'unknown')}-{result.get('user_id', 0)}/",
                "photo_url": result["pageURL"],
                "keyword": keyword
            }
            return img_url, attribution
        return None, None
    except Exception as e:
        print(f"    [PIXABAY ERROR: {e}]")
        return None, None

# ── Main Logic ──────────────────────────────────────────────────────────
def main():
    keywords = load_json(KEYWORDS_FILE)
    progress = load_json(PROGRESS_FILE)
    
    if not keywords:
        print("ERROR: keywords.json not found. Run extract_keywords.py first.")
        return
    
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    # Parse args
    mode = "all"
    if "--pixabay" in sys.argv:
        mode = "pixabay"
    elif "--verify" in sys.argv:
        mode = "verify"
    
    # Build list of what needs downloading
    pending = []
    already_done = 0
    for entry in keywords:
        slug = entry["topic_slug"]
        q_idx = entry["q_index"]
        dest_file = os.path.join(IMAGE_DIR, f"{slug}_{q_idx}.jpg")
        
        if os.path.exists(dest_file) and os.path.getsize(dest_file) > 1000:
            already_done += 1
            continue
        
        pending.append(entry)
    
    print(f"Total questions: {len(keywords)}")
    print(f"Already downloaded: {already_done}")
    print(f"Pending: {len(pending)}")
    print(f"Mode: {mode}")
    print()
    
    if mode == "verify":
        if not pending:
            print("All images present!")
        else:
            print(f"Missing {len(pending)} images:")
            for entry in pending[:20]:
                print(f"  [{entry['topic_slug']}] Q{entry['q_index']}: {entry['keyword']}")
            if len(pending) > 20:
                print(f"  ... and {len(pending) - 20} more")
        return
    
    # Download
    downloaded = 0
    failed = 0
    skipped = 0
    pexels_count = 0
    pixabay_count = 0
    pexels_rate_limited = False
    
    for i, entry in enumerate(pending):
        slug = entry["topic_slug"]
        q_idx = entry["q_index"]
        keyword = entry["keyword"]
        key = f"{slug}_{q_idx}"
        dest_file = os.path.join(IMAGE_DIR, f"{slug}_{q_idx}.jpg")
        
        # Double-check file still doesn't exist
        if os.path.exists(dest_file) and os.path.getsize(dest_file) > 1000:
            skipped += 1
            continue
        
        print(f"[{i+1}/{len(pending)}] [{slug}] Q{q_idx}: \"{keyword}\"", end=" ", flush=True)
        
        img_url = None
        attribution = None
        
        # Try Pexels first (unless pixabay-only mode)
        if mode != "pixabay" and not pexels_rate_limited:
            img_url, attribution, was_rate_limited = search_pexels(keyword)
            if was_rate_limited:
                pexels_rate_limited = True
                print("✗ PEXELS RATE LIMITED → fallback", end=" ")
            elif img_url:
                pexels_count += 1
                print("✓ Pexels", end=" ")
            else:
                print("✗ Pexels", end=" ")
        
        # Fallback to Pixabay
        if not img_url:
            img_url, attribution = search_pixabay(keyword)
            if img_url:
                pixabay_count += 1
                print("✓ Pixabay", end=" ")
            else:
                print("✗ Pixabay", end=" ")
        
        # Download
        if img_url:
            if download_file(img_url, dest_file):
                progress[key] = {
                    "file": f"Sliding In Images/{slug}_{q_idx}.jpg",
                    "attribution": attribution
                }
                save_json(PROGRESS_FILE, progress)
                downloaded += 1
                print(f"→ {os.path.getsize(dest_file)//1024}KB")
            else:
                failed += 1
                print("→ DOWNLOAD FAILED")
        else:
            failed += 1
            print("→ NO IMAGE FOUND")
        
        # Rate limit pacing: Pexels needs 18s between requests
        if not pexels_rate_limited and mode != "pixabay":
            time.sleep(PEXELS_DELAY)
        else:
            time.sleep(0.5)  # Pixabay can handle faster
        
        # Progress save every 10
        if (i + 1) % 10 == 0:
            save_json(PROGRESS_FILE, progress)
            print(f"  --- Progress saved: {downloaded} downloaded, {failed} failed ---")
    
    # Final save
    save_json(PROGRESS_FILE, progress)
    
    print()
    print("=" * 60)
    print(f"DOWNLOAD COMPLETE")
    print(f"  Downloaded: {downloaded}")
    print(f"  Failed: {failed}")
    print(f"  Skipped (already existed): {skipped}")
    print(f"  Pexels: {pexels_count}")
    print(f"  Pixabay: {pixabay_count}")
    print(f"  Total in folder: {len([f for f in os.listdir(IMAGE_DIR) if f.endswith('.jpg')])}")
    print("=" * 60)

if __name__ == "__main__":
    main()
