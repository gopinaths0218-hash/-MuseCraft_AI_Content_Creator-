import os
import random
import requests
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")

def local_generate(mode, topic, genre, tone, details):
    """Useful offline fallback; each request selects a different writing structure."""
    rng = random.SystemRandom()
    details_text = f"\n\nCreative details: {details}" if details else ""
    if mode == "social":
        hooks = [
            f"Stop scrolling—here's why {topic} deserves your attention.",
            f"What if your next big idea starts with {topic}?",
            f"A little inspiration for today: {topic}.",
            f"Let's talk about {topic}—and how it can make a difference."
        ]
        angles = [
            "Lead with a relatable challenge, then share one practical insight.",
            "Show a quick before-and-after, followed by the key takeaway.",
            "Use a surprising question, explain the idea, and invite discussion."
        ]
        return f"""SOCIAL CONTENT: {topic}
Platform/style: {genre}
Tone: {tone}

HOOK
{rng.choice(hooks)}

CAPTION
{topic} ✨

Some of the most memorable ideas begin with curiosity. Explore this thought, try one small step, and make it your own. Save this for later or share it with someone who would enjoy it.

CONTENT PLAN
1. Opening: {rng.choice(angles)}
2. Main value: Explain the most useful or interesting part of {topic} in clear, specific language.
3. Example: Give your audience a real-life situation they can relate to.
4. Closing: End with one memorable takeaway.

CALL TO ACTION
What is your perspective on {topic}? Share it in the comments.

HASHTAGS
#MuseCraftAI #CreativeIdeas #{''.join(word.title() for word in topic.split()[:2])} #ContentCreation #Inspiration
{details_text}"""
    openings = [
        f"The first sign that something was wrong appeared when {topic.lower()}.",
        f"Nobody in the town expected {topic.lower()} to change their lives.",
        f"At the edge of an ordinary day, {topic.lower()} became an extraordinary mystery.",
        f"Years later, the memory began with one impossible detail: {topic.lower()}."
    ]
    twists = [
        "The clue was not a warning—it was an invitation from someone they had forgotten.",
        "The person they trusted most had been protecting the truth for years.",
        "The discovery solved one mystery but revealed a much larger one.",
        "Their greatest obstacle turned out to be a choice they had made long ago."
    ]
    endings = [
        "As the morning light arrived, they understood that courage was not the absence of fear, but the decision to move forward.",
        "The final message was simple: some doors open only when we stop searching for the key.",
        "They walked away with no perfect answer, but with a truth worth carrying.",
        "And somewhere beyond the silence, a new chapter quietly began."
    ]
    return f"""TITLE: {topic.title()}
GENRE: {genre}
MOOD: {tone}

CHARACTERS
• Protagonist: A curious, determined person with a personal reason to pursue the central idea.
• Companion: A thoughtful ally who challenges the protagonist's assumptions.
• Mystery figure: Someone whose motives become clear only near the turning point.

SCENE 1 — THE BEGINNING
{rng.choice(openings)}
Establish the setting through sensory details. Introduce what the protagonist wants and the small problem that interrupts an otherwise familiar day.

SCENE 2 — THE DISCOVERY
A new clue connects the central idea to something personal. The protagonist investigates, meets resistance, and learns that the first explanation may be incomplete.

SCENE 3 — THE CONFLICT
{rng.choice(twists)}
The protagonist must choose between the comfortable path and the difficult truth. Use dialogue and action to reveal their values.

SCENE 4 — THE CLIMAX
Bring the characters together at the moment when the decision matters most. Let the protagonist's earlier choices shape the outcome.

ENDING
{rng.choice(endings)}

DIALOGUE SAMPLE
“Are you certain this is the right way?”
“Not certain,” the protagonist replied. “But I know why I have to try.”

WRITER'S NOTE
Expand each scene with character-specific dialogue, vivid locations, and consequences that follow naturally from the choices.
{details_text}"""

def ai_generate(mode, topic, genre, tone, details):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    endpoint = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    system = ("You are MuseCraft AI, a creative writing assistant. Produce original, detailed, "
              "non-repetitive content. Follow the requested language if it appears in the user's details. "
              "Avoid generic filler. Return only the finished content.")
    task = "Create a complete story or screenplay outline with a title, distinct characters, scene-by-scene development, dialogue, climax, and satisfying ending." if mode == "story" else "Create platform-ready social content with a strong hook, substantial caption, useful content outline, CTA, and relevant hashtags."
    prompt = f"Task: {task}\nTopic: {topic}\nGenre/platform: {genre}\nTone: {tone}\nAdditional details and language: {details or 'Use creative judgment.'}\nMake this response distinct and specific to this request."
    try:
        r = requests.post(f"{endpoint}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages":[{"role":"system","content":system},{"role":"user","content":prompt}],
                  "temperature":0.9, "max_tokens":1800}, timeout=90)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        app.logger.warning("AI provider unavailable; using local fallback: %s", exc)
        return None

@app.get("/")
def home():
    return send_from_directory(".", "index.html")

@app.get("/api/health")
def health():
    return jsonify(status="ok", service="MuseCraft AI backend")

@app.post("/api/generate")
def generate():
    data = request.get_json(silent=True) or {}
    topic = str(data.get("topic", "")).strip()
    if not topic:
        return jsonify(error="Please enter a topic or idea."), 400
    if len(topic) > 1500:
        return jsonify(error="Topic is too long (maximum 1500 characters)."), 400
    mode = data.get("mode", "story")
    if mode not in ("story", "social"):
        return jsonify(error="Mode must be story or social."), 400
    genre = str(data.get("genre", "Creative")).strip()[:100]
    tone = str(data.get("tone", "Engaging")).strip()[:100]
    details = str(data.get("details", "")).strip()[:4000]
    content = ai_generate(mode, topic, genre, tone, details)
    provider = "openai" if content else "local"
    if not content:
        content = local_generate(mode, topic, genre, tone, details)
    return jsonify(content=content, provider=provider)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
