"""Central study-flow and widget-task catalog for the pilot prototype."""

from __future__ import annotations

from dataclasses import dataclass


CONDITIONS = ("Voice only", "Gesture only", "CAN use both")

CATEGORY_NAMES = {
    1: "Accept/Reject",
    2: "Select+Adjust",
    3: "Browse+Select",
    4: "Confirm+Modify",
}

DOMAINS = (
    "calls",
    "audio",
    "messages",
    "navigation",
    "ambient_light",
    "climate",
)


@dataclass(frozen=True)
class WidgetTask:
    task_id: str
    domain: str
    title: str
    study_refs: tuple[str, ...]


@dataclass(frozen=True)
class FlowStep:
    task_id: str
    domain: str
    prompt: str
    overlay_title: str
    overlay_body: str
    modality: str
    expected_status: str
    voice_input: str = ""
    gesture_label: str = ""
    gesture_ref: str = ""
    accepted_text: str = ""
    rejected_text: str = ""
    unclear_text: str = ""


@dataclass(frozen=True)
class StudyScenario:
    scenario_id: str
    study_ref: str
    condition: str
    category_index: int
    category_name: str
    title: str
    flow_steps: tuple[FlowStep, ...]
    fallback_9: bool

    @property
    def domain(self) -> str:
        return self.flow_steps[0].domain

    @property
    def prompt(self) -> str:
        return self.flow_steps[0].prompt

    @property
    def expected_actions(self) -> tuple[str, ...]:
        return tuple(step.expected_status for step in self.flow_steps)


TASK_CATALOG = {
    "CALL-INCOMING": WidgetTask("CALL-INCOMING", "calls", "Eingehenden Anruf annehmen", ("1.1", "4.3")),
    "CALL-ACTIVE": WidgetTask("CALL-ACTIVE", "calls", "Laufenden Anruf beenden", ("1.1",)),
    "CALL-ENDED": WidgetTask("CALL-ENDED", "calls", "Anruf beendet", ("1.1",)),
    "CALL-VOLUME": WidgetTask("CALL-VOLUME", "calls", "Lautstärke regeln", ("4.3",)),
    "AUDIO-SUGGESTION": WidgetTask("AUDIO-SUGGESTION", "audio", "Musikvorschlag annehmen", ("1.2",)),
    "AUDIO-NEXT": WidgetTask("AUDIO-NEXT", "audio", "Nächsten Song abspielen", ("1.2", "2.1", "3.3")),
    "AUDIO-VOLUME-UP": WidgetTask("AUDIO-VOLUME-UP", "audio", "Lautstärke erhöhen", ("2.1",)),
    "AUDIO-RESUME": WidgetTask("AUDIO-RESUME", "audio", "Song pausiert -> Song abspielen", ("3.3",)),
    "MESSAGE-OPEN": WidgetTask("MESSAGE-OPEN", "messages", "Eingehende Nachricht öffnen", ("3.1",)),
    "MESSAGE-OPENED": WidgetTask("MESSAGE-OPENED", "messages", "Nachricht geöffnet und antwort erhalten", ("3.1",)),
    "MESSAGE-CLOSE": WidgetTask("MESSAGE-CLOSE", "messages", "Eingehende Nachricht schließen", ("3.1",)),
    "MESSAGE-CLOSED": WidgetTask("MESSAGE-CLOSED", "messages", "Nachricht ist geschlossen", ("3.1",)),
    "NAV-ACCEPT-ROUTE": WidgetTask("NAV-ACCEPT-ROUTE", "navigation", "Route annehmen", ("1.3", "4.1")),
    "NAV-ACTIVE": WidgetTask("NAV-ACTIVE", "navigation", "Navigation läuft", ("4.1",)),
    "NAV-REJECT-ROUTE": WidgetTask("NAV-REJECT-ROUTE", "navigation", "Route ablehnen", ("1.3",)),
    "NAV-NEXT-ROUTE": WidgetTask("NAV-NEXT-ROUTE", "navigation", "2 Routenvorschläge - nächster Vorschlag", ("3.2",)),
    "NAV-SELECT-SECOND": WidgetTask("NAV-SELECT-SECOND", "navigation", "2. Vorschlag auswählen", ("3.2",)),
    "NAV-VOLUME-UP": WidgetTask("NAV-VOLUME-UP", "navigation", "Navigationslautstärke erhöhen", ("4.1",)),
    "AMBIENT-COLOR": WidgetTask("AMBIENT-COLOR", "ambient_light", "Farbe wechseln", ("2.3",)),
    "AMBIENT-BRIGHTER": WidgetTask("AMBIENT-BRIGHTER", "ambient_light", "Farbe heller machen", ("2.3", "4.2")),
    "AMBIENT-NIGHTMODE": WidgetTask("AMBIENT-NIGHTMODE", "ambient_light", "Popup: zu Nachtmodus wechseln", ("4.2",)),
    "CLIMATE-SEAT-HEAT": WidgetTask("CLIMATE-SEAT-HEAT", "climate", "Sitzheizung auswählen", ("2.2",)),
    "CLIMATE-SEAT-WARMER": WidgetTask("CLIMATE-SEAT-WARMER", "climate", "Temperatur Sitzheizung erhöhen", ("2.2",)),
}


