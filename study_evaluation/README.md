# Multimodal In-Vehicle Assistant: Quantitative & Qualitative Study Evaluation

This directory contains the complete dataset, statistical evaluation scripts, and generated publication figures for the empirical study on gestural and multimodal in-vehicle interaction.

---

## Directory Structure

```text
study_evaluation/
├── raw_data/
│   ├── participant_logs/      # Interaction logs for N=18 participants (P01 - P18) in JSONL format
│   └── questionnaires/        # Placeholder for subjective questionnaire data (NASA-TLX & SUS - H3)
├── scripts/
│   └── evaluate_study_data.py # Master quantitative evaluation pipeline (H1 & H2)
└── results/
    ├── figures/               # High-resolution publication plots in Turquoise theme (PNG & PDF)
    └── statistics/            # Full statistical analysis reports and significance test summaries
```

---

## 1. Raw Study Data (`raw_data/`)

### Participant Interaction Logs (`raw_data/participant_logs/`)
Contains the complete behavioral event logs recorded during the simulator experiments for all 18 analyzed participants ($N = 18$).
- **Format**: JSON Lines (`.jsonl`)
- **Recorded Metrics**: Task completion times (ms), clarification loops, intent recognition confidence estimates, speech transcriptions, gesture classifications, and Wizard-of-Oz fallback activations across the three experimental conditions:
  1. **Voice Only**
  2. **Gesture Only**
  3. **Multimodal (Voice + Gesture)**

### Subjective Questionnaires (`raw_data/questionnaires/`)
Designated location for the raw survey data exported from Google Forms / Excel regarding:
- **NASA-TLX**: Perceived workload across 6 subscales (Mental Demand, Physical Demand, Temporal Demand, Performance, Effort, Frustration).
- **System Usability Scale (SUS)**: Perceived system usability across 10 standard items.

---

## 2. Evaluation Scripts (`scripts/`)

### Master Evaluation Pipeline (`evaluate_study_data.py`)
Fully automated Python script that reads all 18 participant logs, performs robust non-parametric inferential statistical testing, and generates ACM-style publication graphs.

#### Run the Analysis:
From the repository root, run:
```bash
python study_evaluation/scripts/evaluate_study_data.py
```

#### What the script computes:
1. **Descriptive Statistics**: Means ($M$), Standard Deviations ($SD$), and 95% Confidence Intervals ($\pm 95\% \text{ CI}$) for TCT, loops, confidence, and task success rate.
2. **Inferential Statistics**:
   - **Friedman Test** ($\chi^2(2)$) with **Kendall's $W$** effect sizes for repeated-measures differences across modalities.
   - **Post-hoc Wilcoxon Signed-Rank Tests** with **Holm correction** and **Cohen's $r$** effect sizes for pairwise comparisons.
   - **Chi-Square Test of Independence** ($\chi^2(2)$) for binary task success rates.
3. **Automated Export**: Saves plots directly into `results/figures/` and writes a formatted markdown report into `results/statistics/statistical_analysis_summary.md`.

---

## 3. Results & Figures (`results/`)

### Publication Figures (`results/figures/`)
Contains the high-resolution vector (`.pdf`) and raster (`.png`) diagrams generated in the project's **Turquoise Color Theme** with **95% Confidence Interval error bars**:
- `tct_plot.png` / `tct_plot.pdf`: Task Completion Time across experimental conditions.
- `robustness_plot.png` / `robustness_plot.pdf`: Clarification loops and internal system intent confidence.
- `nasatlx_plot.pdf`: NASA-TLX workload subscales across conditions.
- `sus_plot.pdf`: System Usability Scale total scores.

### Statistical Summaries (`results/statistics/`)
- `statistical_analysis_summary.md`: Complete markdown report listing all descriptive numbers, $\chi^2$ values, $p$-values, Holm-adjusted significance levels, and effect sizes ($r$ and $W$) formatted ready for copy-pasting into LaTeX or sharing with reviewers.
