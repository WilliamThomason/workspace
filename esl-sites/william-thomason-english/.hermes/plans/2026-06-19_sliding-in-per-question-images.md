# Sliding In: Per-Question Real Images from Unsplash + Pixabay

> **For Hermes:** Use `subagent-driven-development` skill to implement this plan task-by-task.

**Goal:** Replace the current Pollinations.ai AI-generated images in `Sliding In.html` with real photographs — one unique image per question — sourced from Unsplash and Pixabay, stored in a local folder, and referenced by keyword-matching.

**Architecture:** A Python script extracts a keyword (noun/verb) from each of the 1,452 questions, searches Unsplash first (50 req/hr free tier), then Pixabay as fallback (100 req/min free tier), downloads one image per question into `Sliding In Images/`, and generates a JSON image map that the HTML's JS reads at runtime. The existing `renderSlide()` function is patched to use the local image map instead of Pollinations URLs.

**Tech Stack:** Python 3.11, `curl` (no pip packages needed), Unsplash API, Pixabay API, JSON.

---

## Current State

- **File:** `Sliding In.html` — 107 topics, 1,452 questions across 12 categories
- **Current images:** Pollinations.ai AI-generated (dynamic URL per question)
- **Existing image folder:** `Sliding In Images/` — 113 existing topic-level JPGs (one per topic, not per question)
- **Keyword extraction:** Already implemented in JS (`extractKeyword()`) — strips question words, picks first 2 meaningful nouns/verbs
- **Color themes:** 7 palettes already implemented, assigned per-topic

## What We Need

1. A keyword for each of 1,452 questions (extracted from question text)
2. One real photo per keyword from Unsplash or Pixabay
3. Images saved to `Sliding In Images/` as `{slug}_{qindex}.jpg`
4. A JSON map: `{ "slug": { "0": "path/to/img.jpg", ... } }` saved as `sliding-in-image-map.json`
5. HTML patched to load local images from the JSON map instead of Pollinations URLs

---

## Workload 1: Extract Keywords from All Questions

**Goal:** Produce a JSON file with every question's keyword, ready for image search.

### Task 1.1: Write keyword extraction script

**Files:**
- Create: `extract_keywords.py` (in project root)

**Implementation:** Read `Sliding In.html`, extract `lessonData` JSON, iterate all questions, run keyword extraction (strip question words, pick first 2 meaningful nouns/verbs with length > 3), output `keywords.json`:

```json
[
  {
    "topic_slug": "age",
    "topic_title": "Age and Ageing (16 questions)",
    "q_index": 0,
    "question": "In your opinion what age is it best to be? Why?",
    "keyword": "best age"
  },
  ...
]
```

**Verification:**
```bash
cd "/c/Users/irieb/Documents/William's Projects/workspace/esl-sites/william-thomason-english"
python extract_keywords.py
# Check output
python -c "import json; d=json.load(open('keywords.json')); print(f'Total: {len(d)}'); print(d[0])"
```
Expected: 1,452 entries, first entry has a sensible keyword like "best age".

---

## Workload 2: Download Images from Unsplash + Pixabay

**Goal:** For each keyword, download one real photo. Use Unsplash first, Pixabay as fallback.

### Task 2.1: Set up API keys

**Files:**
- Modify: `~/.hermes/.env` or create `.env` in project root

**Required keys:**
- `UNSPLASH_ACCESS_KEY` — Get free at https://unsplash.com/developers (50 req/hr demo tier)
- `PIXABAY_API_KEY` — Get free at https://pixabay.com/api/docs/ (100 req/min free tier)

**Verification:**
```bash
echo $UNSPLASH_ACCESS_KEY
echo $PIXABAY_API_KEY
```
Both print non-empty strings.

### Task 2.2: Write image download script

**Files:**
- Create: `download_images.py`

**Algorithm:**
1. Read `keywords.json`
2. For each entry, construct filename: `{slug}_{qindex}.jpg` in `Sliding In Images/`
3. Skip if file already exists (resume support)
4. Search Unsplash: `GET https://api.unsplash.com/search/photos?query={keyword}&per_page=1&orientation=landscape`
   - Use header: `Authorization: Client-ID {UNSPLASH_ACCESS_KEY}`
   - Extract `results[0].urls.regular` (1280px wide)
