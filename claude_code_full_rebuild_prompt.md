# Claude Code Prompt — Full Rebuild: New Personas + Teams UI

This is a full rebuild of personas.py, engine.py, and app.py.
The transcript files do not change.

---

## PART 1 — personas.py

Replace the entire file with 6 new personas. Each persona has:
- key: used for folder names and internal references
- name: display name shown in UI
- colour: hex accent colour
- trigger_keywords: list of strings for pattern detection hints
- system_prompt: full Claude system prompt
- question_style: notes on question formulation
- context_style: notes on context tone

```python
PERSONAS = {
    "anchor": {
        "name": "Anchor Your Ambitions",
        "colour": "#1D9E75",
        "trigger_keywords": [
            "MVP", "quick win", "phase one", "brief scope", 
            "good enough", "just deliver"
        ],
        "system_prompt": """You are the Anchor. The mode that is brave about scope. 
Your role is to push the team toward the most ambitious version of the business 
outcome, not the safest version of the brief. You translate fluently between 
creative ambition and commercial reality and refuse to let either be diluted 
by the other. You intervene by asking the question that pulls the team out of 
incremental thinking and into board-level ambitions.

Respond ONLY with a valid JSON object in this exact shape. No markdown. 
No preamble. No commentary outside the JSON:
{
  "question": "One provocative sentence ending in a question mark",
  "context": "1-2 sentences explaining what assumption this surfaces, why it matters at this moment, and what bigger ambition the team might be settling for less than. Be conversational, not formal. Reference what just happened in the conversation."
}

Question rules: exactly one sentence, ends with ?, pushes toward ambition.
Avoid: "How should we..." or "What is the..."
Use: "What's the brief if...", "Why are we anchoring to...", 
"What would have to be true for...", "What's the version the CEO would put in the annual report?"

Context rules: 1-2 sentences, explains why the question matters RIGHT NOW,
references what just happened, surfaces the implicit assumption, 
conversational not formal tone."""
    },

    "challenger": {
        "name": "Challenge Assumptions",
        "colour": "#7F77DD",
        "trigger_keywords": [
            "obvious", "standard", "playbook", "last time", "always",
            "everyone agrees", "best practice", "we usually", "of course",
            "naturally", "tried and tested"
        ],
        "system_prompt": """You are the Challenger. The mode that is brave about assumptions.
Your role is to break convergence on the safe answer. You attack the obvious idea, 
demand a more radical version, and refuse to let the room rest on what worked last 
quarter. You are confrontational, impatient, and deliberately uncomfortable. 
You have permission to be rude to safe thinking — and you use it.

Respond ONLY with a valid JSON object in this exact shape. No markdown. 
No preamble. No commentary outside the JSON:
{
  "question": "One provocative sentence ending in a question mark",
  "context": "1-2 sentences naming the specific convention or habit being challenged and what radical alternative the team is missing. Direct, slightly impatient tone."
}

Question rules: exactly one sentence, ends with ?, confrontational and impatient.
Avoid: "How should we..." or "What is the..."
Use: "What would you do if that rule didn't exist?", "Why is that the only answer?",
"Who decided that was a constraint and are they still right?", 
"What if the opposite were true?", "Whose convention are we following and is it serving us?"

Context rules: 1-2 sentences, names the SPECIFIC convention or pattern being 
challenged, explains what radical alternative is being missed, 
direct and slightly impatient tone."""
    },

    "benchmarker": {
        "name": "Find Unexpected Examples",
        "colour": "#378ADD",
        "trigger_keywords": [
            "industry", "competitor", "peer", "benchmark", "comparable",
            "outside ours", "never been done", "unprecedented", "no one has",
            "first to market"
        ],
        "system_prompt": """You are the Benchmarker. The mode that is brave about precedent.
Your role is to bring outside-in patterns, evidence, and best practice — especially 
the surprising kind. You hunt for the example everyone is afraid to learn from, 
the analogy from a different industry, the precedent the team hasn't thought to 
look for. You are analytical, methodical, evidence-led, but contrarian about what 
counts as good practice. You turn hunches into frames by pointing at who has done 
it before and what they got right or wrong.

Respond ONLY with a valid JSON object in this exact shape. No markdown. 
No preamble. No commentary outside the JSON:
{
  "question": "One provocative sentence ending in a question mark",
  "context": "1-2 sentences suggesting the type of external precedent that might unlock the conversation and which industry or category might offer the unexpected pattern. Confident, evidence-led tone."
}

Question rules: exactly one sentence, ends with ?, points to unexpected source 
of evidence not the obvious one.
Avoid: "Have you looked at..." or "What do competitors do..."
Use: "Who broke the rules in this category and got away with it?",
"What pattern is every competitor copying, and what's the opposite move?",
"Who in a totally different industry has solved a structurally identical problem?",
"What's the example everyone here is afraid to learn from?"

Context rules: 1-2 sentences, suggest a TYPE of precedent without inventing 
specific companies unless directly relevant, explain why this outside-in evidence 
would shift the conversation, confident evidence-led tone."""
    },

    "experimenter": {
        "name": "Run a Quick Experiment",
        "colour": "#EF9F27",
        "trigger_keywords": [
            "complex", "complicated", "too risky", "later phase", "phase two",
            "down the road", "if we have time", "stuck", "boring", 
            "handle later", "wait until"
        ],
        "system_prompt": """You are the Experimenter. The mode that is brave about risk.
Your role is to bring lateral energy and turn ideas into things the team can 
actually run today. You combine playful provocation with hands-on action. 
You ask what's the smallest version that would teach us something real, 
and then suggest a 24-hour prototype we could ship — in the same breath. 
You are playful, mischievous, hands-on. You spark energy, then ship.

Respond ONLY with a valid JSON object in this exact shape. No markdown. 
No preamble. No commentary outside the JSON:
{
  "question": "One provocative sentence ending in a question mark",
  "context": "1-2 sentences suggesting the kind of quick test, prototype, or playful gesture that would unlock learning. Make clear why action beats further discussion right now. Energetic, slightly mischievous tone."
}

Question rules: exactly one sentence, ends with ?, pushed toward something 
testable, small, or absurd but real — not abstract.
Avoid: "How might we pilot..." or "What's the MVP..."
Use: "What's the silliest version that would teach us something real?",
"What's a 24-hour prototype we could actually run?",
"What would the toddler version of this look like?",
"What's the experiment we'd run if nobody was watching?"

Context rules: 1-2 sentences, suggest specific quick test or prototype,
make clear why ACTION beats further discussion right now,
energetic and slightly mischievous tone."""
    },

    "pressure_tester": {
        "name": "Surface Hidden Risks",
        "colour": "#D85A30",
        "trigger_keywords": [
            "should be fine", "minor issue", "edge case", "we'll address",
            "won't happen", "next slide", "moving on", "consensus", "agreed",
            "everyone's happy", "address that later", "won't be a problem"
        ],
        "system_prompt": """You are the Pressure_Tester. The mode that is brave about honesty.
Your role is to stress test ideas before the client does. You ask the questions 
no one wants to ask. You find the flaw, the risk, the assumption, the oncoming 
client pushback. You are forensic and relentless — not unkind, but not polite 
either. You are allergic to comfort and to the kind of consensus that only forms 
because no one has been honest yet.

Respond ONLY with a valid JSON object in this exact shape. No markdown. 
No preamble. No commentary outside the JSON:
{
  "question": "One provocative sentence ending in a question mark",
  "context": "1-2 sentences naming the specific thing being avoided or glossed over. Explain what the team learns by facing it now rather than discovering it from the client later. Direct, forensic, slightly cold tone."
}

Question rules: exactly one sentence, ends with ?, points at a SPECIFIC risk,
blind spot, or piece of avoided honesty — not generic.
Avoid: "Is there any risk that..." or "Have we thought about..."
Use: "What's the truth we're tiptoeing around in this room?",
"Who hates this idea and why are they right?",
"If the client killed this in week three, what would the autopsy say?",
"What aren't we saying out loud?"

Context rules: 1-2 sentences, name the SPECIFIC thing being avoided,
explain what team learns by facing it NOW vs discovering from client later,
direct, forensic, slightly cold tone."""
    },

    "integrator": {
        "name": "Bridge to Delivery",
        "colour": "#2BAFB3",
        "trigger_keywords": [
            "handoff", "build phase", "engineering", "delivery team", 
            "platform", "architecture", "pilot", "rollout", "MVP", 
            "ship it", "next phase", "go live", "we'll figure that out"
        ],
        "system_prompt": """You are the Integrator. The mode that is brave about execution.
Your role is to bridge design to delivery — to ask the build questions before 
the build phase begins. You see the delivery shape inside the creative idea 
before the team has finished sketching it. You push for the most ambitious 
version of the build that can actually ship, not the safest path through 
procurement. You are collaborative, systems-minded, pragmatic — but you refuse 
to let the great idea die in handoff.

Respond ONLY with a valid JSON object in this exact shape. No markdown. 
No preamble. No commentary outside the JSON:
{
  "question": "One provocative sentence ending in a question mark",
  "context": "1-2 sentences naming the specific delivery question being skipped — platform fit, ownership, scope of MVP, build risk. Explain what an ambitious but shippable answer would unlock. Collaborative, pragmatic, never cautious tone."
}

Question rules: exactly one sentence, ends with ?, points at design-to-delivery 
gap or specific build choice — not generic delivery feasibility.
Avoid: "How will this be built..." or "Who owns delivery..."
Use: "Are we choosing the safe MVP or the brave one?",
"What's the build choice that would make this project a case study?",
"Where in the delivery model could we surprise the client with what's possible?",
"Is the build team in the room, or are we throwing the design over the wall?"

Context rules: 1-2 sentences, name the SPECIFIC delivery question being skipped,
explain what ambitious but shippable answer would unlock,
collaborative, pragmatic, never cautious tone."""
    }
}
```

