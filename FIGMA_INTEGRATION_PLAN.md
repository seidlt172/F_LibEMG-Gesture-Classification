# Figma Make Widget Integration Plan

## Executive Summary

You have **12 beautifully designed widgets** from Figma Make that are currently a **design reference gallery** (standalone project with category filters). Your task is to **extract their visual essence** and integrate them into the **existing participant-facing React cockpit** (`car_widgets_react/src/main.tsx`) **without modifying the middleware, study logic, or event handling**.

**Key constraint**: The Figma Make export uses Tailwind CSS + shadcn components. Your main app uses **plain CSS**. This is **NOT a blocker** — we will translate the visual designs to plain CSS equivalents.

---

## 1. WHAT THE FIGMA MAKE CODE REPRESENTS

### Design Reference Gallery (Current State)
```
car_widgets_react/design_refs/src/app/components/figma/
├── src/
│   ├── main.tsx                          ← Entry point
│   ├── app/
│   │   ├── App.tsx                       ← Gallery UI + category filters
│   │   └── components/
│   │       ├── figma/
│   │       │   ├── Widget1Voice.tsx      ← Music (voice)
│   │       │   ├── Widget2Voice.tsx      ← Call incoming (voice)
│   │       │   ├── Widget3Voice.tsx      ← Messages (voice)
│   │       │   ├── Widget4Voice.tsx      ← Navigation (voice)
│   │       │   ├── Widget5Gesture.tsx    ← Music (gesture)
│   │       │   ├── Widget6Gesture.tsx    ← Climate/Seat (gesture)
│   │       │   ├── Widget7Gesture.tsx    ← Navigation (gesture)
│   │       │   ├── Widget8Gesture.tsx    ← Ambient light (gesture)
│   │       │   ├── Widget9VoiceAndGesture.tsx   ← Navigation (combined)
│   │       │   ├── Widget10VoiceAndGesture.tsx  ← Ambient light (combined)
│   │       │   ├── Widget11VoiceAndGesture.tsx  ← Music (combined)
│   │       │   └── Widget12VoiceAndGesture.tsx  ← Call incoming (combined)
│   │       └── ui/                       ← shadcn/ui components (Radix UI + Tailwind)
│   └── imports/                          ← Generated assets (SVG paths, etc.)
├── package.json                          ← Tailwind + shadcn deps
├── vite.config.ts
└── README.md
```

### What It Does
- **12 self-contained widget components** rendered as a grid gallery
- **Category filtering**: "All Widgets" | "Voice" | "Gesture" | "Voice + Gesture"
- **Fixed card size**: ~178px × 204px (automotive proportions)
- **Dark HMI theme**: #181818 background, #252530 cards, accent colors
- **Use case**: Design showcase / component reference

### What It Does NOT Do
- Does NOT handle real study events
- Does NOT talk to middleware
- Does NOT track state changes
- Is NOT the participant-facing cockpit
- Should NOT be directly copied into the real app

---

## 2. WIDGET MAPPING TABLE

### All 12 Figma Widgets → Study Domains + Conditions

| Figma Widget | ID | Domain | Label | Study Condition(s) | Content | Color |
|---|---|---|---|---|---|---|
| Widget1Voice | W1 | `audio` | Musik | Voice only | Music player (now playing) | Blue |
| Widget2Voice | W2 | `calls` | Anruf | Voice only | Incoming call (accept/decline) | Green/Red buttons |
| Widget3Voice | W3 | `messages` | Nachrichten | Voice only | Message (read/interact) | Blue |
| Widget4Voice | W4 | `navigation` | Navigation | Voice only | Route selection | Blue |
| Widget5Gesture | W5 | `audio` | Musik | Gesture only | Music player (gesture variant) | Purple |
| Widget6Gesture | W6 | `climate` | Klima | Gesture only | Seat heater level (+/− buttons) | Orange |
| Widget7Gesture | W7 | `navigation` | Navigation | Gesture only | Route selection (gesture variant) | Purple |
| Widget8Gesture | W8 | `ambient_light` | Ambiente | Gesture only | Ambient light control | Purple |
| Widget9VoiceAndGesture | W9 | `navigation` | Navigation | CAN use both | Route selection (dual modality) | Blue+Purple |
| Widget10VoiceAndGesture | W10 | `ambient_light` | Ambiente | CAN use both | Ambient light (dual modality) | Blue+Purple |
| Widget11VoiceAndGesture | W11 | `audio` | Musik | CAN use both | Music player (dual modality) | Blue+Purple |
| Widget12VoiceAndGesture | W12 | `calls` | Anruf | CAN use both | Incoming call (dual modality) | Blue+Purple |

