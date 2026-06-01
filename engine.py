import os
import re
import hashlib
import json
from pathlib import Path
from anthropic import Anthropic
from personas import PERSONAS

client = Anthropic()

PATTERN_TO_PERSONA = {
    "scope_too_safe": "anchor",
    "assumption_unchallenged": "challenger",
    "missing_external_evidence": "benchmarker",
    "analysis_paralysis": "experimenter",
    "risk_glossed_over": "pressure_tester",
    "delivery_gap": "integrator",
}

AVAILABLE_PATTERNS = ", ".join(PATTERN_TO_PERSONA.keys())


def parse_transcript(transcript_path: str) -> list[dict]:
    """Parse transcript.md into a list of turns."""
    with open(transcript_path, "r") as f:
        content = f.read()

    lines = content.split("\n")
    turns = []

    for line in lines:
        if line.startswith("#") or line.startswith("Participants:") or not line.strip():
            continue

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

    if len(chunk_text) < 100:
        return None

    system_prompt = f"""You are an expert facilitator analyzing meeting transcripts for team dynamics patterns.

Detect exactly ONE of these patterns:
1. scope_too_safe: The team is converging on an MVP or incremental version when a bolder, more ambitious approach is possible. Watch for "MVP", "phase one", "just deliver", "good enough" without exploring what a bolder version could unlock.
2. assumption_unchallenged: A team member assumes a past solution applies directly to a new situation without scrutiny. Requires: (A) mention of "that worked for X", (B) plan to apply same approach to Y, (C) no one questions if situations are comparable.
3. missing_external_evidence: A critical decision is being made WITHOUT consulting external benchmarks, market data, competitor examples, or outside-in evidence. Triggers: Decision made/dismissed without any mention of comparable data, competitor moves, market research, benchmarks, or external validation. Even dismissing a data point (like a price signal) without comparing to market context. Most sensitive pattern — fire whenever external reference points are absent from a decision point.
4. analysis_paralysis: The team is stuck in discussion, complexity, or risk-aversion when a small experiment, prototype, or quick test would unlock progress. Watch for "too complex", "later phase", "handle later", "if we have time".
5. risk_glossed_over: Potential risks are acknowledged but quickly dismissed without honest examination. Watch for "should be fine", "won't happen", "address that later", "consensus" that masks unexamined concerns.
6. delivery_gap: The team is skipping critical design-to-delivery questions (platform fit, ownership, MVP scope, build risk) before handing off to the build team.

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
            max_tokens=1000,
            system=persona["system_prompt"],
            messages=[
                {
                    "role": "user",
                    "content": f"Here's the dialogue:\n\n{chunk_text}\n\nProvide your intervention.",
                }
            ],
        )
        response_text = message.content[0].text.strip()

        try:
            parsed = json.loads(response_text)
            question = parsed.get("question", "")
            context = parsed.get("context", "")
        except json.JSONDecodeError:
            question = ""
            context = response_text

        return {
            "persona": persona["name"],
            "persona_key": persona_key,
            "colour": persona["colour"],
            "pattern": pattern,
            "question": question,
            "context": context,
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

        if cache_data.get("transcript_hash") == transcript_hash:
            return cache_data.get("events")
        return None
    except Exception as e:
        print(f"Error loading cache: {e}")
        return None


def run_demo(transcript_path: str, cache_key: str = "", _file_hash: str = "") -> list[dict]:
    """Run the full pipeline on the transcript."""
    turns = parse_transcript(transcript_path)
    chunks = chunk_turns(turns, window_size=4, slide=1)

    cooldown = {}
    firing_count = {}  # Track firings per persona per session
    max_firings_per_session = 2
    events = []

    for turn_idx, turn in enumerate(turns):
        event = {
            "turn_index": turn_idx,
            "speaker": turn["speaker"],
            "text": turn["text"],
            "intervention": None,
        }

        to_remove = [k for k, v in cooldown.items() if v <= 1]
        for k in to_remove:
            del cooldown[k]
        for persona_key in cooldown:
            cooldown[persona_key] -= 1

        if turn_idx >= 3 and turn_idx < len(chunks) + 3:
            chunk_idx = turn_idx - 3
            if chunk_idx >= 0 and chunk_idx < len(chunks):
                chunk = chunks[chunk_idx]

                pattern = detect_pattern(chunk)
                if pattern:
                    persona_key = PATTERN_TO_PERSONA[pattern]

                    # Check both cooldown and max firings per session
                    if (persona_key not in cooldown or cooldown[persona_key] <= 0) and \
                       firing_count.get(persona_key, 0) < max_firings_per_session:
                        intervention = dispatch_persona(pattern, chunk)
                        if intervention:
                            event["intervention"] = intervention
                            cooldown[persona_key] = 8
                            firing_count[persona_key] = firing_count.get(persona_key, 0) + 1

        events.append(event)

    if _file_hash:
        cache_path = f"events_cache_{cache_key}.json" if cache_key else "events_cache.json"
        save_cache(events, _file_hash, cache_path)

    return events
