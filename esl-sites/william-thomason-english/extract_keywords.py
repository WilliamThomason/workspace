"""
extract_keywords.py
Reads Sliding In.html, extracts lessonData, and produces keywords.json
with one keyword per question for image searching.
"""
import re, json, os

HTML_FILE = os.path.join(os.path.dirname(__file__), "Sliding In.html")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "keywords.json")

# Question words / stop words to strip
STOP_WORDS = {
    "you", "your", "the", "a", "an", "of", "to", "in", "on", "at", "for",
    "and", "or", "but", "with", "from", "by", "it", "is", "are", "was",
    "were", "be", "been", "being", "that", "this", "these", "those",
    "there", "here", "they", "them", "their", "we", "us", "our", "my",
    "me", "do", "does", "did", "about", "like", "think", "feel", "know",
    "want", "need", "go", "get", "make", "take", "have", "has", "had",
    "would", "could", "should", "will", "can", "may", "might", "shall",
    "not", "no", "yes", "so", "if", "then", "than", "very", "really",
    "just", "also", "only", "even", "still", "already", "ever", "never",
    "always", "often", "sometimes", "usually", "rather", "quite", "much",
    "more", "most", "less", "least", "some", "any", "all", "each", "every",
    "both", "few", "many", "several", "own", "other", "another", "such",
    "what", "which", "who", "whom", "whose", "where", "when", "why", "how"
}

QUESTION_PREFIXES = [
    "in your opinion", "do you", "what", "how", "why", "when", "where",
    "who", "would you", "have you", "are you", "is", "are", "can you",
    "do", "does", "did", "would", "could", "should", "has", "have", "had"
]

def extract_keyword(question, topic_slug, q_index):
    """Extract a searchable keyword from an ESL question."""
    cleaned = question.lower().strip()
    
    # Strip question prefixes
    for prefix in QUESTION_PREFIXES:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            break
    
    # Remove punctuation
    cleaned = re.sub(r'[?!.,;:\'\"()\-]', ' ', cleaned)
    
    # Split and filter
    words = cleaned.split()
    meaningful = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    
    if not meaningful:
        # Fallback: use topic slug
        return topic_slug.replace("-", " ")
    
    # Take first 2-3 meaningful words for better search results
    # But keep it to 2 for very long questions
    keyword = " ".join(meaningful[:2])
    
    # If keyword is too short (< 4 chars), try to add a third word
    if len(keyword) < 4 and len(meaningful) > 2:
        keyword = " ".join(meaningful[:3])
    
    return keyword


def main():
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Extract lessonData JSON
    match = re.search(r'var lessonData = (\[.*?\]);', html, re.DOTALL)
    if not match:
        print("ERROR: Could not find lessonData in HTML")
        return
    
    data = json.loads(match.group(1))
    
    keywords = []
    for cat in data:
        for topic in cat["topics"]:
            slug = topic.get("slug", topic["title"].lower().replace(" ", "-"))
            for i, q in enumerate(topic["questions"]):
                question_text = q["original"]
                keyword = extract_keyword(question_text, slug, i)
                keywords.append({
                    "topic_slug": slug,
                    "topic_title": topic["title"],
                    "q_index": i,
                    "question": question_text,
                    "keyword": keyword
                })
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(keywords, f, indent=2, ensure_ascii=False)
    
    print(f"Extracted {len(keywords)} keywords → {OUTPUT_FILE}")
    
    # Show first 10 samples
    for k in keywords[:10]:
        print(f"  [{k['topic_slug']}] Q{k['q_index']}: \"{k['keyword']}\" ← {k['question'][:60]}...")


if __name__ == "__main__":
    main()