**Key observations:**
- **6 study domains covered**: audio, calls, messages, navigation, ambient_light, climate
- **3 study conditions represented**: voice-only (blue), gesture-only (purple), both (combined)
- **Multiple variants per domain**: e.g., audio has 3 variants (W1, W5, W11)
- **Fixed card size**: All widgets maintain 178×204px for consistency

---

## 3. RECOMMENDED FILE/COMPONENT STRUCTURE

### Phase 1: Plan (this document)
✅ Completed: Analysis of Figma export, mapping, and constraints identified.

### Phase 2: Extract Visual Specs (before implementation)
For each widget, identify:
- Layout structure (grid, flex, nesting)
- Color scheme (primary, accent, text)
- Typography (font sizes, weights)
- Spacing and padding
- Borders and shadows
- Icons/SVG content
- Interactive states (hover, active)

### Phase 3: Refactor Main App Structure
```
car_widgets_react/src/
├── main.tsx
│   ├── App() [unchanged: polling, state management]
│   ├── TopBar [unchanged]
│   ├── MapPanel [unchanged]
│   │
│   ├── SideWidgets
│   │   ├── MusicWidget() [NEW: W1 | W5 | W11]
│   │   ├── CallWidget() [NEW: W2 | W12]
│   │   ├── MessageWidget() [REFACTOR: W3]
│   │   ├── NavigationWidget() [NEW: W4 | W7 | W9]
│   │   ├── AmbientWidget() [REFACTOR: W8 | W10]
│   │   └── ClimateWidget() [REFACTOR: W6]
│   │
│   ├── BottomControls [unchanged]
│   ├── InteractionPopup() [REFACTOR with Figma visual specs]
│   └── FeedbackBadge [unchanged]
│
├── styles.css
│   ├── :root (CSS variables) [EXTEND with new Figma colors]
│   ├── .music-widget* [NEW]
│   ├── .call-widget* [NEW]
│   ├── .message-widget* [NEW]
│   ├── .navigation-widget* [NEW]
│   ├── .ambient-widget* [NEW]
│   ├── .climate-widget* [NEW]
│   └── ...other existing styles...
│
└── types.ts [unchanged — no new state types needed]
```

### Phase 4: Widget Component Pattern
Each widget will follow this pattern:
```tsx
function MusicWidget({ state, activeDomain }: { state: CockpitState; activeDomain?: Domain }) {
  // No new props — read from existing CockpitState
  // No new state logic — all changes via applyDecision()
  return (
    <div className="widget-card music-widget" style={{ ... Figma visual specs ... }}>
      {/* Use existing: state.track, state.audioPlaying, state.volume */}
      {/* Render Figma design layout with current state values */}
    </div>
  );
}
```

**Principles:**
- ✅ Reuse `CockpitState` variables — no new state
- ✅ Read-only rendering — no setState() calls
- ✅ Use Figma layout as template
- ✅ Translate Tailwind → plain CSS classes
- ✅ Condition-based styling (voice/gesture/combined)

---

## 4. SAFE STEP-BY-STEP MIGRATION PLAN

### Step 0: Preparation (Current Phase — Planning Only)
- [x] Locate Figma Make export files
- [x] Analyze all 12 widgets
- [x] Map to study domains
- [x] Understand dependencies (Tailwind ❌, plain CSS ✅)
- [ ] Create visual spec sheet for each widget (NEXT)
- [ ] Review with user before implementation

### Step 1: Middleware Integration Verification
**Before any UI changes:**
1. Confirm event server is running (port 8765)
2. Confirm React dev server is running (port 5174)
3. Test scenario_start → step_update → trial_completed flow
4. Verify middleware sends correct payloads
5. ✅ (Already done in previous session)

### Step 2: Introduce New Color Variables to CSS
```css
:root {
  /* Existing vars */
  --voice: #3b82f6;         /* Blue */
  --gesture: #7c3aed;       /* Purple */
  /* NEW: Combined accent */
  --combined: #5b6fd4;      /* Blue + Purple blend */
  /* NEW: Widget-specific colors */
  --widget-call-accept: #16a34a;  /* Green */
  --widget-call-decline: #dc2626; /* Red */
  --widget-seat-accent: #f97316;  /* Orange */
  /* ... more as needed ... */
}
```

