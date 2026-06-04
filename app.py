import streamlit as st
import time
import re
import os
import base64
from pathlib import Path
from engine import run_demo, get_transcript_hash, load_cache, generate_reaction
from personas import PERSONAS

st.set_page_config(layout="wide", page_title="The Creative Brain")

# Load brain icon as base64
icon_path = os.path.join(os.path.dirname(__file__), "brain_icon.png")
with open(icon_path, "rb") as f:
    icon_b64 = base64.b64encode(f.read()).decode()

TRANSCRIPT_MAPPING = {
    "DIGITAL TRANSFORMATION": ("transcript.md", "digital_transformation"),
    "PRODUCT ROADMAP": ("transcript_product_roadmap.md", "product_roadmap"),
    "POST-MERGER INTEGRATION": ("transcript_post_merger.md", "post_merger"),
}

# Participant tile colours (muted desaturated pastels for Teams aesthetic)
PARTICIPANT_TILE_COLOURS = [
    {"tile": "#F2F2F0", "circle": "#D4C5A0"},  # warm sand
    {"tile": "#F2F2F0", "circle": "#B8BDD4"},  # soft periwinkle
    {"tile": "#F2F2F0", "circle": "#D4A8A8"},  # dusty rose
    {"tile": "#F2F2F0", "circle": "#A8C5B8"},  # sage green
    {"tile": "#F2F2F0", "circle": "#C5B8D4"},  # soft mauve
    {"tile": "#F2F2F0", "circle": "#B8D4C5"},  # muted mint
]

