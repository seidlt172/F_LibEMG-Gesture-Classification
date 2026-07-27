# Qualitative Study Synthesis: Post-Study Interviews & Video Analysis

This document synthesizes the qualitative findings from the post-study semi-structured interviews and video behavioral observations across all analyzed participants ($N = 18$ valid study trials, plus pilot feedback). 

These insights complement the quantitative metrics (TCT, Clarification Loops, NASA-TLX, SUS) and provide deep contextual explanations for the observed user behaviors and modality preferences reported in **Section 5.3 (Qualitative Results)** and **Section 6 (Discussion)** of the paper.

---

## 1. Safety Risks & Glance Behavior: The Cost of Waiting for Feedback
* **Observation**: In the video recordings, the 6 critical driving errors / simulator collisions observed across the cohort (e.g., in trials for `P01`, `P03`, `P05`, `P08`, `P11`, `P12`, `P16`) did **not** occur during the active execution of speech or gesture commands. Instead, they occurred **during or immediately after the LLM clarification/waiting loop**, when participants stared at the screen waiting for visual/audio confirmation (e.g., missing a traffic light, drifting out of lane, or grazing the guardrail).
* **Participant Feedback**: `P16` explicitly noted that *"the most critical and distracting moment was waiting for the system's confirmation."*
* **Scientific Relevance**: This finding strongly validates the core design argument of our paper: **latency and transparent, immediate feedback** are safety-critical in automotive UIs. When LLM clarification loops add delay, visual attention shifts away from the primary driving task.

---

## 2. Physical Demand of Gesture Control (Arm Fatigue & Cornering)
* **Observation**: While gestures were praised for quick, discrete actions (e.g., volume control, accepting calls), repeated mid-air gesturing caused physical fatigue. In one video instance, `P12` drifted toward the guardrail while attempting to perform a gesture during a sharp curve.
* **Participant Feedback**: Several participants (`P04`, `P06`, `P07`, `P10`) noted physical exertion when holding or repeating gestures. `P06` stated that *"holding the arm up for repeated commands gets tiring quickly and distracts from watching the road."*
* **Scientific Relevance**: Explains the slightly higher **Physical Demand** score in the NASA-TLX for Gesture Only compared to Voice Only, reinforcing that gesture controls must be designed for rapid, single-impulse execution without requiring prolonged arm elevation.

---

## 3. Specific Sources of User Confusion (Not General Modality Rejection)
* **Observation**: User confusion in gesture trials was highly concentrated on two specific interaction points rather than the gesture modality as a whole:
  1. **Thumb Up / Thumb Down Semantics**: `P01`, `P03`, and `P12` showed brief hesitation or confusion in videos when distinguishing between accepting/rejecting an intent versus general confirmation/interruption. In the interview, `P03`, `P09`, and `P12` noted: *"I sometimes mixed up the thumb-up gesture with general confirmation."*
  2. **System Freeze Perception During Loops**: During 2nd-turn LLM clarification loops, `P05`, `P06`, `P08`, `P11`, and `P15` thought the system had frozen because feedback was momentary or silent while processing.
* **Scientific Relevance**: Demonstrates that gesture classification accuracy itself was well-received; errors stemmed from semantic mapping and feedback state visibility.

---

## 4. The 'Hey Carla' Wake-Word Frustration
* **Observation**: At least 5 participants (`P03`, `P05`, `P08`, `P09`, `P16`) explicitly mentioned that repeatedly speaking the wake-word (*"Hey Carla"*) became annoying, especially during error recovery or multi-step dialogues.
* **Scientific Relevance**: This is a voice-exclusive friction point. In contrast, EMG gesture control requires no wake-word activation, highlighting a major ergonomic advantage of gestural shortcuts for quick interventions.

---

## 5. Overwhelming Preference for the Multimodal Combination (H3 Validation)
* **Observation**: An overwhelming majority of participants (`P01`, `P02`, `P03`, `P06`, `P09`, `P11`, `P12`, `P13`, `P15`, `P17`, `P18`) independently stated in the interviews that the **Combined Multimodal System (Round 3)** was their absolute favorite interaction method.
* **Core Rationale**: Participants developed an intuitive division of labor:
  - **Gestures** for immediate, simple, binary actions (e.g., skipping tracks, adjusting volume, accepting navigation prompts).
  - **Voice** for complex, semantic, or exploratory tasks (e.g., searching for a specific song, entering destination addresses), or when both hands needed to remain gripping the steering wheel in dense traffic.
* **Scientific Relevance**: This qualitative consensus perfectly explains why **Round 3 achieved the highest System Usability Scale (SUS) scores and lowest overall frustration**, proving our core hypothesis (**H3**): users naturally switch modalities based on driving situation and task complexity rather than relying on a single input channel.

---

## 6. The Novelty & Habituation Confound
* **Observation**: Multiple participants explicitly highlighted a strong learning and habituation curve with the EMG gesture armband.
* **Participant Feedback**:
  - `P06`: *"At first, gesture control felt strange and unfamiliar, but after a few tries it became extremely pleasant."*
  - `P11`: *"It was unfamiliar at the beginning, but once I got the hang of it, it was actually fun to use."*
* **Scientific Relevance**: Stresses that initial cognitive workload or hesitation with EMG gestures is largely a **novelty effect**. Long-term driver adaptation would likely further reduce task completion times and physical tension.

---

## 7. Conditional Acceptance: Highly Autonomous vs. Active City Driving
* **Observation**: In discussing real-world automotive adoption, `P03`, `P07`, and `P09` argued that gestural interaction is exceptionally well-suited for **Level 2+ / Level 3 semi-autonomous driving** (e.g., highway cruising or traffic jams), where the driver's hands are not actively maneuvering tight turns. In active, complex city traffic, they preferred voice commands to keep both hands fixed on the wheel.
* **Scientific Relevance**: Provides a sophisticated, nuanced design guideline for future automotive UI research—multimodal systems should dynamically adapt their command prompts and input sensitivity based on the vehicle's automation level and current driving context.