def step(
    task_id: str,
    *,
    prompt: str,
    overlay_title: str,
    overlay_body: str,
    modality: str,
    expected_status: str = "execute",
    voice_input: str = "",
    gesture_label: str = "",
    gesture_ref: str = "",
    accepted_text: str = "",
    rejected_text: str = "",
    unclear_text: str = "",
) -> FlowStep:
    task = TASK_CATALOG[task_id]
    return FlowStep(
        task_id=task_id,
        domain=task.domain,
        prompt=prompt,
        overlay_title=overlay_title,
        overlay_body=overlay_body,
        modality=modality,
        expected_status=expected_status,
        voice_input=voice_input,
        gesture_label=gesture_label,
        gesture_ref=gesture_ref,
        accepted_text=accepted_text or f"{task.title} bestätigt.",
        rejected_text=rejected_text or f"{task.title} nicht akzeptiert.",
        unclear_text=unclear_text or f"Bitte wiederhole die Eingabe für: {task.title}.",
    )


def scenario(
    study_ref: str,
    condition: str,
    category_index: int,
    title: str,
    flow_steps: tuple[FlowStep, ...],
) -> StudyScenario:
    return StudyScenario(
        scenario_id=f"STUDY-{study_ref}",
        study_ref=study_ref,
        condition=condition,
        category_index=category_index,
        category_name=CATEGORY_NAMES[category_index],
        title=title,
        flow_steps=flow_steps,
        fallback_9=category_index <= 3,
    )