5. If Unsplash returns 0 results or rate-limited (403), fall back to Pixabay:
   - `GET https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={keyword}&image_type=photo&orientation=horizontal&per_page=1`
   - Extract `hits[0].largeImageURL`
6. Download the image URL to `Sliding In Images/{slug}_{qindex}.jpg` using `curl`
7. Save progress to `download_progress.json` after each image (resume on re-run)
8. Print summary: downloaded X, skipped Y (already existed), failed Z

**Rate limit handling:**
- Unsplash: 50/hr = ~1 per 72 seconds. For 1,452 images, Unsplash alone would take ~29 hours.
- Pixabay: 100/min = much faster. Primary source for bulk downloads.
- **Mixed strategy:**
  - First pass: Unsplash for the first ~50 images (1 hour of API budget) — use for the most visual/concrete topics (e.g., "cooking", "travel", "animals", "cities")
  - Second pass: Pixabay for all remaining images not yet downloaded (~1,400 images, ~25-30 minutes)
  - Track which source was used per image in `download_progress.json`
  - User can re-run Unsplash pass on subsequent days for more quality images (script skips existing files)

**Verification:**
```bash
cd "/c/Users/irieb/Documents/William's Projects/workspace/esl-sites/william-thomason-english"
python download_images.py
# Should start downloading images
ls "Sliding In Images/" | wc -l
# Should grow over time
```

### Task 2.3: Run the download (batch execution)

**This is a long-running task.** 1,452 images at ~1-2 seconds each = 25-50 minutes on Pixabay, or ~29 hours on Unsplash alone.

**Recommended approach:** Run Pixabay as primary source (faster), Unsplash for variety on a subset.

**Verification:**
```bash
ls "Sliding In Images/" | wc -l
# Target: 1,452 new files + 113 existing = ~1,565 total
python -c "
import json, os
progress = json.load(open('download_progress.json'))
print(f'Downloaded: {len(progress)}')
missing = [k for k,v in progress.items() if not os.path.exists(v)]
print(f'Missing files: {len(missing)}')
"
```

---

## Workload 3: Generate Image Map JSON

**Goal:** Create `sliding-in-image-map.json` that maps each topic slug + question index to its local image file.

### Task 3.1: Write image map generator

**Files:**
- Create: `generate_image_map.py`

**Algorithm:**
1. Read `keywords.json`
2. For each entry, check if `Sliding In Images/{slug}_{qindex}.jpg` exists
3. Build nested dict: `{ "slug": { "0": "Sliding In Images/slug_0.jpg", ... } }`
4. Save as `sliding-in-image-map.json`

**Output format:**
```json
{
  "age": {
    "0": "Sliding In Images/age_0.jpg",
    "1": "Sliding In Images/age_1.jpg",
    ...
  },
  "appearance": {
    "0": "Sliding In Images/appearance_0.jpg",
    ...
  }
}
```

**Verification:**
```bash
python generate_image_map.py
python -c "
import json
m = json.load(open('sliding-in-image-map.json'))
total = sum(len(v) for v in m.values())
print(f'Topics: {len(m)}, Total images mapped: {total}')
"
```
Expected: 107 topics, ~1,452 mapped images.

---

## Workload 4: Patch HTML to Use Local Images

**Goal:** Modify `Sliding In.html` to load images from the local JSON map instead of Pollinations.ai URLs.

### Task 4.1: Add image map loading to HTML

**Files:**
- Modify: `Sliding In.html`

**Changes:**
1. Add a `<script>` tag that loads `sliding-in-image-map.json` into `window.localImageMap`
2. Patch `renderSlide()` to use `window.localImageMap[slug][currentIndex]` as the image src
3. Fall back to the existing Pollinations URL if no local image exists (graceful degradation)

**Code to inject (in `<head>` or before closing `</body>`):**
```javascript
// Load local image map
window.localImageMap = {};
fetch('sliding-in-image-map.json')
  .then(r => r.json())
  .then(data => { window.localImageMap = data; })
  .catch(() => console.log('No local image map found'));
```

