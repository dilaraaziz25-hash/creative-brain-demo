import os
import re
import hashlib
import json
from pathlib import Path
from anthropic import Anthropic
from personas import PERSONAS

client = Anthropic()

PATTERN_TO_PERSONA = {
    "groupthink": "anarchist",
    "assumption_unchallenged": "cartographer",
    "missing_perspective": "fool",
    "risk_glossed_over": "devils_advocate",
    "expertise_needed": "industry_sme",
}

AVAILABLE_PATTERNS = ", ".join(PATTERN_TO_PERSONA.keys())


def parse_transcript(transcript_path: str) -> list[dict]:
    """Parse transcript.md into a list of turns."""
    with open(transcript_path, "r") as f:
        content = f.read()

    # Extract lines after the header/participants section
    lines = content.split("\n")
    turns = []

    for line in lines:
        # Skip headers and empty lines
        if line.startswith("#") or line.startswith("Participants:") or not line.strip():
            continue

        # Match "Speaker: text"
        match = re.match(r"^(\w+):\s+(.+)$", line.strip())
        if match:
            speaker, text = match.groups()
            turns.append({"speaker": speaker, "text": text})

    return turns


def chunk_turns(turns: list[dict], window_size: int = 4, slide: int = 1) -> list[list[dict]]:
    """Group turns into sliding window chunks."""
    chunks = []
    for i in range(len(turns) - window_size + 1):
        chunk = turns[i : i + window_size]
        chunks.append(chunk)
    return chunks


def detect_pattern(chunk: list[dict]) -> str | None:
    """Detect a pattern in a chunk using Claude Haiku."""
    chunk_text = "\n".join([f"{turn['speaker']}: {turn['text']}" for turn in chunk])

    # Skip pattern detection on very short chunks (e.g., "I think so", "Yeah")
    if len(chunk_text) < 100:
        return None

    system_prompt = f"""You are an expert facilitator analyzing meeting transcripts for team dynamics patterns.

Detect exactly ONE of these patterns in the dialogue:
- groupthink: The team is rushing to consensus, suppressing dissent, or defaulting to past solutions without scrutiny
- assumption_unchallenged: Key assumptions are stated as facts without examination
- missing_perspective: A critical viewpoint or expertise is absent from the conversation
- risk_glossed_over: Potential risks or concerns are acknowledged but quickly dismissed
- expertise_needed: Team members cite industry norms or standards without data (e.g., "that's standard", "that's what everyone does", "that's normal practice"). External benchmarks, industry data, or expert input would strengthen the decision.

Respond with ONLY the pattern name (one word, lowercase with underscores), or "none" if no pattern detected.
Do not explain. Just the pattern name."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=20,
            system=system_prompt,
            messages=[{"role": "user", "content": chunk_text}],
        )
        pattern = message.content[0].text.strip().lower()
        if pattern in PATTERN_TO_PERSONA:
            return pattern
        return None
    except Exception as e:
        print(f"Error detecting pattern: {e}")
        return None


def dispatch_persona(pattern: str, chunk: list[dict]) -> dict:
    """Generate a persona intervention for a detected pattern."""
    persona_key = PATTERN_TO_PERSONA.get(pattern)
    if not persona_key:
        return None

    persona = PERSONAS[persona_key]
    chunk_text = "\n".join([f"{turn['speaker']}: {turn['text']}" for turn in chunk])

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=persona["system_prompt"],
            messages=[
                {
                    "role": "user",
                    "content": f"Here's the dialogue:\n\n{chunk_text}\n\nProvide your intervention.",
                }
            ],
        )
        intervention_text = message.content[0].text.strip()

        return {
            "persona": persona["name"],
            "colour": persona["colour"],
            "intervention": intervention_text,
            "pattern": pattern,
        }
    except Exception as e:
        print(f"Error dispatching persona: {e}")
        return None


def get_transcript_hash(transcript_path: str) -> str:
    """Get hash of transcript file for cache invalidation."""
    with open(transcript_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def save_cache(events: list[dict], transcript_hash: str, cache_path: str = "events_cache.json"):
    """Save events to a JSON cache file with transcript hash."""
    cache_data = {
        "transcript_hash": transcript_hash,
        "events": events,
    }
    cache_file = Path(__file__).parent / cache_path
    with open(cache_file, "w") as f:
        json.dump(cache_data, f, indent=2)


def load_cache(transcript_hash: str, cache_path: str = "events_cache.json") -> list[dict] | None:
    """Load events from cache if hash matches. Returns None if cache miss or invalid."""
    cache_file = Path(__file__).parent / cache_path
    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        # Verify hash matches
        if cache_data.get("transcript_hash") == transcript_hash:
            return cache_data.get("events")
        return None
    except Exception as e:
        print(f"Error loading cache: {e}")
        return None


def run_demo(transcript_path: str, _file_hash: str = "") -> list[dict]:
    """Run the full pipeline on the transcript. _file_hash is used for cache invalidation."""
    turns = parse_transcript(transcript_path)
    chunks = chunk_turns(turns, window_size=4, slide=1)

    cooldown = {}
    events = []

    for turn_idx, turn in enumerate(turns):
        event = {
            "turn_index": turn_idx,
            "speaker": turn["speaker"],
            "text": turn["text"],
            "intervention": None,
        }

        # Decrement cooldown
        to_remove = [k for k, v in cooldown.items() if v <= 1]
        for k in to_remove:
            del cooldown[k]
        for persona_key in cooldown:
            cooldown[persona_key] -= 1

        # Only analyze for patterns after the first full window (turn 3+)
        # This ensures patterns develop across multiple turns before firing
        if turn_idx >= 3 and turn_idx < len(chunks) + 3:
            # Find the chunk that ends at this turn
            chunk_idx = turn_idx - 3
            if chunk_idx >= 0 and chunk_idx < len(chunks):
                chunk = chunks[chunk_idx]

                # Detect pattern
                pattern = detect_pattern(chunk)
                if pattern:
                    persona_key = PATTERN_TO_PERSONA[pattern]

                    # Check cooldown
                    if persona_key not in cooldown or cooldown[persona_key] <= 0:
                        intervention = dispatch_persona(pattern, chunk)
                        if intervention:
                            event["intervention"] = intervention
                            cooldown[persona_key] = 6

        events.append(event)

    # Save to file-based cache for persistence across restarts
    if _file_hash:
        save_cache(events, _file_hash)

    return events