SCENARIOS: tuple[StudyScenario, ...] = (
    scenario(
        "1.1",
        "Voice only",
        1,
        "Anruf annehmen und beenden",
        (
            step(
                "CALL-INCOMING",
                prompt="Anruf kommt rein.",
                overlay_title="Eingehender Anruf",
                overlay_body="Alex ruft an.",
                modality="voice",
                voice_input="Annehmen",
                accepted_text="Anruf angenommen.",
                unclear_text="Möchtest du den Anruf annehmen?",
            ),
            step(
                "CALL-ACTIVE",
                prompt="Call läuft.",
                overlay_title="Aktiver Anruf",
                overlay_body="Anruf mit Alex läuft.",
                modality="voice",
                voice_input="Beenden",
                accepted_text="Anruf wird beendet.",
                unclear_text="Soll der Anruf beendet werden?",
            ),
            step(
                "CALL-ENDED",
                prompt="Anruf beendet.",
                overlay_title="Anruf beendet",
                overlay_body="Gespräch beendet.",
                modality="voice",
                accepted_text="Anruf beendet.",
                unclear_text="",
            ),
        ),
    ),
    scenario(
        "1.2",
        "Gesture only",
        1,
        "Musikvorschlag annehmen und nächster Titel",
        (
            step(
                "AUDIO-SUGGESTION",
                prompt="Songvorschlag wird angezeigt.",
                overlay_title="Musikvorschlag",
                overlay_body="Vorgeschlagen: Night Drive.",
                modality="gesture",
                gesture_label="Daumen hoch",
                gesture_ref="1",
                accepted_text="Musikvorschlag angenommen.",
                unclear_text="Soll der Musikvorschlag angenommen werden?",
            ),
            step(
                "AUDIO-NEXT",
                prompt="Wiedergabe läuft.",
                overlay_title="Audio",
                overlay_body="Night Drive wird abgespielt.",
                modality="gesture",
                gesture_label="Swipe",
                gesture_ref="3",
                accepted_text="Nächster Titel wird abgespielt.",
                unclear_text="Soll der nächste Titel abgespielt werden?",
            ),
        ),
    ),
    scenario(
        "1.3",
        "CAN use both",
        1,
        "Route annehmen und Routenänderung ablehnen",
        (
            step(
                "NAV-ACCEPT-ROUTE",
                prompt="Route wird vorgeschlagen.",
                overlay_title="Routenvorschlag",
                overlay_body="Schnellste Route: 18 Minuten.",
                modality="voice+gesture",
                voice_input="Annehmen",
                gesture_label="Daumen hoch",
                gesture_ref="1",
                accepted_text="Route übernommen.",
                unclear_text="Soll diese Route übernommen werden?",
            ),
            step(
                "NAV-REJECT-ROUTE",
                prompt="Routenänderung wird vorgeschlagen.",
                overlay_title="Routenänderung",
                overlay_body="Alternative Route spart 2 Minuten.",
                modality="voice+gesture",
                expected_status="cancel",
                voice_input="Ablehnen",
                gesture_label="Swipe",
                gesture_ref="2",
                accepted_text="Routenänderung übernommen.",
                rejected_text="Routenänderung abgelehnt.",
                unclear_text="Soll die Routenänderung abgelehnt werden?",
            ),
        ),
    ),
    scenario(
        "2.1",
        "Voice only",
        2,
        "Nächster Song und lauter",
        (
            step(
                "AUDIO-NEXT",
                prompt="Song läuft.",
                overlay_title="Audio",
                overlay_body="Low Beam wird abgespielt.",
                modality="voice",
                voice_input="Nächstes Lied",
                accepted_text="Nächstes Lied spielt.",
                unclear_text="Soll das nächste Lied abgespielt werden?",
            ),
            step(
                "AUDIO-VOLUME-UP",
                prompt="Nächstes Lied spielt.",
                overlay_title="Audio",
                overlay_body="City Lights wird abgespielt.",
                modality="voice",
                voice_input="Lauter",
                accepted_text="Lautstärke erhöht.",
                unclear_text="Soll die Musik lauter werden?",
            ),
        ),
    ),
    scenario(
        "2.2",
        "Gesture only",
        2,
        "Sitzheizung auswählen und erhöhen",
        (
            step(
                "CLIMATE-SEAT-HEAT",
                prompt="Klimamenü ist geöffnet.",
                overlay_title="Klimabedienung",
                overlay_body="Klima ist ausgewählt.",
                modality="gesture",
                gesture_label="Swipe",
                gesture_ref="3",
                accepted_text="Sitzheizung ausgewählt.",
                unclear_text="Soll die Sitzheizung ausgewählt werden?",
            ),
            step(
                "CLIMATE-SEAT-WARMER",
                prompt="Sitzheizung ist ausgewählt.",
                overlay_title="Sitzheizung",
                overlay_body="Aktuelle Stufe: 1.",
                modality="gesture",
                gesture_label="Handgelenk drehen",
                gesture_ref="4",
                accepted_text="Sitzheizung erhöht.",
                unclear_text="Soll die Sitzheizung erhöht werden?",
            ),
        ),
    ),
    scenario(
        "2.3",
        "CAN use both",
        2,
        "Ambientefarbe wechseln und heller machen",
        (
            step(
                "AMBIENT-COLOR",
                prompt="Ambientebeleuchtung ist aktiv.",
                overlay_title="Ambientebeleuchtung",
                overlay_body="Aktuelle Farbe: Blau.",
                modality="voice+gesture",
                voice_input="Farbe wechseln",
                gesture_label="Swipe",
                gesture_ref="3",
                accepted_text="Farbe gewechselt.",
                unclear_text="Soll die Lichtfarbe gewechselt werden?",
            ),
            step(
                "AMBIENT-BRIGHTER",
                prompt="Neue Farbe ist aktiv.",
                overlay_title="Ambientebeleuchtung",
                overlay_body="Aktuelle Helligkeit: 45 Prozent.",
                modality="voice+gesture",
                voice_input="Farbe heller machen",
                gesture_label="Handgelenk drehen",
                gesture_ref="4",
                accepted_text="Ambientelicht heller gemacht.",
                unclear_text="Soll das Ambientelicht heller werden?",
            ),
        ),
    ),
    scenario(
        "3.1",
        "Voice only",
        3,
        "Nachricht öffnen und schließen",
        (
            step(
                "MESSAGE-OPEN",
                prompt="Nachricht kommt rein.",
                overlay_title="Neue Nachricht",
                overlay_body="Bin in 5 Minuten da.",
                modality="voice",
                voice_input="Nachricht öffnen",
                accepted_text="Nachricht geöffnet.",
                unclear_text="Soll die Nachricht geöffnet werden?",
            ),
            step(
                "MESSAGE-CLOSE",
                prompt="Nachricht ist geöffnet.",
                overlay_title="Nachricht",
                overlay_body="Hey, wie lange brauchst du noch?",
                modality="voice",
                voice_input="Schließen",
                accepted_text="Nachricht geschlossen.",
                unclear_text="Soll die Nachricht geschlossen werden?",
            ),
        ),
    ),
    scenario(
        "3.2",
        "Gesture only",
        3,
        "Routenvorschlag wechseln und auswählen",
        (
            step(
                "NAV-NEXT-ROUTE",
                prompt="2 Routenvorschläge werden angezeigt.",
                overlay_title="Routenoptionen",
                overlay_body="Route 1 ist schneller. Route 2 ist ruhiger.",
                modality="gesture",
                gesture_label="Swipe",
                gesture_ref="3",
                accepted_text="Nächster Vorschlag angezeigt.",
                unclear_text="Soll der nächste Routenvorschlag angezeigt werden?",
            ),
            step(
                "NAV-SELECT-SECOND",
                prompt="2. Vorschlag wird angezeigt.",
                overlay_title="Routenoptionen",
                overlay_body="Route 2 ist ausgewählt.",
                modality="gesture",
                gesture_label="Zeigen / Tippen",
                gesture_ref="5",
                accepted_text="2. Vorschlag ausgewählt.",
                unclear_text="Soll der 2. Vorschlag ausgewählt werden?",
            ),
        ),
    ),
    scenario(
        "3.3",
        "CAN use both",
        3,
        "Wiedergabe fortsetzen und nächster Song",
        (
            step(
                "AUDIO-RESUME",
                prompt="Song ist pausiert.",
                overlay_title="Audio pausiert",
                overlay_body="Low Beam ist pausiert.",
                modality="voice+gesture",
                voice_input="Wiedergabe fortsetzen",
                gesture_label="Zeigen / Tippen",
                gesture_ref="5",
                accepted_text="Song wird abgespielt.",
                unclear_text="Soll die Wiedergabe fortgesetzt werden?",
            ),
            step(
                "AUDIO-NEXT",
                prompt="Song läuft.",
                overlay_title="Audio",
                overlay_body="Low Beam wird abgespielt.",
                modality="voice+gesture",
                voice_input="Spiele den nächsten Song",
                gesture_label="Swipe",
                gesture_ref="3",
                accepted_text="Nächster Song wird abgespielt.",
                unclear_text="Soll der nächste Song abgespielt werden?",
            ),
        ),
    ),
    scenario(
        "4.1",
        "Voice only",
        4,
        "Navigation annehmen und Ansagen lauter",
        (
            step(
                "NAV-ACCEPT-ROUTE",
                prompt="Navigation wird vorgeschlagen.",
                overlay_title="Navigationsvorschlag",
                overlay_body="Zielroute ist verfügbar.",
                modality="voice",
                voice_input="Annehmen",
                accepted_text="Navigation läuft.",
                unclear_text="Soll die Navigation gestartet werden?",
            ),
            step(
                "NAV-ACTIVE",
                prompt="Navigation läuft.",
                overlay_title="Navigation aktiv",
                overlay_body="Route ist aktiv. Ansagelautstärke: normal.",
                modality="voice",
                voice_input="Lauter",
                accepted_text="Navigation läuft.",
                unclear_text="Sollen die Navigationsansagen lauter werden?",
            ),
            step(
                "NAV-VOLUME-UP",
                prompt="Navigation läuft.",
                overlay_title="Navigationsansagen",
                overlay_body="Ansagelautstärke: 40 Prozent.",
                modality="voice",
                voice_input="Lauter",
                accepted_text="Navigationsansagen lauter gemacht.",
                unclear_text="Sollen die Navigationsansagen lauter werden?",
            ),
        ),
    ),
    scenario(
        "4.2",
        "Gesture only",
        4,
        "Nachtmodus annehmen und Ambientelicht heller",
        (
            step(
                "AMBIENT-NIGHTMODE",
                prompt="Popup: zu Nachtmodus wechseln.",
                overlay_title="Nachtmodus",
                overlay_body="Das System schlägt Nachtmodus vor.",
                modality="gesture",
                gesture_label="Daumen hoch",
                gesture_ref="1",
                accepted_text="Nachtmodus angenommen.",
                unclear_text="Soll der Nachtmodus aktiviert werden?",
            ),
            step(
                "AMBIENT-BRIGHTER",
                prompt="Ambientebeleuchtung ist aktiv.",
                overlay_title="Ambientebeleuchtung",
                overlay_body="Nachtmodus ist aktiv.",
                modality="gesture",
                gesture_label="Handgelenk drehen",
                gesture_ref="4",
                accepted_text="Ambientebeleuchtung heller gemacht.",
                unclear_text="Soll die Ambientebeleuchtung heller werden?",
            ),
        ),
    ),
    scenario(
        "4.3",
        "CAN use both",
        4,
        "Anruf annehmen und Lautstärke regeln",
        (
            step(
                "CALL-INCOMING",
                prompt="Anruf kommt rein.",
                overlay_title="Eingehender Anruf",
                overlay_body="Alex ruft an.",
                modality="voice+gesture",
                voice_input="Annehmen",
                gesture_label="Daumen hoch",
                gesture_ref="1",
                accepted_text="Anruf angenommen.",
                unclear_text="Möchtest du den Anruf annehmen?",
            ),
            step(
                "CALL-VOLUME",
                prompt="Call läuft.",
                overlay_title="Aktiver Anruf",
                overlay_body="Anruf mit Alex läuft.",
                modality="voice+gesture",
                voice_input="Mach lauter",
                gesture_label="Handgelenk drehen",
                gesture_ref="4",
                accepted_text="Anruflautstärke geregelt.",
                unclear_text="Soll die Anruflautstärke geregelt werden?",
            ),
        ),
    ),
)

