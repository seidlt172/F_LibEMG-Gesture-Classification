# Pilot Study Design: EMG + Voice In-Car Interaction

## 1. Study Purpose

This pilot study evaluates an in-car interaction concept that combines spoken
commands with subtle EMG-based micro-gestures. The system is treated as a
research prototype, not as a production-ready automotive interface.

The central idea is that voice can express explicit semantic intent, while EMG
micro-gestures can support fast, subtle, and low-visual-demand interaction for
confirmation, rejection, disambiguation, selection, and parameter adjustment.

The pilot compares three interaction conditions:

| Condition | Description |
| --- | --- |
| Voice only | Users complete each task using spoken commands only. |
| Gesture only | Users complete each task using EMG micro-gestures only. |
| CAN use both | Users may freely use voice, EMG gestures, or both in any natural combination. |

The multimodal condition must not require simultaneous voice and gesture input.
Users may combine modalities simultaneously, successively, redundantly, or may
choose one modality even though both are available. These natural usage patterns
are part of the study outcome.

This document specifies a first-stage pilot study. A later main study may use a
more realistic cockpit mockup or driving simulator, but the current pilot focuses
on feasibility, interaction behavior, scenario balance, logging quality, and
directional evidence.

## 2. Research Questions and Hypotheses

### Research Questions

RQ1: Does allowing users to combine voice and EMG gestures improve interaction
efficiency for in-car secondary tasks compared to single-modality interaction?

RQ2: Does multimodal input improve interaction robustness when recognition is
uncertain or when a task requires confirmation, rejection, or disambiguation?

RQ3: How do users naturally distribute intent across voice and EMG gestures when
both modalities are available?

RQ4: Does multimodal interaction reduce perceived workload for tasks involving
selection, confirmation, or adjustment?

### Exploratory Hypotheses

H1 - Efficiency: Multimodal interaction may reduce task completion time compared
to voice-only and gesture-only interaction in tasks that require disambiguation,
selection, or confirmation.

H2 - Robustness: Combining EMG micro-gestures and voice may improve intent
recognition robustness compared to single-modality interaction, measured through
fewer failed attempts, fewer wrong recognitions, fewer clarification cycles, and
fewer Wizard-of-Oz interventions.

H3 - Workload: Allowing users to combine EMG micro-gestures and voice may reduce
perceived workload compared to voice-only and gesture-only interaction,
especially for tasks requiring selection, confirmation, or parameter adjustment.

These hypotheses are exploratory. The pilot is not intended to support strong
confirmatory claims or claims about superiority over menu-based interaction,
because no menu baseline is included.

## 3. Prototype Interaction Vocabulary

The gesture vocabulary follows the current prototype classes:

| Gesture class | Label | Intended interaction role |
| --- | --- | --- |
| 0 | Rest | Neutral state, no intentional command. |
| 1 | Daumen hoch | Accept, confirm, approve, resume. |
| 2 | Swipe | Reject, dismiss, next option, skip. |
| 3 | Handgelenk drehen | Regulate a continuous parameter such as volume, brightness, or heating. |
| 4 | Zeigen/Tippen | Select, point to an option, choose an item. |

The voice vocabulary is intentionally flexible in the pilot. Participants may
use natural short commands, for example "accept the call", "reject it", "make it
brighter", or "select the faster route". The Wizard or interaction manager maps
recognized utterances to the intended task action.

## 4. Study Design

### Design Type

The pilot uses a within-subject design. Each participant completes tasks in all
three interaction conditions.

Condition order should be counterbalanced across participants to reduce order
and learning effects. With a small pilot sample, use a Latin-square inspired
rotation:

| Order group | Block 1 | Block 2 | Block 3 |
| --- | --- | --- | --- |
| A | Voice only | Gesture only | CAN use both |
| B | Gesture only | CAN use both | Voice only |
| C | CAN use both | Voice only | Gesture only |

If six participants are recruited, assign two participants to each order group.
If fewer participants are recruited, distribute participants as evenly as
possible across the order groups.

### Pilot Sample

Target pilot sample: 6 to 8 participants.

The pilot sample is used to evaluate feasibility, task clarity, scenario
balance, logging reliability, recognition failure handling, and subjective
feedback. The pilot is not powered for confirmatory statistical inference.

### Setting

The pilot may be run as a desktop or low-fidelity cockpit-style setup. The
automotive context is represented through task framing, scenario prompts, and
system feedback. Driving performance, lane keeping, and glance behavior are not
primary pilot measures.

A later main study may move to a stationary cockpit mockup or driving simulator.
If a simulator is used later, distraction-related measures such as glance
behavior or driving performance can be added.

## 5. Scenario Set

### Main 12-Scenario Design

Each row represents one interaction problem type. The three condition-specific
tasks do not need to be identical, but they must be balanced in task difficulty,
expected completion time, number of interaction steps, cognitive complexity,
gesture difficulty, and need for disambiguation.

