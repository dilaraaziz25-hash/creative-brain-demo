# Creative Brain — Implementation Notes

## Current App Structure (app.py execution order)

### 1. Imports & Config (Lines 1-8)
```python
import streamlit as st, time, os
from pathlib import Path
from engine import run_demo, get_transcript_hash, load_cache
from personas import PERSONAS

st.set_page_config(layout="wide", page_title="The Creative Brain")
```

### 2. Session State Initialization (Lines 10-16) ⭐ CRITICAL
**Must be FIRST before any st.write(), st.markdown(), or other Streamlit commands**
```python
if "playing" not in st.session_state:
    st.session_state.playing = False
if "current_turn" not in st.session_state:
    st.session_state.current_turn = 0
if "listening_state" not in st.session_state:
    st.session_state.listening_state = False
```
**Why:** Streamlit re-runs the entire script on every user interaction. Session state must be initialized before it's accessed.

### 3. Debug Output (Line 19)
```python
st.write(f"DEBUG: playing={st.session_state.get('playing', 'NOT SET')}, turn={st.session_state.get('current_turn', 'NOT SET')}")
```
Shows session state on each rerun (remove later).

### 4. CSS Styling (Lines 21-88)
Custom Streamlit CSS for transcript turns and persona cards.

### 5. Function Definitions (Lines 91-125)
- `load_events(_transcript_hash)`: Loads from file cache or runs pipeline
- `get_persona_image_or_placeholder()`: Shows persona card images or colored placeholder

### 6. Load Events (Lines 128-134)
```python
if "events" not in st.session_state:
    transcript_path = Path(__file__).parent / "transcript.md"
    transcript_hash = get_transcript_hash(str(transcript_path))
    st.session_state.events = load_events(transcript_hash)

events = st.session_state.events
```

### 7. Auto-Play Loop (Lines 136-155) ⭐ KEY LOGIC
```python
if st.session_state.get("playing"):
    current_event = events[st.session_state.current_turn]
    
    if current_event["intervention"]:
        # Turn has intervention → STOP and show card
        st.session_state.playing = False
        st.rerun()
    else:
        # Turn has no intervention → WAIT and advance
        time.sleep(1.5)
        if st.session_state.current_turn < len(events) - 1:
            st.session_state.current_turn += 1
        else:
            st.session_state.playing = False
        st.rerun()
```
**This is the core playback mechanism.** Each rerun:
- Checks if playing
- If current turn has intervention: pause immediately
- If no intervention: sleep 1.5s, advance turn, rerun
- Loop continues until all turns shown or paused on intervention

### 8. Rest of App (Lines 157+)
- Title and description
- Two-column layout
- Playback buttons (Play/Continue, Stop, Next, Reset)
- Transcript display with progressive rendering
- Persona card display with dynamic button labels

---

## Major Fixes Made

### Fix 1: Session State Initialization Order
**Problem:** Session state was initialized AFTER st.set_page_config() and CSS, causing "NOT SET" errors.
**Solution:** Move all session state init to lines 10-16, immediately after st.set_page_config().
**Why it matters:** Streamlit must know about session variables before they're accessed.

### Fix 2: Pattern Detection Timing
**Problem:** Interventions fired at turn 0, showing persona cards on startup.
**Solution:** In `engine.py`, only analyze patterns from turn 3+ (`if turn_idx >= 3`).
**Why:** Patterns need 4+ turns to develop. First window is turns [0-3], analyzed at turn 3.
**File:** `engine.py:179-196`

### Fix 3: Simplified Auto-Play Logic
**Problem:** Complex `listening_state` flag caused races through all turns instantly.
**Solution:** Direct logic: if turn has intervention → stop, else → wait 1.5s and advance.
**Why it works:** Each rerun shows one turn before deciding what to do next.
**File:** `app.py:136-155`

### Fix 4: Bounds Checking
**Problem:** `current_turn` could exceed `len(events)`, causing IndexError.
**Solution:** Add bounds check in Play button and rendering loop.
**File:** `app.py:151-152` (auto-play), line 205 (render)

### Fix 5: File-Based Caching
**Problem:** Cache was lost on Streamlit restart.
**Solution:** Added `save_cache()` and `load_cache()` in `engine.py`.
**How it works:**
  1. After `run_demo()` completes, save events + transcript hash to `events_cache.json`
  2. On startup, `load_cache()` checks if hash matches
  3. If match: load from file (no API calls)
  4. If mismatch: run pipeline, update cache
**Files:** `engine.py:126-153`

### Fix 6: Initial State Cleanliness
**Problem:** Button showed "Continue" and persona card showed intervention on load.
**Solution:** 
  - Button shows "Continue" only if `current_turn > 0` (not on first load)
  - Persona card shows intervention only if `current_turn > 0 or playing`
**Files:** `app.py:165, 254`

### Fix 7: Persona Card Pause Check
**Problem:** Auto-play didn't pause on interventions (removed, replaced with simpler logic).
**Solution:** Auto-play loop checks if current turn has intervention and stops if so.
**File:** `app.py:136-155`

---

## Key Design Decisions

### Auto-Play Mechanism
- **1.5 second delay** between turns (natural pacing for meeting playback)
- **Immediate pause** when intervention detected (no delay, show card right away)
- **No listening_state flag** — too complex, caused races
- **Clean state tracking** — only `playing`, `current_turn`, `listening_state` needed

