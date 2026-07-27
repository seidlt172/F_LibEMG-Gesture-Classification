# Quantitative Study Results and Statistical Analysis

## 1. Task Completion Time (TCT - H1)

- **Voice**: M = 32.77s, SD = 5.99, 95% CI = +/-2.98s
- **Gesture**: M = 19.86s, SD = 7.50, 95% CI = +/-3.73s
- **Multimodal**: M = 26.55s, SD = 7.99, 95% CI = +/-3.97s

**Friedman Test**: chi2(2) = 22.11, p = 0.0000, Kendall's W = 0.61 (Statistically Significant)

### Post-hoc Wilcoxon Signed-Rank Tests (Holm-corrected):
- **Gesture vs Voice**: p = 0.0003, Cohen's r = 0.86
- **Gesture vs Multimodal**: p = 0.0018, Cohen's r = 0.73
- **Multimodal vs Voice**: p = 0.0043, Cohen's r = 0.67

## 2. Interaction Robustness - Clarification Loops (H2)

- **Voice**: M = 0.99, SD = 0.38, 95% CI = +/-0.19
- **Gesture**: M = 0.14, SD = 0.18, 95% CI = +/-0.09
- **Multimodal**: M = 0.38, SD = 0.33, 95% CI = +/-0.16

**Friedman Test**: chi2(2) = 24.87, p = 0.0000, Kendall's W = 0.69 (Statistically Significant)

### Post-hoc Wilcoxon Signed-Rank Tests (Holm-corrected):
- **Gesture vs Voice**: p = 0.0002, Cohen's r = 0.88
- **Gesture vs Multimodal**: p = 0.0124, Cohen's r = 0.59
- **Multimodal vs Voice**: p = 0.0006, Cohen's r = 0.81

## 3. Interaction Robustness - Internal System Score (LLM Confidence - H2)

- **Voice**: M = 71.87%, SD = 6.62%, 95% CI = +/-3.29%
- **Gesture**: M = 93.70%, SD = 2.81%, 95% CI = +/-1.40%
- **Multimodal**: M = 84.99%, SD = 8.47%, 95% CI = +/-4.21%

**Friedman Test**: chi2(2) = 25.00, p = 0.0000, Kendall's W = 0.69 (Statistically Significant)

### Post-hoc Wilcoxon Signed-Rank Tests (Holm-corrected):
- **Gesture vs Voice**: p = 0.0002, Cohen's r = 0.88
- **Gesture vs Multimodal**: p = 0.0014, Cohen's r = 0.75
- **Multimodal vs Voice**: p = 0.0009, Cohen's r = 0.79

## 4. Task Success Rate

- **Voice**: 93.1%
- **Multimodal**: 89.9%
- **Gesture**: 88.9%

**Chi-Square Test of Independence**: chi2(2) = 1.67, p = 0.4337 (Not Significant)