SCENARIO_BY_ID = {scenario.scenario_id: scenario for scenario in SCENARIOS}
SCENARIO_BY_REF = {scenario.study_ref: scenario for scenario in SCENARIOS}


CONDITION_GUIDANCE = {
    "Voice only": {
        "title": "Spracheingabe",
        "description": "Spracheingabe verwenden. Gesten werden in diesem Block nicht gewertet.",
        "voice_examples": ("Anruf annehmen", "Route ablehnen", "Mach lauter"),
        "gestures": (),
    },
    "Gesture only": {
        "title": "EMG-Gesten",
        "description": "EMG-Gesten verwenden. Spracheingabe wird in diesem Block nicht gewertet.",
        "voice_examples": (),
        "gestures": (
            ("Daumen hoch", "akzeptieren / bestätigen"),
            ("Swipe", "ablehnen / weiter / überspringen"),
            ("Handgelenk drehen", "regeln / erhöhen / verringern"),
            ("Zeigen / Tippen", "auswählen"),
        ),
    },
    "CAN use both": {
        "title": "Sprache + EMG",
        "description": "Sprache, Geste oder beides möglich.",
        "voice_examples": ("Anruf annehmen", "Route ablehnen", "Mach lauter"),
        "gestures": (
            ("Daumen hoch", "akzeptieren / bestätigen"),
            ("Swipe", "ablehnen / weiter / überspringen"),
            ("Handgelenk drehen", "regeln / erhöhen / verringern"),
            ("Zeigen / Tippen", "auswählen"),
        ),
    },
}