| Category | Voice only | Gesture only | CAN use both |
| --- | --- | --- | --- |
| Accept / Reject | An incoming call appears. Accept or reject it using voice only. | A suggested song appears. Accept or reject it using EMG gesture only. | A navigation route suggestion appears. Accept or reject it using voice, gesture, or both. |
| Select + Adjust | Select the volume control and make it louder using voice only. | Select seat heating and increase it using EMG gesture only. | Change the ambient light color and make it brighter using voice, gesture, or both. |
| Browse + Select | Open a received message and close it again using voice only. | Browse route options and select one route using EMG gesture only. | Resume paused media and skip to the next song using voice, gesture, or both. |
| Confirm + Modify | Accept navigation guidance and increase announcement volume using voice only. | Accept an ambient light suggestion and increase brightness using EMG gesture only. | Accept an incoming call and regulate volume using voice, gesture, or both. |

This table yields 12 total trials per participant:

- 3 interaction conditions.
- 4 task categories.
- 1 scenario per condition and category.

### 9-Scenario Fallback

If the pilot session becomes too long, remove the Confirm + Modify category. It
is the least cleanly comparable category because it combines acceptance with a
second parameter adjustment and can introduce more domain-specific variation.

The shortened study keeps:

- Accept / Reject.
- Select + Adjust.
- Browse + Select.

This yields 9 total trials per participant.

### Scenario Balancing Rules

When refining prompts, preserve these balancing rules:

- Do not make the multimodal scenario simpler than the single-modality scenarios.
- Avoid comparing a simple voice-only command with a complex gesture-only
  route-selection sequence.
- Keep the number of intended interaction steps comparable within each category.
- Keep the semantic task type comparable within each row.
- Use the same success criteria across conditions wherever possible.
- Treat task domain as context, not as the primary comparison.

## 6. System Behavior

The system should provide short, transparent feedback after recognized input.
It should not silently guess when recognition is uncertain.

| System state | Behavior | Example feedback |
| --- | --- | --- |
| Recognized confidently | Execute the action and provide short confirmation. | "Call accepted." |
| Ambiguous or uncertain | Ask for clarification before executing. | "I detected a swipe. Do you want to reject this option?" |
| Not recognized or invalid | Ask the user to repeat or try again. | "Gesture not recognized. Try again." |

For wrong or unclear inputs, feedback should be minimal and task-oriented. The
interaction manager should distinguish between incorrect recognition, no
recognition, delayed recognition, and Wizard intervention.

## 7. Wizard-of-Oz Backup Protocol

The pilot may use Wizard-of-Oz support if EMG or voice recognition is unreliable.
The Wizard is a fallback layer, not a replacement for logging real recognition
behavior.

Protocol:

1. Real recognition is attempted first and logged.
2. The Wizard observes recognition output and task progress.
3. The Wizard intervenes only after three failed recognition attempts or when the
   system clearly cannot continue.
4. The Wizard triggers the intended system response according to the task script.
5. The intervention is logged explicitly as Wizard-of-Oz intervention.

Recognition outcomes must be coded as:

- Correct recognition.
- Wrong recognition.
- No recognition.
- Delayed recognition.
- Wizard intervention.

Wizard intervention must never be hidden or counted as normal recognition
success.

## 8. Measures

### Efficiency

- Task completion time, measured from task start to successful completion.
- Number of interaction steps.
- Number of repetitions.
- Number of corrections.

### Robustness

- Successful task completion rate.
- Recognition accuracy.
- Number of failed attempts.
- Number of wrong recognitions.
- Number of clarification prompts.
- Number of Wizard-of-Oz interventions.

### Workload and Subjective Experience

- NASA-TLX or short NASA-TLX after each condition block.
- Optional ease-of-use rating.
- Optional perceived naturalness rating.
- Optional perceived confidence rating.
- Post-study interview about modality preference and perceived failure recovery.

Driving performance and glance behavior are excluded from the pilot unless a
driving simulator is explicitly selected later.

## 9. Trial Log Schema

The following fields should be logged for each trial. Logging may be implemented
in software, collected manually by the experimenter, or combined.

| Field | Description |
| --- | --- |
| participant_id | Anonymous participant identifier. |
| trial_id | Unique trial identifier. |
| condition | Voice only, gesture only, or CAN use both. |
| category | Accept/Reject, Select+Adjust, Browse+Select, or Confirm+Modify. |
| scenario_id | Stable scenario identifier. |
| condition_order | Order group A, B, or C. |
| start_timestamp | Timestamp when the task prompt is shown. |
| end_timestamp | Timestamp when the task is successfully completed or aborted. |
| task_completion_time_ms | End minus start in milliseconds. |
| success | Boolean task success flag. |
| interaction_steps | Count of user-system interaction turns. |
| repetitions | Count of user repetitions. |
| corrections | Count of user corrections after a wrong or unclear recognition. |
| clarification_cycles | Count of system clarification prompts. |
| recognition_failures | Count of no-recognition events. |
| wrong_recognitions | Count of incorrect recognition events. |
| recognition_outcome | Correct, wrong, none, delayed, Wizard intervention, or mixed. |
| wizard_intervention | Boolean flag. |
| voice_transcript | Recognized or manually transcribed utterance, if any. |
| gesture_label | Recognized gesture class, if any. |
| gesture_confidence | Gesture confidence where available. |
| voice_confidence | Voice confidence where available. |
| multimodal_usage_pattern | Only for CAN use both condition; see coding scheme below. |
| nasa_tlx_score | NASA-TLX or short NASA-TLX score for the condition block. |
| ease_of_use_rating | Optional subjective rating. |
| naturalness_rating | Optional subjective rating. |
| confidence_rating | Optional subjective rating. |
| notes | Experimenter notes, unusual events, participant comments. |