st.markdown(
    """
    <style>
    body { background-color: #F2F2F0; }
    [data-testid="stAppViewContainer"] { background-color: #F2F2F0; }

    /* Make all columns transparent - no background */
    [data-testid="stColumn"] {
        background-color: transparent !important;
        padding: 0 !important;
    }

    [data-testid="stHorizontalBlock"]:has(
      [data-testid="stButton"]) {
        background: transparent !important;
        box-shadow: none !important;
    }

    [data-testid="stHorizontalBlock"] {
        background: transparent !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:last-of-type {
        border-left: 2px solid #D0D0D0 !important;
        padding-left: 8px;
    }

    /* Transcript selector dropdown styling */
    [data-testid="stSelectbox"] > div > div {
        background-color: #FFFFFF !important;
        border: 1px solid #D0D0D0 !important;
        border-radius: 8px !important;
    }

    [data-testid="stSelectbox"] {
        margin-top: -0.5rem !important;
    }

    /* Right column styling */
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child > div {
        background-color: #E2E2E0;
        padding: 16px;
        border-radius: 8px;
    }

    .avatar-grid {
        display: grid;
        grid-template-columns: repeat(3, 160px);
        gap: 12px;
        padding: 0;
        width: 100%;
    }

    .avatar-item {
        width: 160px;
        height: 160px;
        background-color: #1E1E2E;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 12px;
        box-sizing: border-box;
        border: 2px solid transparent;
        transition: all 0.3s ease;
        cursor: default;
    }

    .avatar-item.active {
        border: 2px solid var(--person-color, #fff);
        box-shadow: 0 0 20px rgba(255, 255, 255, 0.3), inset 0 0 20px var(--person-color-shadow, rgba(255, 255, 255, 0.1));
        transform: scale(1.05);
    }

    .avatar-circle {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 24px;
        color: white;
        margin-bottom: 8px;
        transition: all 0.3s ease;
        flex-shrink: 0;
    }

    .avatar-item.active .avatar-circle {
        animation: pulse-circle 1.5s infinite;
    }

    @keyframes pulse-circle {
        0%, 100% {
            box-shadow: 0 0 0 0 var(--person-color, rgba(255, 255, 255, 0.7));
        }
        50% {
            box-shadow: 0 0 0 12px rgba(255, 255, 255, 0);
        }
    }

    @keyframes sparkle {
        0%   { filter: brightness(1) drop-shadow(0 0 4px rgba(100,150,255,0.6)); }
        50%  { filter: brightness(1.3) drop-shadow(0 0 14px rgba(100,150,255,0.9)); }
        100% { filter: brightness(1) drop-shadow(0 0 4px rgba(100,150,255,0.6)); }
    }

    .persona-icon {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 12px;
        flex-shrink: 0;
    }

    .persona-icon.sparkling {
        animation: sparkle 1.5s ease-in-out infinite;
    }

    .persona-icon.listening {
        opacity: 0.3;
    }

    .persona-header-with-icon {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .avatar-name {
        font-weight: 700;
        font-size: 13px;
        color: white;
        margin: 4px 0 2px 0;
        line-height: 1.2;
        word-wrap: break-word;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
    }

    .avatar-title {
        font-size: 11px;
        font-style: italic;
        color: #999999;
        line-height: 1.2;
        word-wrap: break-word;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
    }

    .persona-card {
        border-radius: 0.75rem;
        padding: 16px;
        background: white;
        border-left: 4px solid;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin-bottom: 1rem;
    }

    .persona-header-row {
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .persona-pattern {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.05rem;
        color: #999;
        margin-bottom: 1rem;
        font-weight: 600;
    }

    .persona-question {
        font-size: 15px;
        font-weight: 400;
        line-height: 1.5;
        margin-bottom: 1rem;
        color: #1A1A1A;
    }

    .listening-placeholder {
        text-align: center;
        padding: 2rem 1rem;
        color: #aaa;
        font-style: italic;
        font-size: 0.95rem;
    }

    .transcript-turn {
        margin-bottom: 1.2rem;
        padding: 0.75rem;
    }

    .transcript-turn.with-intervention {
        border-left: 3px solid;
        background-color: rgba(0, 0, 0, 0.01);
    }

    .speaker-name {
        font-weight: 700;
        color: #1f1f1f;
        display: inline;
        margin-right: 0.25rem;
    }

    .speaker-title {
        font-style: italic;
        color: #888;
        font-size: 0.85rem;
        font-weight: normal;
    }

    .turn-text {
        color: #484848;
        line-height: 1.5;
        margin-top: 0.25rem;
        font-size: 0.9rem;
    }

    .context-label {
        font-weight: 600;
        color: #666;
        margin-top: 0.75rem;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }

    .expander-content {
        font-size: 0.9rem;
        line-height: 1.6;
        color: #555;
    }

    .history-emoji {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }

    [data-testid="stExpander"] {
        border: none;
        background-color: transparent;
    }

    /* Persona question expander - inside outer intervention frame */
    [data-testid="stVerticalBlock"] > [data-testid="stExpander"] [role="button"] {
        font-size: 22px !important;
        font-weight: 500;
        background-color: transparent !important;
        padding: 12px !important;
        line-height: 1.45 !important;
    }

    [data-testid="stVerticalBlock"] > [data-testid="stExpander"] {
        background-color: transparent !important;
    }

    [data-testid="stVerticalBlock"] > [data-testid="stExpander"] details {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
    }

    [data-testid="stVerticalBlock"] > [data-testid="stExpander"] [role="button"]:hover {
        background-color: #F5F5F5 !important;
    }

    /* Intervention card frame - targets the container with col1 and col2 */
    [data-testid="stColumn"]:has([data-testid="stExpander"]) {
        background-color: #FFFFFF !important;
        border: 1px solid #D8D8D8 !important;
        border-radius: 12px !important;
        padding: 18px !important;
        margin-top: 8px !important;
    }

    /* Persona identity - inside outer intervention frame */
    [data-testid="stColumn"]:has([data-testid="stHtml"]) {
        background-color: transparent !important;
    }

    /* Expander lightening */
    [data-testid="stExpander"] {
        background-color: #F5F5F5 !important;
        border: 1px solid #E8E8E8 !important;
        border-radius: 8px !important;
    }

    .divider {
        border: none;
        border-top: 1px solid #e0e0e0;
        margin: 0.75rem 0;
    }

    .intervention-history-header {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #999;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }

    .intervention-history-item {
        font-size: 0.85rem;
        margin: 0 !important;
        padding: 0 !important;
    }

    .intervention-history-item [role="button"] {
        font-size: 0.85rem;
        padding: 4px 0 !important;
        min-height: auto !important;
    }

    .intervention-history-item [data-testid="stExpander"] {
        padding: 0 !important;
    }

    .history-question {
        font-size: 14px;
        font-weight: 400;
        color: #1A1A1A;
        margin-bottom: 0.75rem;
        line-height: 1.4;
    }

    .history-context {
        font-size: 13px;
        color: #666;
        line-height: 1.4;
    }

    img {
        max-height: 250px;
        width: 100%;
        object-fit: cover;
        margin-top: 0.75rem;
        border-radius: 0.5rem;
    }

    .placeholder-box {
        width: 100%;
        height: 150px;
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 0.85rem;
        text-align: center;
        padding: 1rem;
        margin-top: 0.75rem;
    }

    .section-header {
        font-size: 0.85rem;
        color: #999;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05rem;
        margin-bottom: 0.75rem;
        margin-top: 1rem;
    }

    .control-button {
        padding: 0.5rem 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "selected_transcript" not in st.session_state:
    st.session_state.selected_transcript = "DIGITAL TRANSFORMATION"
if "last_transcript" not in st.session_state:
    st.session_state.last_transcript = "DIGITAL TRANSFORMATION"
if "playing" not in st.session_state:
    st.session_state.playing = False
if "display_turn" not in st.session_state:
    st.session_state.display_turn = 0
if "current_turn" not in st.session_state:
    st.session_state.current_turn = -1
if "listening_state" not in st.session_state:
    st.session_state.listening_state = False
if "last_chime_turn" not in st.session_state:
    st.session_state.last_chime_turn = -1
if "intervention_history" not in st.session_state:
    st.session_state.intervention_history = []
if "reactions" not in st.session_state:
    st.session_state.reactions = {}

@st.cache_data
def load_events(_transcript_path: str, _transcript_hash: str, _cache_key: str):
    """Load events from file cache or run the pipeline."""
    cached_events = load_cache(_transcript_hash, f"events_cache_{_cache_key}.json")
    if cached_events:
        return cached_events

    return run_demo(_transcript_path, cache_key=_cache_key, _file_hash=_transcript_hash)


def play_intervention_chime():
    """Play a notification chime when persona intervention fires."""
    unique_id = int(time.time() * 1000000)

    chime_html = f"""
    <script>
    (function() {{
        // Digital glitch sound - three descending beeps
        const ctx = new (window.AudioContext || window.webkitAudioContext)();

        function playBeep(frequency, startTime, duration) {{
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.type = 'square';
            osc.frequency.value = frequency;

            gain.gain.setValueAtTime(0, startTime);
            gain.gain.linearRampToValueAtTime(0.15, startTime + 0.01);
            gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration);

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.start(startTime);
            osc.stop(startTime + duration);
        }}

        if (ctx.state === 'suspended') {{
            ctx.resume();
        }}

        const now = ctx.currentTime;
        playBeep(880, now, 0.08);
        playBeep(660, now + 0.1, 0.08);
        playBeep(440, now + 0.2, 0.08);
    }})();
    // Unique ID: {unique_id}
    </script>
    """
    st.components.v1.html(chime_html, height=0)


def get_persona_image_or_placeholder(persona_key: str, colour: str):
    """Get image from cards folder or show placeholder."""
    cards_dir = Path(__file__).parent / "cards" / persona_key
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    images = [
        f for f in cards_dir.iterdir()
        if f.is_file() and f.suffix.lower() in valid_extensions
    ] if cards_dir.exists() else []

    if images:
        st.image(str(images[0]), use_container_width=True)
    else:
        st.markdown(
            f'<div class="placeholder-box" style="background-color: {colour};">'
            f"Drop .jpg, .jpeg, .png, or .webp files in cards/{persona_key}/</div>",
            unsafe_allow_html=True,
        )


def parse_participants(transcript_path: str) -> list[dict]:
    """Parse participant names and titles from transcript."""
    with open(transcript_path, "r") as f:
        for line in f:
            if line.startswith("Participants:"):
                participants_line = line.replace("Participants:", "").strip()
                participants = []

                pattern = r"(\w[\w\s]+?)\s+\(([^)]+)\)"
                matches = re.findall(pattern, participants_line)

                for name, title in matches:
                    participants.append({
                        "name": name.strip(),
                        "title": title.strip(),
                    })
                return participants

    return []


def get_initials(name: str) -> str:
    """Get first 2 letters of first name."""
    parts = name.split()
    if len(parts) > 0:
        return parts[0][:2].upper()
    return "?"


def render_avatar_grid(participants: list[dict], current_speaker: str, tile_colours: list[dict]):
    """Render avatar grid with flexible sizing and pastel colours."""
    colour_map = {p["name"]: tile_colours[i % len(tile_colours)] for i, p in enumerate(participants)}

    # Build complete HTML with embedded CSS
    avatar_html = """
    <style>
    .pastel-avatar-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        width: 100%;
        background-color: #F2F2F0;
        padding: 8px;
        box-sizing: border-box;
        margin: 0;
    }

    .pastel-avatar-tile {
        aspect-ratio: 1 / 1;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        border: 1px solid #E0E0E0;
        transition: all 0.3s ease;
        box-sizing: border-box;
        padding: 12px;
    }

    .pastel-avatar-tile.active {
        border: 2px solid #6B8FC9;
        box-shadow: 0 0 12px rgba(107, 143, 201, 0.3);
        transform: scale(1.02);
    }

    .pastel-avatar-circle {
        width: 50%;
        aspect-ratio: 1 / 1;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 28px;
        font-family: "Source Sans Pro", -apple-system, BlinkMacSystemFont, sans-serif;
        color: #2D2D2D;
        margin-bottom: 8px;
        transition: all 0.3s ease;
    }

    .pastel-avatar-circle.active {
        animation: subtle-pulse 1.5s infinite;
    }

    @keyframes subtle-pulse {
        0%, 100% {
            box-shadow: 0 0 0 0 var(--circle-color);
        }
        50% {
            box-shadow: 0 0 0 8px rgba(0, 0, 0, 0.05);
        }
    }

    .pastel-avatar-name {
        font-weight: 700;
        font-size: 13px;
        font-family: "Source Sans Pro", -apple-system, BlinkMacSystemFont, sans-serif;
        color: #333;
        margin: 4px 0 2px 0;
        line-height: 1.2;
        word-wrap: break-word;
    }

    .pastel-avatar-title {
        font-size: 10px;
        font-family: "Source Sans Pro", -apple-system, BlinkMacSystemFont, sans-serif;
        font-style: italic;
        color: #666;
        line-height: 1.2;
        word-wrap: break-word;
    }

    .pastel-avatar-placeholder {
        aspect-ratio: 1 / 1;
        background-color: transparent !important;
        border: none !important;
        border-radius: 12px;
        box-shadow: none !important;
    }
    </style>

    <div class="pastel-avatar-grid">
    """

    for participant in participants:
        name = participant["name"]
        title = participant["title"]
        initials = get_initials(name)
        colours = colour_map[name]
        tile_colour = colours["tile"]
        circle_colour = colours["circle"]
        is_active = "active" if name == current_speaker else ""

        avatar_html += f"""
    <div class="pastel-avatar-tile {is_active}" style="background-color: {tile_colour};">
        <div class="pastel-avatar-circle {is_active}" style="background-color: {circle_colour}; --circle-color: {circle_colour};">
            {initials}
        </div>
        <div class="pastel-avatar-name">{name}</div>
        <div class="pastel-avatar-title">{title}</div>
    </div>
        """

    # Add placeholder tiles to fill out the grid to a multiple of 3
    remainder = len(participants) % 3
    if remainder != 0:
        placeholders = 3 - remainder
        for _ in range(placeholders):
            avatar_html += '\n    <div class="pastel-avatar-placeholder"></div>'

    avatar_html += "\n    </div>"

    # Use flexible height based on number of rows
    rows = (len(participants) + 2) // 3
    # Each tile is ~(1fr), gaps are 8px, plus padding
    grid_height = 400 + (rows - 1) * 50
    st.components.v1.html(avatar_html, height=grid_height)


st.markdown("<h2>🧠 The Creative Brain</h2>", unsafe_allow_html=True)

st.markdown("<b>Select Transcript</b>", unsafe_allow_html=True)
st.markdown('<div style="max-width:300px">', unsafe_allow_html=True)
new_transcript = st.selectbox(
    "",
    options=list(TRANSCRIPT_MAPPING.keys()),
    key="transcript_selector",
    index=list(TRANSCRIPT_MAPPING.keys()).index(st.session_state.selected_transcript) if "selected_transcript" in st.session_state else 0
)
st.markdown('</div>', unsafe_allow_html=True)

# Update selected transcript immediately if it changed
if "last_transcript" not in st.session_state:
    st.session_state.last_transcript = st.session_state.selected_transcript

if new_transcript != st.session_state.last_transcript:
    # Clear Streamlit cache to force reload of transcript data
    st.cache_data.clear()

    # Clear ALL session state completely
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # Re-initialize with new transcript
    st.session_state.selected_transcript = new_transcript
    st.session_state.last_transcript = new_transcript
    st.session_state.playing = False
    st.session_state.display_turn = 0
    st.session_state.current_turn = -1
    st.session_state.listening_state = False
    st.session_state.last_chime_turn = -1
    st.session_state.intervention_history = []
    st.rerun()

# ALWAYS use the current selectbox value
st.session_state.selected_transcript = new_transcript

# Load transcript based on current selection
transcript_file, cache_key = TRANSCRIPT_MAPPING[st.session_state.selected_transcript]
current_transcript_path = Path(__file__).parent / transcript_file

transcript_hash = get_transcript_hash(str(current_transcript_path))
events = load_events(str(current_transcript_path), transcript_hash, cache_key)

# Playback loop
if st.session_state.get("playing"):
    if st.session_state.current_turn >= 0 and st.session_state.current_turn < len(events):
        current_event = events[st.session_state.current_turn]

        if current_event["intervention"]:
            st.session_state.playing = False
            st.rerun()
        else:
            time.sleep(1.5)
            if st.session_state.display_turn < len(events):
                st.session_state.display_turn += 1
                st.session_state.current_turn = st.session_state.display_turn - 1
            else:
                st.session_state.playing = False
            st.rerun()

st.markdown("---")

col_play, col_next, col_reset, col_spacer = st.columns([1, 1, 1, 6])

has_intervention = (st.session_state.current_turn >= 0 and
                   st.session_state.current_turn < len(events) and
                   events[st.session_state.current_turn]["intervention"] is not None)

if st.session_state.playing:
    play_label = "⏸ Pause"
elif has_intervention and st.session_state.display_turn > 0:
    play_label = "▶ Continue"
else:
    play_label = "▶ Play"

with col_play:
    if st.button(play_label, key="play_btn"):
        if st.session_state.playing:
            st.session_state.playing = False
        else:
            if st.session_state.display_turn == 0:
                st.session_state.display_turn = 1
                st.session_state.current_turn = 0
            elif has_intervention and st.session_state.display_turn < len(events):
                st.session_state.display_turn += 1
                st.session_state.current_turn = st.session_state.display_turn - 1

            if st.session_state.display_turn <= len(events):
                st.session_state.playing = True
                st.rerun()

with col_next:
    if st.button("Next turn →", key="next_btn"):
        if st.session_state.display_turn < len(events):
            # Check if previous turn had an intervention
            prev_turn_idx = st.session_state.display_turn - 1
            if prev_turn_idx >= 0 and prev_turn_idx < len(events):
                prev_event = events[prev_turn_idx]
                if prev_event.get("intervention"):
                    # Generate reaction from the speaker whose turn had the intervention
                    speaker_with_intervention = prev_event["speaker"]
                    persona_name = prev_event["intervention"]["persona"]
                    question = prev_event["intervention"]["question"]
                    recent_turns = events[max(0, prev_turn_idx - 2):prev_turn_idx + 1]
                    reaction = generate_reaction(speaker_with_intervention, persona_name, question, recent_turns)
                    if reaction:
                        st.session_state.reactions[st.session_state.display_turn] = reaction

            st.session_state.display_turn += 1
            st.session_state.current_turn = min(st.session_state.display_turn - 1, len(events) - 1)

with col_reset:
    if st.button("↺ Reset", key="reset_btn"):
        st.session_state.display_turn = 0
        st.session_state.current_turn = -1
        st.session_state.playing = False
        st.session_state.intervention_history = []
        st.session_state.reactions = {}

st.markdown("---")

col_avatar, col_right = st.columns([0.65, 0.35])

# LEFT COLUMN: CREATIVE BRAIN INTERVENTION + AVATAR GRID
with col_avatar:
    current_event = None
    intervention = None
    if st.session_state.current_turn >= 0 and st.session_state.current_turn < len(events):
        current_event = events[st.session_state.current_turn]
        intervention = current_event["intervention"]

    should_show_intervention = intervention and (st.session_state.display_turn > 0 or st.session_state.playing)

    if should_show_intervention:
        if st.session_state.current_turn != st.session_state.last_chime_turn:
            play_intervention_chime()
            st.session_state.last_chime_turn = st.session_state.current_turn
            # Add to intervention history (fires only once per intervention)
            st.session_state.intervention_history.append({
                "turn_number": st.session_state.current_turn + 1,
                "intervention": intervention
            })

        # Two-column layout: brain icon + persona name on LEFT, expander on RIGHT
        col1, col2 = st.columns([0.75, 3.25], gap="small")

        with col1:
            # Brain icon with sparkle animation
            st.components.v1.html(f"""
            <style>
            @keyframes sparkle {{
                0%   {{
                    filter: brightness(1) drop-shadow(0 0 8px rgba(100,180,255,0.9));
                    transform: scale(1);
                }}
                50%  {{
                    filter: brightness(1.6) drop-shadow(0 0 28px rgba(100,180,255,1.0)) drop-shadow(0 0 50px rgba(150,200,255,0.7));
                    transform: scale(1.12);
                }}
                100% {{
                    filter: brightness(1) drop-shadow(0 0 8px rgba(100,180,255,0.9));
                    transform: scale(1);
                }}
            }}
            .brain-icon {{ width:48px; height:48px; border-radius:50%;
                animation: sparkle 1.2s ease-in-out infinite; }}
            </style>
            <img src="data:image/png;base64,{icon_b64}" class="brain-icon">
            """, height=60)

            # Persona name in color
            st.markdown(f"<div style='color: {intervention['colour']}; font-weight: 600; font-size: 16px;'>{intervention['persona']}</div>", unsafe_allow_html=True)

            # Pattern label muted
            pattern_text = intervention['pattern'].replace('_', ' ').capitalize()
            st.markdown(f"<div style='color: #999; font-size: 11px; letter-spacing: 0.05rem; font-weight: 600;'>{pattern_text}</div>", unsafe_allow_html=True)

            st.markdown("---")

        with col2:
            # Question as expandable label with context inside
            with st.expander(intervention['question'], expanded=False):
                st.markdown(f"<div class='expander-content'>{intervention['context']}</div>", unsafe_allow_html=True)

                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

                persona_key = intervention.get("persona_key")
                if persona_key:
                    get_persona_image_or_placeholder(persona_key, intervention['colour'])

    else:
        # Display listening state with faded brain icon
        st.components.v1.html(f"""
        <style>
        .brain-icon-listening {{
            width: 52px;
            height: 52px;
            border-radius: 50%;
            opacity: 0.3;
        }}
        </style>
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;">
            <img src="data:image/png;base64,{icon_b64}" class="brain-icon-listening">
            <div>🎧 Listening...</div>
        </div>
        """, height=140)

    # AVATAR GRID - Below intervention card
    st.markdown('<div class="section-header">👥 In this meeting</div>', unsafe_allow_html=True)

    participants = parse_participants(str(current_transcript_path))

    current_speaker = ""
    if st.session_state.current_turn >= 0 and st.session_state.current_turn < len(events):
        current_speaker = events[st.session_state.current_turn]["speaker"]

    render_avatar_grid(participants, current_speaker, PARTICIPANT_TILE_COLOURS)

# RIGHT COLUMN: LIVE TRANSCRIPT
with col_right:
    st.markdown('<div class="section-header">📝 Transcript</div>', unsafe_allow_html=True)

    if st.session_state.playing or st.session_state.display_turn > 0:
        start = 0
        transcript_items = ""
        for idx in range(start, min(st.session_state.display_turn, len(events))):
            event = events[idx]
            intervention = event["intervention"]
            border_color = intervention["colour"] if intervention else "transparent"

            # Check if this turn has a reaction to display
            reaction_html = ""
            if idx + 1 in st.session_state.reactions:
                reaction = st.session_state.reactions[idx + 1]
                reaction_html = f"""<div style="font-style:italic; font-size:12px; color:#666; margin-top:6px; font-family: 'Source Sans Pro', sans-serif;">*{event['speaker']}: {reaction}*</div>"""

            transcript_items += f"""
            <div style="margin-bottom:12px; padding-left:10px;
                 border-left:3px solid {border_color};">
                <div style="font-weight:500; font-size:13px;
                     color:#1a1a1a; font-family: 'Source Sans Pro', sans-serif;">{event['speaker']}</div>
                <div style="font-size:12px; color:#555;
                     margin-top:4px; font-family: 'Source Sans Pro', sans-serif;">{event['text']}</div>
                {reaction_html}
            </div>
            """

        st.components.v1.html(f"""
        <div style="height:250px; overflow-y:auto;
             padding:12px; background: transparent;
             border:1px solid #E0E0E0; border-radius:8px;
             font-family: 'Source Sans Pro', sans-serif; font-size:16px;">
        {transcript_items}
        <script>
        var container = document.currentScript.parentElement;
        container.scrollTop = container.scrollHeight;
        </script>
        </div>
        """, height=300)

    # INTERVENTION HISTORY (COMPACT) - Display independently from current intervention
    # Always show if there's history, regardless of whether a current intervention is showing
    if st.session_state.intervention_history:
        st.markdown('<div class="intervention-history-header">Previous nudges</div>', unsafe_allow_html=True)

        # Display in reverse order (most recent first)
        for item in reversed(st.session_state.intervention_history):
            intervention_data = item["intervention"]
            persona_name = intervention_data["persona"]
            colour = intervention_data["colour"]

            # Use Unicode filled circle with colour styling
            label = f"● {persona_name} · Turn {item['turn_number']}"

            with st.expander(label, expanded=False):
                # Add colour to the circle using markdown
                st.markdown(f"<span style='color: {colour};'>●</span> **{persona_name}**", unsafe_allow_html=True)
                st.markdown(f"<div class='history-question'>{intervention_data['question']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='history-context'><strong>Context:</strong> {intervention_data['context']}</div>", unsafe_allow_html=True)

    st.markdown("---")
    progress = min(st.session_state.display_turn / len(events), 1.0) if events else 0
    st.progress(progress, text=f"Turn {st.session_state.display_turn} of {len(events)}")