### Step 3: Extract & Translate Figma Widget Specs
For **Widget1Voice** (Music — voice):
1. Open `design_refs/.../Widget1Voice.tsx`
2. Identify layout structure (flex column, spacing, grid)
3. Identify colors (card bg, text, accents)
4. Identify typography (font sizes, weights)
5. Map to plain CSS classes + custom properties
6. Create `.music-widget-voice` class in `styles.css`
7. Create component in `main.tsx`

### Step 4: Implement Widgets One by One
**Recommended order (simple → interactive → complex):**

#### Phase 4A: Static display widgets (lowest risk)
1. **W8 (AmbientWidget — Gesture)** — Simple label + brightness display
2. **W6 (ClimateWidget — Gesture)** — Simple seat level display

#### Phase 4B: Display + minor status widgets
3. **W3 (MessageWidget — Voice)** — Message preview + open/closed state
4. **W5 (MusicWidget — Gesture)** — Music display with pause/play toggle

#### Phase 4C: Enhanced display widgets
5. **W1 (MusicWidget — Voice)** — Full player (now playing, artist, volume)
6. **W10 (AmbientWidget — Combined)** — Dual-mode ambient control

#### Phase 4D: Interactive widgets (higher complexity)
7. **W2 (CallWidget — Voice)** — Incoming call with accept/decline
8. **W6 (ClimateWidget — Gesture)** — Seat heating with +/− buttons
9. **W4, W7, W9 (NavigationWidgets)** — Route selection
10. **W12 (CallWidget — Combined)** — Dual-mode call handling
11. **W11, W9 (Music/Nav — Combined)** — Multi-input variants
12. **W12 (Call — Combined)** — Final complex widget

