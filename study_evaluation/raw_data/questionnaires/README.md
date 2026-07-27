# Subjective Questionnaire & Demographic Raw Data

This directory contains the transcribed raw data from the subjective study evaluation questionnaires (NASA-TLX and System Usability Scale - SUS) as well as participant demographics ($N = 23$ total responses recorded in Google Forms).

---

## Files in this Directory

All tables are saved in universally accessible, Git-friendly **CSV format** (UTF-8 encoded), which can be opened directly with Microsoft Excel, Apple Numbers, Google Sheets, Python (`pandas`), or R.

### 1. Master Combined Dataset
- **`master_combined_questionnaires.csv`**
  - Contains the linked dataset merging participant IDs (`P01`–`P23`), demographics, condition testing order, and exact numeric answers for both tested rounds (Round 1: Single Modality and Round 3: Combined Multimodal).
  - This is the primary table recommended for statistical analysis in R, SPSS, or Python.

### 2. Demographic & Screening Data
- **`demographic_data.csv`**
  - Contains timestamps, participant IDs (`P01`–`P23`), assigned test condition order, age, gender, driver's license status, driving frequency, prior experience with voice assistants and gesture controls, and screening for motor impairments.

### 3. Condition-Specific Sub-Tables
- **`round1_single_modalities_nasatlx_sus.csv`**
  - Contains the NASA-TLX (6 items, 1–7 scale) and SUS (10 items, 1–5 scale) ratings for the baseline individual modality tested in Round 1 (**Voice only** or **Gesture only**).
- **`round3_multimodal_nasatlx_sus.csv`**
  - Contains the NASA-TLX and SUS ratings for the final combined interaction modality tested in Round 3 (**Multimodal: Voice + Gesture**).

---

## Questionnaire Item Mapping

### NASA-TLX Items (Scale: 1 = Sehr niedrig / gut, 7 = Sehr hoch / schlecht)
- `TLX_Mental`: Mentale Beanspruchung
- `TLX_Koerperlich`: Körperliche Beanspruchung
- `TLX_Zeitlich`: Zeitliche Beanspruchung
- `TLX_Leistung`: Wie zufrieden sind Sie mit Ihrer Leistung? *(Achtung: Hier bedeutet 7 = sehr zufrieden)*
- `TLX_Anstrengung`: Wie viel Anstrengung mussten Sie aufbringen?
- `TLX_Frustration`: Wie unsicher, entmutigt, irritiert oder gestresst fühlten Sie sich?

### System Usability Scale (SUS) Items (Scale: 1 = Stimme überhaupt nicht zu, 5 = Stimme voll und ganz zu)
- `SUS_01_haeufig_nutzen`: Ich denke, dass ich dieses System häufig nutzen würde.
- `SUS_02_komplex`: Ich fand das System unnötig komplex.
- `SUS_03_einfach`: Ich fand das System einfach zu bedienen.
- `SUS_04_support`: Ich denke, dass ich technische Unterstützung brauchen würde, um dieses System zu nutzen.
- `SUS_05_integriert`: Ich fand, dass die verschiedenen Funktionen in diesem System gut integriert waren.
- `SUS_06_inkonsistent`: Ich fand, dass das System zu viele Inkonsistenzen aufweist.
- `SUS_07_schnell_lernen`: Ich kann mir vorstellen, dass die meisten Menschen lernen würden, mit diesem System sehr schnell umzugehen.
- `SUS_08_umstaendlich`: Ich fand das System sehr umständlich zu bedienen.
- `SUS_09_sicher`: Ich fühlte mich bei der Benutzung des Systems sicher.
- `SUS_10_viele_dinge`: Ich musste viele Dinge lernen, bevor ich das System erfolgreich nutzen konnte.
