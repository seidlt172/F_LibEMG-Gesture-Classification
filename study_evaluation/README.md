```text
,------.,--.   ,--.       ,--.                                            ,-.   
|  .---'|   `.'   | ,---. `--',--,--,  ,---.  ,---. ,--.--. ,---.     .--.'. \  
|  `--, |  |'.'|  || .-. |,--.|      \| .-. :| .-. :|  .--'(  .-'     '--' |  | 
|  `---.|  |   |  |' '-' '|  ||  ||  |\   --.\   --.|  |   .-'  `)    .--. |  | 
`------'`--'   `--'.`-  / `--'`--''--' `----' `----'`--'   `----'     '--'.' /  
                   `---'                                                  `-'   
```

# 🚗💨 EMGineers: Multimodal In-Vehicle Assistant Study Evaluation

![Study Status: 100% Complete](https://img.shields.io/badge/Study%20Status-100%25%20Complete-00c8a5?style=for-the-badge) ![ACM CHI Standard](https://img.shields.io/badge/CHI%20Standard-Ready-00c8a5?style=for-the-badge) ![Data: N=18 Participants](https://img.shields.io/badge/Quantitative-N%3D18%20Logs-00c8a5?style=for-the-badge) ![Qualitative: N=18 Interviews](https://img.shields.io/badge/Qualitative-N%3D18%20Interviews-blue?style=for-the-badge)

Welcome to the central evaluation repository of the **EMGineers** research team! This folder contains our empirical dataset, non-parametric inferential statistics pipeline, publication-ready vector figures in our signature **Turquoise Color Theme**, and exhaustive qualitative interview transcriptions for our multimodal automotive cockpit study.

---

## 🌟 Executive Summary & Achievements

Our study evaluates interaction efficiency, cognitive load, and safety in an automotive driving simulator across three experimental paradigms:
1. 🎙️ **Voice Only** (Local Whisper speech recognition & Ollama intent parsing)
2. 🖐️ **Gesture Only** (MindRove EMG armband micro-gesture classification)
3. 🚀 **Multimodal Combination (Voice + Gesture)** (Seamless middleware fusion)

> [!TIP]
> **Key Scientific Finding:** While pure voice commands provide high confidence for complex navigation tasks, **multimodal interaction** significantly reduces physical demand and allows drivers to adaptively switch modalities based on driving situation and cognitive load!

---

## 📂 Repository Architecture

```text
study_evaluation/
├── raw_data/
│   ├── participant_logs/      # 📊 Quantitative interaction logs (P01–P18, JSONL format)
│   └── questionnaires/        # 📋 Subjective ratings (NASA-TLX, SUS) & Qualitative O-Töne (P01–P18)
├── scripts/
│   ├── evaluate_study_data.py # ⚙️ Automated statistical evaluation & plotting pipeline
│   └── create_qualitative_table.py # 🛠️ Script for generating qualitative master tables
└── results/
    ├── figures/               # 🎨 Publication-grade Turquoise vector plots (PNG & PDF)
    ├── statistics/            # 📈 Complete significance reports (Friedman, Wilcoxon, Cohen's r)
    └── qualitative/           # 🗣️ Exhaustive thematic synthesis & behavioral video analysis
```

---

## 📊 1. Raw Study Data (`raw_data/`)

### 🕹️ Simulator Logs (`raw_data/participant_logs/`)
Contains 18 high-precision JSON Lines (`.jsonl`) logs capturing real-time user behavior in the driving simulator ($N=18$):
* **Temporal Metrics:** Task Completion Times (TCT in ms) per trial and task domain.
* **System Metrics:** Intent recognition confidence scores, clarification loop counts, and Wizard-of-Oz fallback activations.
* **Modalities:** Complete coverage of Voice, Gesture, and Multimodal interaction conditions.

### 📋 Questionnaires & Qualitative O-Töne (`raw_data/questionnaires/`)
* **`demographic_data.csv`**: Participant demographics ($N=23$), screening for motor impairments, driving frequency, and tech experience.
* **`round1_single_modalities_nasatlx_sus.csv`**: Baseline NASA-TLX (6 workload subscales, 1–7) and SUS (10 usability items, 1–5) ratings.
* **`round3_multimodal_nasatlx_sus.csv`**: Post-study NASA-TLX and SUS evaluations for the combined multimodal interaction paradigm.
* **`qualitative_interview_raw_responses.csv`**: **Complete verbatim transcription ($N=18$)** of open-ended participant interviews, documenting ergonomic friction points, wake-word annoyance (*"Hey Carla"*), visual delay feedback, and real-world automotive preferences.

---

## ⚙️ 2. Automated Statistical Pipeline (`scripts/`)

Our master script `evaluate_study_data.py` automates the entire quantitative analysis from raw JSONL parsing to LaTeX-ready statistical reporting:

```bash
python study_evaluation/scripts/evaluate_study_data.py
```

### 🔬 What the Pipeline Computes:
1. **Descriptive Statistics:** Calculates Means ($M$), Standard Deviations ($SD$), Medians, Interquartile Ranges ($IQR$), and exact **95% Confidence Intervals ($\pm 95\% \text{ CI}$)**.
2. **Non-Parametric Inferential Tests:**
   * **Friedman Test ($\chi^2$)** with Kendall's $W$ effect sizes for repeated-measures variance across modalities.
   * **Wilcoxon Signed-Rank Post-Hoc Tests** with **Holm-Bonferroni correction** and Cohen's $r$ effect sizes for pairwise comparisons.
   * **Chi-Square Test of Independence ($\chi^2$)** for binary task success rates.
3. **Automated Export:** Generates high-resolution Turquoise charts in `results/figures/` and writes a complete report to `results/statistics/statistical_analysis_report.md`.

---

## 🏆 3. Results & Publication Assets (`results/`)

### 🎨 Signature Turquoise Figures (`results/figures/`)
Formatted strictly to ACM CHI publication guidelines with clean gridlines, bold typography, and 95% CI error bars:
* 📉 **`tct_plot.png / .pdf`**: Task Completion Time distribution across interaction conditions.
* 🔄 **`robustness_plot.png / .pdf`**: Clarification loops vs. internal intent recognition confidence.
* 🧠 **`nasatlx_plot.pdf`**: Multi-dimensional NASA-TLX cognitive workload profile.
* ⭐ **`sus_plot.pdf`**: System Usability Scale benchmark comparison.

### 📈 Statistical Summaries (`results/statistics/`)
* **`statistical_analysis_report.md`**: The definitive quantitative reference document. Ready for instant integration into academic research papers or thesis chapters.

### 🗣️ Qualitative Synthesis (`results/qualitative/`)
* **`qualitative_analysis_synthesis.md`**: Exhaustive analysis synthesizing participant interviews and video behavioral observations into **7 core themes** (Safety & Glance Behavior, Physical Demand, Sources of Confusion, Wake-Word Frustration, Multimodal Preference Rationale, Novelty Effect, and Autonomous Driving Context).
* **`qualitative_themes_summary.csv`**: Structured mapping matrix linking quotes, participant IDs, and hypotheses ($H1, H2, H3$).

---

<div align="center">
  <b>Made with 🔥, precision, and architectural excellence by the EMGineers Team.</b>
</div>
