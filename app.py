import streamlit as st
import time
import os
from pathlib import Path
from engine import run_demo, get_transcript_hash, load_cache
from personas import PERSONAS

st.set_page_config(layout="wide", page_title="The Creative Brain")

# Initialize session state FIRST — before any other code
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

# Custom CSS for styling
st.markdown(
    """
    <style>
    .transcript-turn {
        margin-bottom: 1.5rem;
        padding: 0.75rem;
        border-radius: 0.5rem;
    }
    .transcript-turn.with-intervention {
        border-left: 4px solid var(--intervention-color);
        background-color: rgba(255, 255, 255, 0.02);
    }
    .speaker-name {
        font-weight: 700;
        color: #1f1f1f;
        margin-bottom: 0.25rem;
    }
    .speaker-title {
        font-style: italic;
        color: #888;
        font-size: 0.9em;
        font-weight: normal;
    }
    .turn-text {
        color: #484848;
        line-height: 1.5;
    }
    .persona-card {
        border-radius: 0.75rem;
        padding: 12px 16px;
        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.85) 100%);
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }
    .persona-header {
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .persona-pattern {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05rem;
        color: #888;
        margin-bottom: 16px;
        opacity: 0.7;
    }
    .persona-text {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #333;
        margin-bottom: 1rem;
        max-height: none;
        overflow: visible;
    }
    [data-testid="stMarkdownContainer"] {
        max-height: none !important;
        overflow: visible !important;
        height: auto !important;
    }
    [data-testid="stMarkdownContainer"] * {
        max-height: none !important;
        overflow: visible !important;
        height: auto !important;
    }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] div {
        max-height: none !important;
        overflow: visible !important;
    }
    img {
        max-height: 300px;
        width: 100%;
        object-fit: cover;
        margin-top: 1rem;
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
        font-size: 0.9rem;
    }
    .listening-placeholder {
        text-align: center;
        padding: 3rem 1rem;
        color: #aaa;
        font-style: italic;
    }
    .control-button {
        padding: 0.5rem 1rem;
        margin-right: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_events(_transcript_hash: str):
    """Load events from file cache or run the pipeline. Hash validates cache."""
    # Try file-based cache first (survives Streamlit restarts)
    cached_events = load_cache(_transcript_hash)
    if cached_events:
        return cached_events

    # Cache miss: run the pipeline and save results
    transcript_path = Path(__file__).parent / "transcript.md"
    return run_demo(str(transcript_path), _file_hash=_transcript_hash)


def play_intervention_chime():
    """Play a notification chime when persona intervention fires using Web Audio API."""
    # Generate unique timestamp to embed in HTML and force fresh render
    unique_timestamp = int(time.time() * 1000000)

    chime_html = f"""
    <script>
    (function() {{
        // Unique ID comment ({unique_timestamp}) ensures each chime renders fresh
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();

        // First tone: 1000 Hz for 150ms
        const osc1 = audioContext.createOscillator();
        const gain1 = audioContext.createGain();
        osc1.connect(gain1);
        gain1.connect(audioContext.destination);
        osc1.frequency.value = 1000;
        osc1.type = 'sine';
        gain1.gain.setValueAtTime(0.15, audioContext.currentTime);
        gain1.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
        osc1.start(audioContext.currentTime);
        osc1.stop(audioContext.currentTime + 0.15);

        // Second tone: 1500 Hz for 150ms, starts 50ms after first tone ends
        const osc2 = audioContext.createOscillator();
        const gain2 = audioContext.createGain();
        osc2.connect(gain2);
        gain2.connect(audioContext.destination);
        osc2.frequency.value = 1500;
        osc2.type = 'sine';
        gain2.gain.setValueAtTime(0.15, audioContext.currentTime + 0.2);
        gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.35);
        osc2.start(audioContext.currentTime + 0.2);
        osc2.stop(audioContext.currentTime + 0.35);
    }})();
    </script>
    """
    st.components.v1.html(chime_html, height=0)


def get_persona_image_or_placeholder(persona_key: str, colour: str):
    """Get image from cards folder or show placeholder."""
    cards_dir = Path(__file__).parent / "cards" / persona_key
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    # Find images with case-insensitive extension matching
    images = [
        f for f in cards_dir.iterdir()
        if f.is_file() and f.suffix.lower() in valid_extensions
    ] if cards_dir.exists() else []

    if images:
        st.image(str(images[0]), use_container_width=True)
    else:
        # Show coloured placeholder
        st.markdown(
            f'<div class="placeholder-box" style="background-color: {colour};">'
            f"No images yet — drop .jpg, .jpeg, .png, or .webp files in cards/{persona_key}/</div>",
            unsafe_allow_html=True,
        )


# Load events (session state flags already initialized above)
if "events" not in st.session_state:
    transcript_path = Path(__file__).parent / "transcript.md"
    transcript_hash = get_transcript_hash(str(transcript_path))
    st.session_state.events = load_events(transcript_hash)

events = st.session_state.events

# Auto-play loop — simple and direct
# If current turn has intervention: stop and show card
# If current turn has no intervention: wait 1.5s and advance to next turn
if st.session_state.get("playing"):
    if st.session_state.current_turn >= 0 and st.session_state.current_turn < len(events):
        current_event = events[st.session_state.current_turn]

        if current_event["intervention"]:
            # Current turn has an intervention — stop and show the card
            st.session_state.playing = False
            st.rerun()
        else:
            # Current turn has no intervention — wait and advance
            time.sleep(1.5)
            if st.session_state.display_turn < len(events):
                st.session_state.display_turn += 1
                st.session_state.current_turn = st.session_state.display_turn - 1
            else:
                st.session_state.playing = False
            st.rerun()

st.title("🧠 The Creative Brain")
st.markdown(
    "An AI meeting facilitator that detects groupthink and injects persona interventions in real time."
)

# Speaker job titles mapping
SPEAKER_TITLES = {
    "Sarah": "Project Lead",
    "Marcus": "IT Director",
    "Priya": "Finance",
    "Tom": "Operations",
    "Lisa": "HR",
}

# Layout: two columns
col_transcript, col_card = st.columns([0.65, 0.35])

with col_transcript:
    st.subheader("Meeting Transcript")

    # Playback controls
    col_play, col_next, col_reset = st.columns([0.15, 0.15, 0.15])

    # Determine play button label dynamically
    has_intervention = (st.session_state.current_turn >= 0 and
                       st.session_state.current_turn < len(events) and
                       events[st.session_state.current_turn]["intervention"] is not None)

    if st.session_state.playing:
        play_label = "⏸ Pause"
    elif has_intervention and st.session_state.display_turn > 0:
        # "Continue" only shows if paused on intervention (not on first load)
        play_label = "▶ Continue"
    else:
        play_label = "▶ Play"

    with col_play:
        if st.button(play_label, key="play_btn"):
            if st.session_state.playing:
                # Pause while playing
                st.session_state.playing = False
            else:
                # Start or resume playing
                if st.session_state.display_turn == 0:
                    # Starting from beginning: show turn 0 and process it
                    st.session_state.display_turn = 1
                    st.session_state.current_turn = 0
                elif has_intervention and st.session_state.display_turn < len(events):
                    # Paused on intervention: skip past it to continue
                    st.session_state.display_turn += 1
                    st.session_state.current_turn = st.session_state.display_turn - 1
                # If not at beginning and no intervention, just resume as-is

                if st.session_state.display_turn <= len(events):
                    st.session_state.playing = True
                    st.rerun()

    with col_next:
        if st.button("Next turn →", key="next_btn"):
            if st.session_state.display_turn < len(events):
                st.session_state.display_turn += 1
                st.session_state.current_turn = min(st.session_state.display_turn - 1, len(events) - 1)
    with col_reset:
        if st.button("↺ Reset", key="reset_btn"):
            st.session_state.display_turn = 0
            st.session_state.current_turn = -1
            st.session_state.playing = False

    st.markdown("---")

    # Transcript display — only show if playing or we've started (display_turn > 0)
    if st.session_state.playing or st.session_state.display_turn > 0:
        transcript_container = st.container()
        with transcript_container:
            for idx in range(min(st.session_state.display_turn, len(events))):
                event = events[idx]
                intervention = event["intervention"]
                speaker = event['speaker']
                job_title = SPEAKER_TITLES.get(speaker, "")

                # Build turn HTML
                border_color = (
                    intervention["colour"] if intervention else "transparent"
                )
                title_html = f', <span class="speaker-title">{job_title}</span>' if job_title else ""
                turn_html = f"""
                <div class="transcript-turn {'with-intervention' if intervention else ''}"
                     style="--intervention-color: {border_color};">
                    <div class="speaker-name">{speaker}{title_html}</div>
                    <div class="turn-text">{event['text']}</div>
                </div>
                """
                st.markdown(turn_html, unsafe_allow_html=True)

            # Auto-scroll to bottom
            st.markdown(
                """
                <script>
                var scrollArea = document.querySelector('div[data-testid="stVerticalBlock"]');
                if (scrollArea) {
                    scrollArea.scrollTop = scrollArea.scrollHeight;
                }
                </script>
                """,
                unsafe_allow_html=True,
            )

with col_card:
    st.subheader("Persona Intervention")

    # Show current turn's intervention or listening placeholder
    current_event = None
    intervention = None
    if st.session_state.current_turn >= 0 and st.session_state.current_turn < len(events):
        current_event = events[st.session_state.current_turn]
        intervention = current_event["intervention"]

    # Only show intervention if we've started playback (display_turn > 0) or are actively playing
    should_show_intervention = intervention and (st.session_state.display_turn > 0 or st.session_state.playing)

    if should_show_intervention:
        # Play chime once when intervention first appears
        if st.session_state.current_turn != st.session_state.last_chime_turn:
            play_intervention_chime()
            st.session_state.last_chime_turn = st.session_state.current_turn

        # Build persona card header and pattern
        persona_html = f"""
        <div class="persona-card">
            <div class="persona-header" style="color: {intervention['colour']};">
                ✦ {intervention['persona']}
            </div>
            <div class="persona-pattern">{intervention['pattern'].replace('_', ' ')}</div>
        </div>
        """
        st.markdown(persona_html, unsafe_allow_html=True)

        # Render intervention text as markdown to support formatting (**bold**, ##headers, etc.)
        st.markdown(intervention['intervention'])

        # Show image or placeholder
        persona_key = None
        for key, persona in PERSONAS.items():
            if persona["name"] == intervention["persona"]:
                persona_key = key
                break

        if persona_key:
            get_persona_image_or_placeholder(persona_key, intervention["colour"])
    else:
        st.markdown(
            '<div class="listening-placeholder">🎧 Listening...</div>',
            unsafe_allow_html=True,
        )

    # Intervention history section — show only interventions from previous turns
    fired_interventions = []
    for idx in range(min(st.session_state.display_turn - 1, len(events))):
        event = events[idx]
        if event["intervention"]:
            fired_interventions.append({
                "turn_number": idx + 1,
                "intervention": event["intervention"],
            })

    if fired_interventions:
        st.markdown("---")
        st.markdown("**Intervention History**")

        # Mapping of persona names to colored circle emojis
        persona_emoji = {
            "The Anarchist": "🟣",
            "The Cartographer": "🟢",
            "The Fool": "🟠",
            "The Devil's Advocate": "🔴",
            "The Industry SME": "🔵",
        }

        for i, item in enumerate(reversed(fired_interventions)):
            intervention_data = item["intervention"]

            # Create expander label with colored emoji indicator and persona name
            emoji = persona_emoji.get(intervention_data["persona"], "•")
            expander_label = f'{emoji} {intervention_data["persona"]} — Turn {item["turn_number"]}'

            with st.expander(expander_label, expanded=False):
                # Full intervention text
                st.markdown(intervention_data["intervention"])

                # Show image if available
                persona_key = None
                for key, persona in PERSONAS.items():
                    if persona["name"] == intervention_data["persona"]:
                        persona_key = key
                        break

                if persona_key:
                    get_persona_image_or_placeholder(persona_key, intervention_data["colour"])

    # Show turn progress
    st.markdown("---")
    st.markdown(f"**Turn {st.session_state.display_turn} of {len(events)}**")
    st.progress(
        min(st.session_state.display_turn / len(events), 1.0), text="Progress"
    )
