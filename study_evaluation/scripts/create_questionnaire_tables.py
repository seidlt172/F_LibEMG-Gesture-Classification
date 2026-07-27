import os
import csv

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw_data", "questionnaires")
os.makedirs(out_dir, exist_ok=True)

# 1. Demographic Data & Test Order
demo_headers = [
    "Zeitstempel", "Teilnehmer_ID", "Test_Order", "Alter", "Geschlecht",
    "Fuererschein", "Fahrhaeufigkeit", "Erfahrung_Sprachassistenten",
    "Erfahrung_Gestensteuerung", "Motorische_Einschränkungen"
]

demo_rows = [
    ["6.26.2026 10:36:54", "P01", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "22", "Weiblich", "Ja", "Seltener", "2", "2", "Nein"],
    ["6.26.2026 11:43:28", "P02", "Gestensteuerung (Gesture) -> Sprachsteuerung (Voice) -> Kombinierte Steuerung (Voice + Gesture)", "26", "Männlich", "Ja", "Mehrmals pro Woche", "5", "3", "Nein"],
    ["6.26.2026 13:36:30", "P03", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "27", "Männlich", "Ja", "Täglich", "4", "1", "Nein"],
    ["6.26.2026 14:39:00", "P04", "Gestensteuerung (Gesture) -> Sprachsteuerung (Voice) -> Kombinierte Steuerung (Voice + Gesture)", "29", "Männlich", "Ja", "Seltener", "3", "2", "Nein"],
    ["6.26.2026 15:24:45", "P05", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "29", "Weiblich", "Ja", "Täglich", "3", "2", "Nein"],
    ["6.29.2026 10:46:06", "P06", "Gestensteuerung (Gesture) -> Sprachsteuerung (Voice) -> Kombinierte Steuerung (Voice + Gesture)", "23", "Weiblich", "Ja", "Täglich", "3", "1", "Nein"],
    ["6.29.2026 11:45:23", "P07", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "23", "Männlich", "Ja", "Mehrmals pro Monat", "3", "1", "Nein"],
    ["6.29.2026 12:42:21", "P08", "Gestensteuerung (Gesture) -> Sprachsteuerung (Voice) -> Kombinierte Steuerung (Voice + Gesture)", "24", "Weiblich", "Ja", "Mehrmals pro Woche", "3", "1", "Nein"],
    ["6.29.2026 14:16:28", "P09", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "25", "Weiblich", "Ja", "Mehrmals pro Monat", "3", "2", "Nein"],
    ["6.29.2026 16:15:09", "P11", "Gestensteuerung (Gesture) -> Sprachsteuerung (Voice) -> Kombinierte Steuerung (Voice + Gesture)", "21", "Weiblich", "Ja", "Täglich", "5", "3", "Nein"],
    ["6.30.2026 10:55:41", "P12", "Gestensteuerung (Gesture) -> Sprachsteuerung (Voice) -> Kombinierte Steuerung (Voice + Gesture)", "29", "Weiblich", "Ja", "Täglich", "4", "1", "Nein"],
    ["6.30.2026 10:59:58", "P10", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "27", "Weiblich", "Ja", "Täglich", "3", "2", "Nein"],
    ["7.1.2026 13:36:20", "P14", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "22", "Männlich", "Ja", "Mehrmals pro Woche", "4", "1", "Nein"],
    ["7.1.2026 15:08:52", "P15", "Gestensteuerung (Gesture) -> Sprachsteuerung (Voice) -> Kombinierte Steuerung (Voice + Gesture)", "24", "Männlich", "Ja", "Täglich", "5", "4", "Nein"],
    ["7.1.2026 19:41:03", "P16", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "21", "Weiblich", "Ja", "Mehrmals pro Monat", "4", "1", "Nein"],
    ["7.1.2026 19:51:55", "P17", "Gestensteuerung (Gesture) -> Sprachsteuerung (Voice) -> Kombinierte Steuerung (Voice + Gesture)", "23", "Weiblich", "Ja", "Mehrmals pro Woche", "3", "2", "Nein"],
    ["7.2.2026 14:07:43", "P18", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "22", "Männlich", "Ja", "Mehrmals pro Woche", "4", "1", "Nein"],
    ["7.2.2026 14:55:04", "P19", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "29", "Weiblich", "Ja", "Nie", "4", "3", "Nein"],
    ["7.2.2026 15:23:36", "P20", "Gestensteuerung (Gesture) -> Sprachsteuerung (Voice) -> Kombinierte Steuerung (Voice + Gesture)", "24", "Männlich", "Ja", "Seltener", "1", "1", "Nein"],
    ["7.2.2026 15:51:42", "P21", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "24", "Männlich", "Ja", "Seltener", "2", "1", "Nein"],
    ["7.2.2026 16:25:31", "P22", "Gestensteuerung (Gesture) -> Sprachsteuerung (Voice) -> Kombinierte Steuerung (Voice + Gesture)", "27", "Weiblich", "Ja", "Seltener", "2", "1", "Nein"],
    ["7.2.2026 16:52:31", "P23", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "29", "Männlich", "Ja", "Täglich", "5", "4", "Nein"],
    ["7.2.2026 20:03:39", "P13", "Sprachsteuerung (Voice) -> Gestensteuerung (Gesture) -> Kombinierte Steuerung (Voice + Gesture)", "27", "Männlich", "Ja", "Mehrmals pro Woche", "4", "1", "Nein"]
]