def get_condition_guidance(condition: str) -> dict[str, object]:
    return CONDITION_GUIDANCE.get(condition, CONDITION_GUIDANCE["Voice only"])


def get_scenario(identifier: str) -> StudyScenario:
    return SCENARIO_BY_ID.get(identifier) or SCENARIO_BY_REF.get(identifier) or SCENARIOS[0]


def scenario_titles() -> tuple[str, ...]:
    return tuple(
        f"{scenario.study_ref} - {scenario.condition} - {scenario.title}"
        for scenario in SCENARIOS
    )


def scenario_labels() -> tuple[str, ...]:
    return tuple(scenario_label(scenario) for scenario in SCENARIOS)


def scenario_label(scenario: StudyScenario) -> str:
    return (
        f"{scenario.study_ref} | {scenario.condition} | "
        f"{scenario.category_name} | {scenario.title}"
    )


def scenario_from_label(label: str) -> StudyScenario:
    study_ref = label.split("|", 1)[0].strip()
    return get_scenario(study_ref)


def scenario_id_from_title(title: str) -> str:
    if "|" in title:
        return title.split("|", 1)[0].strip()
    return title.split(" - ", 1)[0] if " - " in title else title


def scenario_prompt(scenario: StudyScenario) -> str:
    steps = " -> ".join(step.prompt for step in scenario.flow_steps)
    return f"{scenario.title}. Steps: {steps}"


def fallback_scenarios() -> tuple[StudyScenario, ...]:
    return tuple(scenario for scenario in SCENARIOS if scenario.fallback_9)