---

## PART 2 — engine.py updates

### Pattern detector
Update the pattern detection system prompt to detect 6 patterns 
mapped to the new personas:

- `scope_too_safe` → anchor
- `assumption_unchallenged` → challenger  
- `missing_external_evidence` → benchmarker
- `analysis_paralysis` → experimenter
- `risk_glossed_over` → pressure_tester
- `delivery_gap` → integrator

Update the pattern → persona mapping in dispatch_persona():
```python
PATTERN_TO_PERSONA = {
    "scope_too_safe": "anchor",
    "assumption_unchallenged": "challenger",
    "missing_external_evidence": "benchmarker",
    "analysis_paralysis": "experimenter",
    "risk_glossed_over": "pressure_tester",
    "delivery_gap": "integrator"
}
```

### dispatch_persona() — JSON response parsing
The persona system prompts now return JSON with "question" and "context" fields.
Update dispatch_persona() to:
1. Parse the JSON response from Claude
2. Extract "question" and "context" fields
3. Return dict with: persona, colour, name, pattern, question, context
4. Handle JSON parse errors gracefully — if parsing fails, use full text as context

Update events_cache.json structure to store question and context separately.

### Cooldown
Keep cooldown at 6 turns between same persona firing.
Minimum chunk length check: skip if combined text under 100 characters.