with open(os.path.join(out_dir, "demographic_data.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(demo_headers)
    writer.writerows(demo_rows)
print("Saved demographic_data.csv")

# 2. Round 1 (Single Modality: Voice or Gesture)
r1_headers = [
    "Bedingung", "TLX_Mental", "TLX_Koerperlich", "TLX_Zeitlich", "TLX_Leistung", "TLX_Anstrengung", "TLX_Frustration",
    "SUS_01_haeufig_nutzen", "SUS_02_komplex", "SUS_03_einfach", "SUS_04_support", "SUS_05_integriert",
    "SUS_06_inkonsistent", "SUS_07_schnell_lernen", "SUS_08_umstaendlich", "SUS_09_sicher", "SUS_10_viele_dinge"
]

r1_rows = [
    ["Sprachsteuerung (Voice)", 5, 5, 5, 4, 5, 5, 4, 1, 3, 1, 4, 1, 4, 1, 4, 1],
    ["Gestensteuerung (Gesture)", 5, 3, 5, 6, 5, 5, 2, 4, 3, 1, 3, 4, 3, 3, 2, 1],
    ["Sprachsteuerung (Voice)", 3, 2, 2, 6, 3, 2, 4, 2, 4, 1, 4, 2, 4, 1, 4, 1],
    ["Gestensteuerung (Gesture)", 5, 4, 3, 5, 5, 3, 1, 4, 2, 1, 4, 2, 3, 4, 3, 3],
    ["Sprachsteuerung (Voice)", 4, 2, 3, 4, 4, 3, 4, 2, 5, 1, 4, 1, 4, 2, 3, 2],
    ["Gestensteuerung (Gesture)", 6, 6, 3, 4, 5, 6, 1, 1, 3, 3, 5, 1, 3, 2, 1, 5],
    ["Sprachsteuerung (Voice)", 2, 3, 1, 7, 3, 1, 4, 2, 4, 1, 4, 1, 5, 1, 5, 1],
    ["Gestensteuerung (Gesture)", 6, 5, 3, 6, 5, 5, 2, 3, 3, 1, 4, 3, 4, 2, 3, 3],
    ["Sprachsteuerung (Voice)", 3, 2, 1, 3, 2, 4, 4, 2, 4, 1, 4, 1, 4, 4, 4, 1],
    ["Gestensteuerung (Gesture)", 5, 5, 2, 3, 4, 5, 3, 2, 4, 2, 4, 1, 4, 1, 3, 1],
    ["Gestensteuerung (Gesture)", 5, 1, 6, 6, 2, 3, 3, 1, 4, 1, 4, 2, 3, 2, 5, 2],
    ["Sprachsteuerung (Voice)", 4, 4, 3, 3, 4, 2, 3, 2, 2, 2, 3, 2, 3, 3, 3, 3],
    ["Sprachsteuerung (Voice)", 2, 1, 2, 6, 2, 3, 4, 3, 4, 1, 3, 1, 3, 2, 5, 1],
    ["Gestensteuerung (Gesture)", 4, 5, 3, 4, 3, 1, 6, 2, 5, 1, 5, 2, 3, 1, 4, 1],
    ["Sprachsteuerung (Voice)", 3, 1, 3, 5, 2, 2, 4, 1, 5, 3, 4, 2, 2, 1, 4, 2],
    ["Gestensteuerung (Gesture)", 6, 5, 4, 5, 6, 4, 2, 3, 2, 4, 3, 2, 2, 3, 2, 4],
    ["Sprachsteuerung (Voice)", 3, 1, 3, 5, 2, 3, 5, 1, 4, 1, 4, 2, 4, 1, 5, 2],
    ["Gestensteuerung (Gesture)", 1, 2, 4, 6, 6, 1, 5, 2, 5, 1, 5, 1, 5, 1, 5, 1],
    ["Gestensteuerung (Gesture)", 1, 1, 1, 6, 1, 1, 4, 1, 5, 1, 5, 1, 4, 1, 4, 1],
    ["Sprachsteuerung (Voice)", 2, 1, 2, 5, 2, 3, 2, 1, 4, 1, 4, 2, 5, 2, 2, 1],
    ["Gestensteuerung (Gesture)", 4, 2, 1, 1, 4, 4, 2, 1, 4, 2, 4, 1, 5, 2, 4, 2],
    ["Sprachsteuerung (Voice)", 2, 1, 1, 7, 1, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1],
    ["Sprachsteuerung (Voice)", 2, 2, 2, 6, 3, 3, 3, 1, 4, 1, 4, 1, 3, 2, 4, 1]
]

with open(os.path.join(out_dir, "round1_single_modalities_nasatlx_sus.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(r1_headers)
    writer.writerows(r1_rows)
print("Saved round1_single_modalities_nasatlx_sus.csv")

# 3. Round 3 (Multimodal Condition)
r3_rows = [
    ["Kombinierte Steuerung (Voice + Gesture)", 3, 2, 2, 6, 2, 2, 5, 1, 5, 1, 5, 1, 4, 1, 5, 2],
    ["Kombinierte Steuerung (Voice + Gesture)", 4, 2, 2, 7, 3, 4, 3, 4, 3, 1, 3, 4, 2, 4, 3, 3],
    ["Kombinierte Steuerung (Voice + Gesture)", 2, 2, 2, 7, 2, 1, 5, 1, 4, 2, 4, 1, 3, 2, 5, 2],
    ["Kombinierte Steuerung (Voice + Gesture)", 2, 1, 2, 3, 2, 3, 3, 3, 2, 1, 2, 3, 4, 3, 4, 3],
    ["Kombinierte Steuerung (Voice + Gesture)", 4, 4, 2, 3, 5, 4, 4, 2, 4, 2, 4, 2, 4, 3, 3, 3],
    ["Kombinierte Steuerung (Voice + Gesture)", 7, 5, 7, 5, 5, 6, 3, 2, 4, 2, 5, 3, 4, 2, 1, 3],
    ["Kombinierte Steuerung (Voice + Gesture)", 2, 3, 1, 6, 3, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1],
    ["Kombinierte Steuerung (Voice + Gesture)", 2, 2, 2, 5, 2, 2, 4, 1, 4, 1, 4, 3, 4, 1, 4, 2],
    ["Kombinierte Steuerung (Voice + Gesture)", 2, 1, 2, 5, 2, 3, 5, 1, 4, 1, 4, 3, 4, 2, 4, 1],
    ["Kombinierte Steuerung (Voice + Gesture)", 6, 3, 2, 5, 4, 2, 5, 1, 5, 1, 5, 1, 5, 2, 4, 2],
    ["Kombinierte Steuerung (Voice + Gesture)", 4, 1, 3, 6, 5, 1, 5, 1, 4, 1, 4, 1, 4, 1, 5, 1],
    ["Kombinierte Steuerung (Voice + Gesture)", 1, 1, 2, 6, 1, 1, 5, 2, 5, 3, 5, 1, 5, 2, 5, 1],
    ["Kombinierte Steuerung (Voice + Gesture)", 2, 2, 2, 5, 2, 2, 4, 4, 5, 1, 4, 4, 3, 4, 3, 2],
    ["Kombinierte Steuerung (Voice + Gesture)", 3, 3, 2, 6, 4, 1, 5, 1, 5, 2, 4, 3, 2, 1, 5, 3],
    ["Kombinierte Steuerung (Voice + Gesture)", 3, 2, 2, 5, 3, 2, 4, 2, 4, 3, 4, 2, 3, 3, 4, 3],
    ["Kombinierte Steuerung (Voice + Gesture)", 3, 3, 2, 6, 3, 2, 5, 2, 5, 3, 4, 1, 3, 2, 5, 4],
    ["Kombinierte Steuerung (Voice + Gesture)", 4, 4, 2, 5, 4, 2, 4, 2, 5, 3, 5, 2, 2, 2, 5, 3],
    ["Kombinierte Steuerung (Voice + Gesture)", 2, 3, 3, 7, 3, 2, 5, 1, 5, 1, 5, 1, 5, 3, 5, 1],
    ["Kombinierte Steuerung (Voice + Gesture)", 2, 1, 2, 4, 2, 2, 4, 2, 4, 1, 4, 2, 4, 1, 2, 1],
    ["Kombinierte Steuerung (Voice + Gesture)", 3, 3, 2, 3, 2, 3, 1, 4, 2, 1, 2, 3, 4, 4, 2, 1],
    ["Kombinierte Steuerung (Voice + Gesture)", 2, 1, 1, 4, 2, 2, 4, 1, 5, 1, 5, 1, 5, 1, 5, 2],
    ["Kombinierte Steuerung (Voice + Gesture)", 3, 1, 1, 7, 1, 1, 4, 1, 5, 1, 5, 1, 4, 1, 5, 1],
    ["Kombinierte Steuerung (Voice + Gesture)", 2, 3, 5, 3, 4, 3, 3, 2, 2, 2, 4, 2, 2, 4, 2, 2]
]

with open(os.path.join(out_dir, "round3_multimodal_nasatlx_sus.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(r1_headers)
    writer.writerows(r3_rows)
print("Saved round3_multimodal_nasatlx_sus.csv")

# 4. Master Combined Table (linking ID to answers)
combined_headers = ["Teilnehmer_ID", "Alter", "Geschlecht", "Test_Order"] + r1_headers
combined_rows = []
for i in range(len(demo_rows)):
    pid = demo_rows[i][1]
    age = demo_rows[i][3]
    gender = demo_rows[i][4]
    order = demo_rows[i][2]
    combined_rows.append([pid, age, gender, order] + r1_rows[i])
    combined_rows.append([pid, age, gender, order] + r3_rows[i])

with open(os.path.join(out_dir, "master_combined_questionnaires.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(combined_headers)
    writer.writerows(combined_rows)
print("Saved master_combined_questionnaires.csv")
