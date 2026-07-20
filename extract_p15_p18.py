import os
import json

base_dir = r"D:\NUIEMG\F_LibEMG-Gesture-Classification\testingdaten\Testing"
participants = ["P15", "P16", "P17", "P18"]

for p in participants:
    p_dir = os.path.join(base_dir, p)
    if not os.path.exists(p_dir):
        continue
    print(f"--- {p} ---")
    for f in os.listdir(p_dir):
        if f.endswith(".jsonl"):
            with open(os.path.join(p_dir, f), "r", encoding="utf-8") as file:
                for line in file:
                    try:
                        data = json.loads(line)
                        if "task_completion_time_ms" in data:
                            cond = data.get("condition")
                            t = data["task_completion_time_ms"] / 1000
                            loops = data.get("clarification_cycles", 0)
                            study_ref = data.get("study_ref", "") # e.g. "1.1"
                            success = data.get("success", False)
                            mod = data.get("used_modalities", "")
                            
                            print(f"Task {study_ref} ({cond}): Time={t:.1f}s, Loops={loops}, Success={success}, Mod={mod}")
                    except:
                        pass