### Button States
- `▶ Play`: Stopped, no intervention (initial state or after manual step)
- `▶ Continue`: Stopped, current turn has intervention (presenter read the card)
- `⏸ Pause`: Playing (user can stop anytime)

### Persona Card Display
- Empty "🎧 Listening..." on startup (first load, turn=0)
- Shows persona card only when:
  - `current_turn > 0` (playback started) AND turn has intervention, OR
  - `playing=True` (actively advancing through turns)

### Caching Layers
1. **File cache** (`events_cache.json`): Survives restarts, checks hash
2. **Streamlit cache** (`@st.cache_data`): Fast within-session, invalidates on hash change

---

## Execution Flow Example

**User clicks Play at turn 0:**

| Rerun | State | Action |
|-------|-------|--------|
| 1 | playing=False, turn=0 | User clicks "▶ Play" → set playing=True, rerun |
| 2 | playing=True, turn=0 | Auto-play: turn 0 has no intervention → sleep 1.5s, turn=1, rerun |
| 3 | playing=True, turn=1 | Auto-play: turn 1 has no intervention → sleep 1.5s, turn=2, rerun |
| 4 | playing=True, turn=2 | Auto-play: turn 2 has no intervention → sleep 1.5s, turn=3, rerun |
| 5 | playing=True, turn=3 | Auto-play: turn 3 has no intervention → sleep 1.5s, turn=4, rerun |
| 6 | playing=True, turn=4 | Auto-play: turn 4 HAS intervention → set playing=False, rerun |
| 7 | playing=False, turn=4 | Render: show transcript 0-4, show persona card (The Anarchist) |
| - | - | User reads intervention for 10-30 seconds |
| 8 | playing=False, turn=4 | User clicks "▶ Continue" → turn=5, set playing=True, rerun |
| 9 | playing=True, turn=5 | Auto-play: turn 5 has no intervention → sleep 1.5s, turn=6, rerun |

---

## Critical Gotchas

### Gotcha 1: Session State Before st.write()
If session state isn't initialized before ANY st.write(), you get "NOT SET" errors.
**Fix:** Initialize all session variables at line 10-16, before line 19 debug output.

### Gotcha 2: st.rerun() Stops Execution
When you call `st.rerun()`, the current execution stops immediately.
Code after `st.rerun()` never runs.
```python
st.session_state.x = 1
st.rerun()
st.write("This never runs")  # ❌ Never executed
```

### Gotcha 3: Streamlit Re-runs Entire Script
On EVERY user interaction (button click, slider change, etc.), Streamlit re-runs the entire script from top to bottom.
This is why session state is critical — it's the only way to persist data across reruns.

### Gotcha 4: Cache Invalidation on File Change
When you edit `transcript.md`, the hash changes, cache is invalidated, and the pipeline re-runs automatically.
This is intentional behavior.

### Gotcha 5: Persona Card Border Color Variable
The transcript turn HTML uses `--intervention-color` CSS variable, which gets set per-turn:
```python
border_color = intervention["colour"] if intervention else "transparent"
turn_html = f'<div ... style="--intervention-color: {border_color};">'
```
This is why coloured borders show exactly where personas fire.

---

## Files Overview

### `app.py` (Main UI)
- Session state management
- Auto-play loop
- Streamlit UI (buttons, layout, rendering)
- Persona card display logic

### `engine.py` (Core Pipeline)
- `get_transcript_hash()`: MD5 hash of transcript.md
- `parse_transcript()`: Parses transcript.md into turn list
- `chunk_turns()`: Sliding window chunking (4-turn windows)
- `detect_pattern()`: Claude Haiku detects one pattern per chunk
- `dispatch_persona()`: Claude Sonnet generates intervention
- `run_demo()`: Orchestrates full pipeline, saves to cache
- `save_cache()` / `load_cache()`: File-based persistence

### `personas.py` (Definitions)
- 5 personas: Anarchist, Cartographer, Fool, Devil's Advocate, Industry SME
- Each has: name, colour (hex), trigger_keywords, system_prompt

### `transcript.md` (Data)
- Meeting with 16 turns
- Patterns: groupthink, assumption_unchallenged, missing_perspective, risk_glossed_over, expertise_needed

### `events_cache.json` (Generated)
- Stores: transcript_hash, events list
- Auto-created after first run
- Auto-invalidated if transcript changes

---

## Next Steps / Future Improvements

1. **Remove debug output** (st.write lines 19, 144, 149, etc.)
2. **Test full playback flow** with actual Streamlit app
3. **Add persona images** to `cards/{persona}/` folders
4. **Polish styling** (fonts, spacing, colors)
5. **Add transcript editing mode** (edit in UI, re-run pipeline)
6. **Add intervention replay** (button to go back to previous intervention)
7. **Export transcript** with annotations to PDF/Word

---

## Testing Checklist

- [ ] Startup: button shows "▶ Play", card shows "🎧 Listening..."
- [ ] Click Play: auto-advances turns every 1.5s
- [ ] Reaches intervention: auto-pauses, shows persona card, button shows "▶ Continue"
- [ ] Click Continue: skips past intervention, resumes auto-play
- [ ] Click Stop: pauses immediately
- [ ] Click Next: manual advance one turn
- [ ] Click Reset: back to turn 0, button shows "▶ Play"
- [ ] Restart app: cache loads instantly, no API calls

---

**Last Updated:** 2026-05-29
**Current Status:** Auto-play logic fixed, session state properly initialized