### Step 5: Test Each Widget
After implementing each widget:
1. Refresh browser (http://127.0.0.1:5174/)
2. Verify visual appearance vs. Figma screenshot
3. Test middleware event triggering
4. Check responsive behavior
5. Verify state updates on scenario_start/step_update
6. Run `npm run build` (check for errors)
7. Run tests: `npm test` (if applicable)

### Step 6: Final Integration
1. Ensure all 12 widgets appear in correct conditions
2. Verify middleware contract unchanged
3. Test full study flow (multiple scenarios)
4. Performance check (no lag on rapid events)
5. Accessibility review (ARIA labels, keyboard nav)

### Step 7: Cleanup
1. Remove design_refs gallery from build (or keep as optional reference)
2. Update documentation
3. Commit final changes
4. Tag release version

---

## 5. WHICH WIDGET TO START WITH & WHY

### Recommendation: START WITH **Widget1Voice (Music — Voice)**

**Why this one?**

| Criteria | Score | Reason |
|---|---|---|
| **Simplicity** | ⭐⭐⭐ | Reuses existing `state.track`, `state.audioPlaying`, `state.volume` |
| **Coverage** | ⭐⭐⭐ | Establishes pattern for voice-modality widgets |
| **User value** | ⭐⭐⭐ | Visible, high-interest domain (music) |
| **Risk** | ⭐ (low) | No new state logic, display-only, existing state vars |
| **Learning** | ⭐⭐⭐ | Shows Tailwind→CSS translation, layout patterns, color handling |

**What Widget1Voice demonstrates:**
- ✅ Fixed card layout (178×204px)
- ✅ Album art rendering (gradient background)
- ✅ Text content (track name, artist)
- ✅ Status display (currently playing)
- ✅ Blue accent color (voice modality)
- ✅ Interactive elements position (play/pause button visual)

**Implementation complexity**: LOW
- Copy existing `state.track` → display as title
- Use `state.audioPlaying` to show play/pause icon
- Use `state.volume` to display volume level
- Apply Figma layout via CSS grid/flex
- Convert Tailwind colors to plain CSS variables

**Alternative starting point**: If you prefer even simpler:
- **Widget8Gesture (Ambient Light — Gesture)** — Just label + brightness number
- But W1 is better for learning the full pattern

---

## 6. RISKS, CHALLENGES & MITIGATIONS

### Risk 1: Tailwind Dependency Mismatch ❌
**Problem**: Figma export uses Tailwind; main app doesn't.
**Severity**: Medium (not a blocker)
**Mitigation**: 
- ✅ Extract visual specs (spacing, colors, fonts) from Figma components
- ✅ Translate to plain CSS custom properties + classes
- ✅ Create CSS equivalents for each widget
- ✅ No Tailwind installation required

### Risk 2: Component Prop Incompatibility ❌
**Problem**: Figma widgets are static (no props); study app needs state-driven rendering.
**Severity**: Low (easily resolved)
**Mitigation**:
- ✅ Accept `state` + `activeDomain` props in new widgets
- ✅ Map `CockpitState` variables to Figma template display
- ✅ Use conditional rendering for conditions (voice/gesture/combined)

### Risk 3: SVG Icon Asset Loss ❌
**Problem**: Figma uses embedded SVGs from generated `svg-*.ts` files.
**Severity**: Low (icons are not critical)
**Mitigation**:
- ✅ Replace embedded SVGs with emoji (existing pattern)
- ✅ Or manually simplify SVG to inline code
- ✅ Or use lucide-react icons if needed (new dep, ask first)

### Risk 4: Middleware Event Handling Disruption ⚠️
**Problem**: Breaking changes to `applyPayload()` or `CockpitState` could break event flow.
**Severity**: HIGH (study-breaking)
**Mitigation**:
- ✅ **DO NOT modify `applyPayload()` logic**
- ✅ **DO NOT add new state variables to `CockpitState`**
- ✅ **DO NOT add middleware calls**
- ✅ **Only refactor rendering layer (JSX + CSS)**
- ✅ Keep state management untouched

### Risk 5: Performance Degradation 🚀
**Problem**: 12 widgets polling every 300ms could cause lag.
**Severity**: Low (unlikely given widget simplicity)
**Mitigation**:
- ✅ Each widget renders from `state` (memoized)
- ✅ No additional polling loops
- ✅ CSS animations only (no JavaScript animations)
- ✅ Test build with `npm run build` to verify bundle size

### Risk 6: Study Flow Contamination 🔴
**Problem**: Accidentally modifying study logic while editing widgets.
**Severity**: CRITICAL
**Mitigation**:
- ✅ **Only edit `main.tsx` JSX and `styles.css`**
- ✅ **DO NOT touch `types.ts` unless adding optional fields**
- ✅ **DO NOT touch `study_flow.py`, `widget_bridge.py`, middleware**
- ✅ Use version control — commit after each widget
- ✅ Run tests before/after each change

---

## 7. IMPLEMENTATION GUIDELINES

### DO ✅
- Translate Tailwind classes to CSS custom properties
- Use existing `CockpitState` variables
- Create reusable component functions
- Test each widget with real middleware events
- Keep render-only logic (no side effects)
- Use CSS variables for colors/spacing
- Maintain 16px border-radius aesthetic (automotive)
- Test responsive behavior

### DON'T ❌
- **Don't install Tailwind** (unless absolutely approved)
- **Don't add new state variables**
- **Don't modify event handling logic**
- **Don't add middleware calls**
- **Don't create category gallery in study UI**
- **Don't use Figma's Gallery App structure**
- **Don't modify operator GUI or Python scripts**
- **Don't hardcode Figma component logic**

### Tailwind → CSS Translation Examples

| Tailwind | Plain CSS Equivalent |
|---|---|
| `flex flex-col gap-[8px]` | `display: flex; flex-direction: column; gap: 8px;` |
| `text-[12px] font-bold` | `font-size: 12px; font-weight: 700;` |
| `bg-[#252530]` | `background: #252530;` |
| `rounded-[16px]` | `border-radius: 16px;` |
| `text-[#99a1af]` | `color: #99a1af;` |
| `hover:bg-[#303540]` | `.class:hover { background: #303540; }` |

---

## 8. QUESTIONS TO RESOLVE BEFORE IMPLEMENTATION

1. **Calls & Navigation widgets**: Should they appear as:
   - [ ] Permanent sidebar widgets (always visible)?
   - [ ] Only in popup (current state)?
   - [ ] Dynamic (only when task is active)?

2. **Combined modality styling**: When condition="CAN use both":
   - [ ] Combine both accent colors visually?
   - [ ] Show variant selector UI?
   - [ ] Just use blue accent with note?

3. **Interactive elements in widgets**:
   - [ ] Should sidebar widgets have buttons (play/pause, volume up/down)?
   - [ ] Or only show state and respond to popup buttons?
   - [ ] Or both (widget buttons + popup for confirmation)?

4. **SVG icons**:
   - [ ] Keep emoji (🎵📞✉️🗺️💡🔥)?
   - [ ] Replace with Figma SVG code?
   - [ ] Use lucide-react (new dependency)?

5. **Bottom button bar**:
   - [ ] Keep current 4 buttons (Sitzheizung, Ambiente, Anruf, Apps)?
   - [ ] Redesign based on Figma if available?
   - [ ] Make functional or decorative?

6. **Dark theme variants**: 
   - [ ] Keep existing #181818 / #252530?
   - [ ] Adopt Figma's exact color palette?
   - [ ] Blend both?

---

## 9. SUMMARY TABLE: WHAT CHANGES, WHAT DOESN'T

| Component | Status | Change Type | File |
|---|---|---|---|
| **Event polling** | ✅ Keep | None | main.tsx |
| **applyPayload() logic** | ✅ Keep | None | main.tsx |
| **CockpitState variables** | ✅ Keep | None | main.tsx |
| **Middleware contract** | ✅ Keep | None | Middleware/*.py |
| **Study flow** | ✅ Keep | None | scripts/study_flow.py |
| **Operator GUI** | ✅ Keep | None | scripts/gesture_gui.py |
| **TopBar layout** | ⚠️ Keep | Minor styling | main.tsx + styles.css |
| **MapPanel layout** | ⚠️ Keep | Minor styling | main.tsx + styles.css |
| **Widget rendering** | 🔄 Refactor | Complete redesign | main.tsx + styles.css |
| **BottomControls** | ⚠️ Keep | Minor styling | main.tsx + styles.css |
| **InteractionPopup** | 🔄 Refactor | Visual update | main.tsx + styles.css |
| **FeedbackBadge** | ⚠️ Keep | Minor styling | main.tsx + styles.css |
| **CSS variables** | 🆕 Extend | Add new colors | styles.css |

---

## NEXT STEPS

### Immediate Actions:
1. **Review this plan** ← You are here
2. **Answer the 6 questions** (section 8) to clarify behavior
3. **Get user approval** on approach
4. **Create visual spec sheets** for first 3 widgets
5. **Implement Widget1Voice** as proof-of-concept

### Then:
6. **Get feedback** on design translation
7. **Iterate** widget 2 and 3
8. **Batch implement** remaining widgets
9. **Full integration test** with middleware
10. **Final review & cleanup**

---

## APPENDIX: Figma Make Export Structure

```
design_refs/src/app/components/figma/
├── ATTRIBUTIONS.md              ← License/credits
├── README.md                    ← "How to run" instructions
├── default_shadcn_theme.css     ← Tailwind + shadcn defaults
├── package.json                 ← Dependencies (Tailwind, shadcn, etc.)
├── postcss.config.mjs           ← PostCSS config (Tailwind)
├── vite.config.ts               ← Vite bundler config
├── pnpm-workspace.yaml          ← pnpm workspace config
│
├── src/
│   ├── main.tsx                 ← Entry point (createRoot + <App />)
│   ├── app/
│   │   ├── App.tsx              ← Gallery UI (category filters, grid)
│   │   └── components/
│   │       ├── figma/           ← 12 widget components
│   │       │   ├── Widget1Voice.tsx
│   │       │   ├── Widget2Voice.tsx
│   │       │   ├── ...
│   │       │   └── Widget12VoiceAndGesture.tsx
│   │       └── ui/              ← shadcn/ui Radix UI components
│   │           ├── card.tsx
│   │           ├── tabs.tsx
│   │           ├── button.tsx
│   │           └── ... (20+ Radix UI primitives)
│   │
│   ├── imports/                 ← Auto-generated from Figma
│   │   ├── Widget1Voice/
│   │   ├── Widget2Voice/
│   │   └── ...
│   │
│   └── styles/                  ← Global Tailwind directives
│       └── globals.css
│
└── guidelines/
    └── Guidelines.md            ← Design system documentation
```

All widget components are **self-contained** with internal SVG imports and Tailwind classes. No interdependencies.

---

**Document Version**: 1.0  
**Created**: Session with Codex  
**Status**: Ready for review & user approval before implementation