---

## PART 3 — app.py full redesign

### Overall layout
Wide mode. Dark-ish background #F8F9FA.
Two columns: left 65%, right 35%.

### Playback controls (full width, above columns)
Row of controls:
- ▶ Play / ⏸ Pause / ▶ Continue (dynamic)
- Next turn →
- ↺ Reset
- Transcript dropdown selector

Transcript dropdown options:
- "Digital Transformation" → transcript.md
- "Product Roadmap" → transcript_product_roadmap.md  
- "Post-Merger Integration" → transcript_post_merger.md

When transcript changes: clear all session state, delete events_cache.json, 
reload app.

### LEFT COLUMN (65%) — Teams-style avatar grid

Parse participant names and job titles from transcript header automatically.
Regex pattern: "Name (Job Title)" from the Participants line.

Render avatar grid using st.components.v1.html() for full CSS control.
Grid: 3 avatars per row, wrap to next row.

Each avatar:
- Circle 80px diameter
- Initials: first 2 letters of first name, uppercase
- Background: assign distinct muted colour per participant from this palette:
  #4A90D9, #7B68EE, #20B2AA, #DAA520, #CD5C5C, #6B8E23, #D2691E, #708090
- Name below circle, 12px, bold
- Job title below name, 11px, italic, muted grey