### Multimodal Usage Coding

For the CAN use both condition, code one primary usage pattern per trial:

| Code | Meaning |
| --- | --- |
| voice_only_available | Participant used only voice although both modalities were available. |
| gesture_only_available | Participant used only gesture although both modalities were available. |
| simultaneous_voice_gesture | Voice and gesture occurred at approximately the same time. |
| sequential_voice_to_gesture | Voice occurred first, then gesture completed, clarified, or confirmed the action. |
| sequential_gesture_to_voice | Gesture occurred first, then voice completed, clarified, or confirmed the action. |
| redundant_voice_gesture | Voice and gesture expressed the same intent redundantly. |

If multiple patterns occur within one trial, code the dominant pattern and note
secondary behavior in the notes field.

## 10. Procedure

### 1. Briefing and Consent

Explain the purpose of the study as an evaluation of interaction modalities for
in-car secondary tasks. Avoid suggesting that multimodal interaction is expected
to be superior.

Explain that the system is a prototype and that some recognition failures may
occur. If Wizard-of-Oz support is used, disclose it appropriately according to
the study ethics requirements.

### 2. Training

Provide a short training phase before each condition:

- Voice only: examples of short spoken commands.
- Gesture only: demonstration and practice of each EMG gesture.
- CAN use both: explanation that participants may use voice, gesture, or both in
  whatever way feels natural.

Training should be long enough for participants to understand the input options,
but not so long that task performance becomes over-practiced.

### 3. Task Blocks

Participants complete one block per condition. Condition order follows the
counterbalancing table.

For each trial:

1. Present the scenario prompt.
2. Start timing when the prompt becomes visible or audible.
3. Let the participant complete the task using the allowed modality or
   modalities.
4. Provide system feedback according to the recognition state.
5. Stop timing when the task is successfully completed or the trial is aborted.
6. Log recognition behavior, Wizard intervention, and experimenter notes.

### 4. Workload Questionnaire

After each condition block, collect NASA-TLX or short NASA-TLX ratings. Optional
ratings for ease of use, naturalness, and confidence can be collected at the same
time.

### 5. Post-Study Interview

Ask short open-ended questions:

- Which condition felt most natural, and why?
- When both voice and gesture were available, how did you decide which modality
  to use?
- Did gestures feel helpful for confirmation, rejection, selection, or
  adjustment?
- Which failures were most disruptive?
- Would you use this type of interaction in a car context?

## 11. Analysis Plan

### Quantitative Analysis

Report descriptive statistics for each condition:

- Mean and median task completion time.
- Success rate.
- Mean number of interaction steps.
- Mean number of repetitions and corrections.
- Mean number of recognition failures and wrong recognitions.
- Mean number of clarification cycles.
- Mean number of Wizard interventions.
- NASA-TLX or short NASA-TLX scores.

Use within-subject comparisons cautiously because the pilot sample is small.
Report effect sizes and confidence intervals where feasible. Statistical tests,
if used, should be described as exploratory.

### Qualitative Analysis

Code post-study interview comments and multimodal trial behavior for:

- Reasons for choosing voice, gesture, or both.
- Situations where gesture felt faster or less visually demanding.
- Situations where voice felt clearer or more expressive.
- Perceived friction in recognition failures.
- Strategies for recovering from errors.
- Whether participants used gestures for confirmation, rejection, selection, or
  adjustment as intended.

The qualitative analysis should help decide whether the multimodal concept is
promising enough for a larger cockpit-mockup or simulator study.

## 12. Pilot Acceptance Criteria

The pilot design is considered methodologically usable if:

- Scenario rows are comparable across conditions.
- The CAN use both condition is not artificially easier than the single-modality
  conditions.
- Participants understand that multimodal input is optional and flexible.
- Recognition behavior is logged separately from Wizard recovery.
- Workload claims do not compare against complex menus or visual menu baselines.
- Logging captures both performance outcomes and natural modality use.
- The study can identify whether a later cockpit-mockup main study is justified.

## 13. Outlook for a Later Main Study

If the pilot indicates that the concept is feasible, a later main study can use a
more realistic cockpit mockup or driving simulator. The main study may increase
sample size, add stronger counterbalancing, refine scenario prompts, and include
additional distraction-related measures.

Potential additions for a later study:

- Stationary cockpit mockup with dashboard-style prompts.
- Driving simulator with lane-keeping or speed-maintenance task.
- Glance behavior or eye-tracking, if technically feasible.
- Larger sample size for confirmatory analysis.
- Improved automatic logging and synchronized voice/gesture timestamps.

These additions should not be retroactively claimed for the pilot.
