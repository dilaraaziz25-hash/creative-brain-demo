# Claude Code Prompt — Creative Brain UI Redesign

Redesign app.py completely with a new Teams-style meeting interface.
The engine.py, personas.py and transcript files do NOT change.

## Overall Layout

Full-width, two-column layout:
- Left column (65%): Teams-style avatar grid
- Right column (35%): Creative Brain panel (top) + Live transcript (bottom)

---

## LEFT COLUMN — Avatar Grid

Show a grid of participant avatars. Parse participant names from the 
transcript at startup.

Each avatar is a circle with:
- 1-2 letter initials (e.g. "SA" for Sarah, "MA" for Marcus)
- Coloured background per participant (assign a distinct muted colour 
  to each person consistently throughout the session)
- Name below the circle in small text
- Job title below name in italic muted text

Avatar grid layout: 3 columns, wrap to next row for more participants.

**Active speaker animation:**
When a turn is being displayed, the current speaker's avatar should:
- Scale up slightly (like Teams "speaking" indicator)
- Have a glowing border/ring in their colour
- Show a subtle "speaking" indicator (animated dots or pulse)
- All other avatars return to normal size

Use st.components.v1.html() with CSS animations for the pulse/glow effect.

Participant map for the digital transformation transcript:
- Sarah — Project Lead — initials: SA
- Marcus — IT Director — initials: MA  
- Tom — Operations — initials: TO
- Priya — Finance — initials: PR
- Lisa — HR — initials: LI

Participant map for product roadmap transcript:
- James — CPO — initials: JA
- Nina — Engineering Lead — initials: NI
- Raj — Product Manager — initials: RA
- Clara — UX Lead — CL
- Ben — Sales Director — initials: BE

Participant map for post-merger transcript:
- Helen — Integration Lead — initials: HE
- David — Legacy Co. HR — initials: DA
- Sophie — Acquired Co. HR — initials: SO
- Mark — Legacy Co. Engineering Manager — initials: MK
- Priya — Acquired Co. Engineering Manager — initials: PR

Make the participant detection dynamic — parse names from the 
transcript header automatically so it works for any transcript.

---

## RIGHT COLUMN — Two sections stacked vertically

### TOP SECTION: Creative Brain Panel

Header: "🧠 Creative Brain" in bold

**When no intervention is active:**
Show subtle "Listening..." text with a gentle pulse animation.

**When a persona intervention fires:**
Show a notification card with:

1. Persona name + pattern label (small, muted) — e.g. "The Cartographer · assumption unchallenged"
2. ONE key question — maximum 10 words — in bold, large text
3. A "▾ See full thinking" expandable section (collapsed by default)

The expandable section contains:
- A 2-3 sentence summary of WHY the brain intervened 
  (what pattern it detected in the conversation)
- The full intervention text from the persona
- The stimulus image from cards/{persona_name}/ if available

The key question must be extracted from the intervention text.
Add a field "key_question" to the dispatch_persona() return dict.
Generate the key question as part of the Claude API call in engine.py:
Ask Claude to return both the full intervention AND a separate 
key_question field of maximum 10 words that captures the core 
challenge as a question.

Use JSON response format in dispatch_persona():
{
  "key_question": "Are we solving the right problem here?",
  "intervention": "Full intervention text..."
}

The card should have a left border in the persona's accent colour.
No persona names like "Anarchist" should feel aggressive — 
keep the tone as "The Brain is nudging" not "attacking".

**Intervention history** (below current card):
Same expandable history as before — coloured emoji dot + 
persona name + turn number. Collapsed by default.
Only shows after persona has spoken and presenter continues.

### BOTTOM SECTION: Live Transcript

Header: "📝 Transcript"

Scrolling transcript of turns revealed so far.
Each turn shows:
- Speaker name bold + job title italic muted (smaller than avatar section)
- Speech text
- Coloured left border if that turn triggered an intervention

Auto-scroll to latest turn.

---

## PLAYBACK CONTROLS

Place controls ABOVE the two columns, full width:
- ▶ Play / ⏸ Pause / ▶ Continue (dynamic label as before)
- Next turn → 
- ↺ Reset
- Transcript selector dropdown: choose between available 
  transcript files (transcript.md, transcript_product_roadmap.md, 
  transcript_post_merger.md)

When a different transcript is selected, clear the cache and 
reload with the new transcript.

---

## TRANSCRIPT SELECTOR

Add a dropdown at the top to select which transcript to run:
- "Digital Transformation" (transcript.md)
- "Product Roadmap" (transcript_product_roadmap.md)  
- "Post-Merger Integration" (transcript_post_merger.md)

When transcript changes: clear session state, reload events 
from cache or reprocess via API.

---

## KEY QUESTION GENERATION

Update engine.py dispatch_persona() to request JSON output:

System prompt addition: 
"Respond in JSON format with two fields:
- key_question: a single challenging question of maximum 10 words 
  that captures the core of your intervention
- intervention: your full response as previously instructed"

Parse the JSON response and return both fields in the event dict.
Update events_cache.json structure accordingly.
Delete existing events_cache.json so it regenerates with new structure.

---

## STYLING

- Clean, dark-ish meeting room feel — not pure white
- Avatar circles: 80px diameter on desktop
- Active speaker: scale 1.1, glowing ring, pulse animation
- Brain panel: subtle card with rounded corners, slight shadow
- Transcript: clean, readable, auto-scroll
- Persona accent colours remain the same:
  - Anarchist: #7F77DD
  - Cartographer: #1D9E75  
  - The Fool: #EF9F27
  - Devil's Advocate: #D85A30
  - Industry SME: #378ADD
- Background: #F8F9FA (very light grey, not white)
- Font: system-ui / sans-serif

---

## IMPORTANT NOTES

- engine.py pattern detection logic does NOT change
- personas.py system prompts do NOT change (designer will update later)
- Only app.py and the key_question addition to engine.py change
- Maintain all existing session state logic for play/pause/continue
- Keep file-based caching (events_cache.json)
- Delete events_cache.json at start so key_question field regenerates
- The chime should still play when a persona fires