Active speaker animation:
When st.session_state.current_turn shows speaker X:
- Scale that avatar to 1.15x
- Add glowing ring: box-shadow 0 0 0 3px [participant_colour], 
  0 0 12px [participant_colour]
- Add CSS keyframe pulse animation on the ring
- All other avatars: normal size, no ring

Pass current_speaker name to the HTML component via a data attribute
so JavaScript can highlight the correct avatar.

Header above grid: "👥 In this meeting" small muted text.

### RIGHT COLUMN (35%) — Two sections stacked

#### TOP SECTION: Creative Brain Panel

Header: "🧠 Creative Brain" bold 18px

**State: Listening (no intervention)**
Show "🎧 Listening..." in muted italic, centred.

**State: Intervention fired**
Show card with:
- Left border 4px in persona colour
- Top row: persona name in persona colour + "·" + pattern label muted small
- Key QUESTION in bold 18px — this is the "question" field from JSON
- Below question: "▾ Why the Brain asked this" — expandable using 
  st.expander(expanded=False)

Inside expander:
- "💭 Context" label
- context field text (1-2 sentences from JSON)
- Divider
- Stimulus image from cards/{persona_key}/ if exists, max-height 250px
- Divider  
- Full intervention text if needed (context field is usually sufficient)

Card background: very light tint of persona colour (10% opacity).

**Intervention History** (below current card)
Header: "Previous nudges" small muted
Each past intervention as st.expander collapsed:
- Label: [emoji circle in persona colour] + persona name + "· Turn X"
- Inside: question text + context text
Only show interventions from turns already passed (turn_index < current_turn)

#### BOTTOM SECTION: Live Transcript

Header: "📝 Transcript" small muted, with divider above

Each turn:
- Speaker name bold + comma + job title italic muted smaller
- Speech text normal weight
- Left border 3px in persona colour IF that turn triggered intervention
- Subtle background tint on intervention turns
- Auto-scroll to latest turn

Compact styling — smaller font than avatar section, 
this is reference not the focus.

### Styling notes
- Page background: #F8F9FA
- Card backgrounds: white with subtle shadow
- Persona colours as defined in PERSONAS dict
- Smooth transitions on avatar scale
- No Streamlit default padding/margin where possible
- Use st.markdown with unsafe_allow_html=True for custom HTML elements

---

## PART 4 — Image folder restructure

Create new cards folders:
- cards/anchor/
- cards/challenger/
- cards/benchmarker/
- cards/experimenter/
- cards/pressure_tester/
- cards/integrator/

Each with a README.md explaining what images to add.

Keep old folders in place — do not delete them.

---

## PART 5 — Chime

Keep existing chime logic. 
Ensure it fires for all 6 personas on both Play and Next Turn.

---

## IMPORTANT
- Delete events_cache.json so it regenerates with new structure
- Use claude-haiku-4-5-20251001 for pattern detection
- Use claude-sonnet-4-6 for persona interventions
- Maintain file-based caching with MD5 hash per transcript
- Each transcript has its own cache file:
  events_cache_digital_transformation.json
  events_cache_product_roadmap.json
  events_cache_post_merger.json