**Patch to renderSlide():**
Replace the image URL generation:
```javascript
// OLD: var imgUrl = getQuestionImage(q.original, slug, currentIndex);
// NEW:
var imgUrl = (window.localImageMap[slug] && window.localImageMap[slug][currentIndex])
    ? window.localImageMap[slug][currentIndex]
    : getQuestionImage(q.original, slug, currentIndex); // fallback
```

**Verification:**
1. Start local server: `cd "/c/Users/irieb/Documents/William's Projects/workspace/esl-sites/william-thomason-english" && python -m http.server 8000`
2. Open `http://127.0.0.1:8000/Sliding%20In.html` in Brave
3. Navigate through slides — images should be real photos, not AI-generated
4. Check browser console for 404s (missing images)

### Task 4.2: Verify no broken images

**Files:**
- Create: `verify_images.py`

**Algorithm:**
1. Read `sliding-in-image-map.json`
2. For each mapped file, check if it exists on disk
3. Report missing files

**Verification:**
```bash
python verify_images.py
# Expected: "All 1452 images present" or a short list of missing ones
```

---

## Workload 5: Cleanup and Polish

### Task 5.1: Remove Pollinations dependency (optional)

If all 1,452 images are confirmed working, remove the `getQuestionImage()` and `extractKeyword()` functions from the HTML to reduce JS size.

### Task 5.2: Add image attribution file

**Files:**
- Create: `Sliding In Images/ATTRIBUTION.md`

**Contents:** List image sources (Unsplash/Pixabay) per keyword for license compliance. Both require attribution.

### Task 5.3: Git commit

```bash
cd "/c/Users/irieb/Documents/William's Projects/workspace/esl-sites/william-thomason-english"
git add "Sliding In Images/" sliding-in-image-map.json Sliding In.html
git commit -m "feat: add per-question real images from Unsplash/Pixabay"
```

---

## Files Likely to Change

| File | Action |
|------|--------|
| `Sliding In.html` | Patch `renderSlide()` to use local image map |
| `sliding-in-image-map.json` | Create — maps slug+qindex to image path |
| `Sliding In Images/` | Add ~1,452 new JPGs |
| `extract_keywords.py` | Create — keyword extraction script |
| `download_images.py` | Create — image download script |
| `generate_image_map.py` | Create — image map generator |
| `verify_images.py` | Create — verification script |

---

## Risks, Tradeoffs, and Open Questions

- **Unsplash rate limit (50/hr):** Too slow for 1,452 images as primary source. Use Pixabay (100/min) as primary, Unsplash for variety on a subset, or run Unsplash over multiple days.
- **API keys required:** Both Unsplash and Pixabay require free API key registration. The user needs to sign up and provide keys.
- **Keyword quality:** Simple noun/verb extraction may produce generic keywords ("best age", "change appearance"). May need manual curation for best image matches.
- **Image relevance:** Stock photos may not perfectly match abstract ESL discussion topics (e.g., "entitlement", "ageism"). Some keywords may return irrelevant images.
- **License compliance:** Unsplash requires attribution. Pixabay requires attribution for some content. An ATTRIBUTION.md file is needed.
- **Resume support:** The download script must support resume (skip existing files) because 1,452 downloads may take multiple sessions.
- **Fallback strategy:** If an image fails to download or no results found, the existing Pollinations URL serves as graceful fallback.
- **File naming:** `{slug}_{qindex}.jpg` — slugs are from the existing `lessonData` (e.g., "age", "appearance"). Verify no slug collisions.

---

## Suggested Execution Order

1. **Batch 1:** Task 1.1 (extract keywords) → verify `keywords.json` has 1,452 entries
2. **Batch 2:** Task 2.1 (API keys) → Task 2.2 (download script) → Task 2.3 (run download)
3. **Batch 3:** Task 3.1 (generate image map) → verify map
4. **Batch 4:** Task 4.1 (patch HTML) → Task 4.2 (verify in Brave)
5. **Batch 5:** Task 5.x (cleanup, attribution, commit)

---

## What is Needed Before Starting

1. **Unsplash API key** — https://unsplash.com/developers (free, instant approval)
2. **Pixabay API key** — https://pixabay.com/api/docs/ (free, instant approval)
3. **Strategy confirmed:** Mixed — Unsplash for ~50 quality images on visual topics, Pixabay for remaining ~1,400. Re-run Unsplash on subsequent days for more.
