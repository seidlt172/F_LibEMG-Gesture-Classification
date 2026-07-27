import csv
import os

out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw_data", "questionnaires", "qualitative_interview_raw_responses.csv")

headers = ["Teilnehmer_ID", "Positiv_Was_war_gut", "Negativ_Was_war_schlecht", "Modalitaet_im_realen_Leben_und_Begruendung"]

rows = [
    [
        "P01",
        "Präferiert letzte Option. -> bietet sehr viele Freiheiten und es minimiert Unsicherheiten, verringert Fehlerquote aus Sicht der Testperson -> fand setup recht realistisch, selber gas geben und lenken, dadurch konnte man sich gut in die situation hineinversetzen",
        "- eingeschränkte (nur voice, nur geste) varianten haben sie gestresst\n- das widget mit wechsel zum nachtmodus war etwas verwirrend, weil beide optionen gleichzeitig angezeigt wurden",
        "- person würde eine kombination aus beiden nutzen\n- wenn es die möglichkeit gibt würde sie es verwenden\n- warum gut: manche aufgaben war mit sprache einfacher, manchmal war eine Geste schneller: Klarheit, Sicherheit gegenüber Schnelligkeit, Einfachheit\n- warum sprache deutlicher: geste hast du nur eine option und wenn es nicht richtig ist ist es nicht richtig, bei sprache hast du mehr optionen; im alltag läuft mehr über Sprache, deswegen würde sie sagen sie würde sich damit besser ausdrücken können\n- warum schlecht: du bist eingeschränkt, man hat keine ausweichmöglichkeit bei fehlern, hat die Person bisschen gestresst"
    ],
    [
        "P02",
        "Gut war die Option, dass man sich bei der letzten bedingung entscheiden kann. Manchmal hat sprache, manchmal geste besser funktioniert.\n- Widgets waren gut, dass angezeigt wurde, was man ungefähr sagen kann, damit es funktioniert.",
        "- reaktionszeit (musste lange geste halten; bei sprache hat es relativ lange gedauert)\n- feedback hat gefehlt, dass der sprachbefehl registriert wird\n- rückfragen bei sprachassisten waren doof, weil er versucht hat das wording wie in dem Popup zu verwenden, hätte erwartet, dass das system damit umgehen kann. Rückfrage war nur ja nein frage, musste aber bestätigen durch ursprungsbefehl wiederholen",
        "- Nutzen: im aktuellen Zustand nein, weil es zu lang gedauert hat, war bisschen anstrengend, musste auf den bilschirm schauen, hat sehr stark abgelenkt\n- Funktionen, wie musik skippen, am lenkrad knopf drücken einfacher als geste und sprache macht mehr sinn -> während telefonie macht spracheingabe für lautstärke kein sinn, weil es für die andere Person besser ist\n- würde wenn dann aber eher noch Sprache nutzen, für komplexere Sachen, oder auch bei mehreren Commands, dann gehts einfach schneller und der Fokus bleibt mehr auf der straße\n- Testsetup ist schwierig, fahren war nicht so leicht und es ist nicht so wie autofahren, spuren bisschen eng und sehr schnell\n- glaubt es gibt sehr wenige Anwendungsfälle, was so simpel ist, dass eine geste besser ist als die bestehenden Funktionen im Auto. Viele Optionen sind bereits im Lenkrad vorhanden, und man hat Feedback durch einen Tastendruck.\n- Bei autonomen fahren, wäre Geste eventuell mehr relevant, dann attraktiver als Touch, weil man sich nicht nach vorne beugen will."
    ],
    [
        "P03",
        "",
        "",
        "- nur Gestensteuerung ist komplexer, da ungewohnt aber eigentlich angenehm , stressig wenn sie nicht gut funktioniert wenn man Hand vom Lenkrad nehmen muss\n- manchmal unklar wie die Geste mit Daumen hoch funktioniert bei Annehmen und Ablehnen was ausgewählt wird\n- am besten wurde die Kombination empfunden"
    ],
    [
        "P04",
        "- die Befehle waren klar",
        "- dieser Zwischenschritt mit doppelt bestätigen\n- Zeigen, da ist die Geste zu ungenau bzw die Abstände zu klein",
        "- kein Fan von Gesten\n- schlechte Erfahrungen , oftmals falsche Ergebnisse\n- Gesten sind sehr ablenkend\n- anstrengend Gesten zu performen, eine Hand weg vom Lenkrad\n- Sprachsteuerung besser, kann sie unabhängig vom Fahren einsetzen\n- beim letzten Durchgang hat er beim Regulieren überlegt ob er doch Geste nehmen sollte, weil er findet dass es da passt (schnell und eindeutig) er hat aber trotzdem nur Sprache verwendet"
    ],
    [
        "P05",
        "",
        "- Verzögerung der Displayänderung nach Sprach oder Gesteneingabe\n- da fehlt einfach etwas Feedback\n- der lila Kreis war verwirrend weil er mit Sprachsteuerung in Verbindung gebracht wird\n- generell schwierig sich auf die Straße zu konzentrieren und zugleich die Aufgaben zu erledigen, das erhöht die mentale Belastung",
        "- Sprachsteuerung besser, da da die Hände am Lenkrad bleiben und man kann sich besser konzentrieren\n- “Hey Carla” ist nervig\n- kein Fan von Geste, wenn dann nur für kurze Sachen wie bestätigen mit Daumen hoch\n- die Gesten muss man halt auch lernen\n- Sprachsteuerung fand sie ganz gut\n- Kombination findet sie unnötig, da man meist eh eine Präferenz hat"
    ],
    [
        "P06",
        "- design war schön\n- man konnte selber entscheiden, ob geste oder voice nutzen",
        "- ziemlich viel Text, bei sprachsteuerung wenn man das lesen musste, hat man einen Unfall gebaut\n- bei gestensteuerung musste man die Hand vom Lenkrad nehmen, fand das nicht so gut, hatte nicht das gefühl, dass man sich dadurch mehr auf s fahren konzentrieren kann\n- Sprachsteuerung fand sie doof, dass man immer davor hey carla sagen muss, war bisschen nervig -> Tribut an Unfall\n- Kein Sound feedback oder visual feedback bei Sprachsteuerung (garnicht oder kein Feedback)\n- Kein fan von Sprach oder Gestensteuerung",
        "- würde es ungern nutzen, vielleicht noch Sprachsteuerung\n- glaubt aber dass man sich daran gewöhnen kann\n- Warum Sprachsteuerung: fühlt sich steuerbarer an, ist direct, bei gesten ist die geste recht unruhig und oft nicht richtig erkannt worden, wenn es lauter ist, wäre vielleicht geste aber doch sinnvoller\n- Im autonomen Kontext zögert lang mit der Antwort: dann ist die Wahl und bei gestensteuerung sieht er das als geringer, würde es aber trotzdem eher nicht nutzen\n- vielleicht wenn man es öfters ausprobiert, kann man sich dran gewöhnen und dann ist es gut?\n- mag das touchsche Feedback am liebsten"
    ],
    [
        "P07",
        "- findet Option für beides sehr gut",
        "- Fahren war sehr gewöhnungsbedürftig",
        "- würde Sprachsteuerung nutzen, benutzt sie auch jetzt schon im Auto\n- weniger interaktion bei Sprachsteuerung, lenkt weniger ab und ist einfacher beim Fahren\n- Bei gesten fehlt das physische feedback, wenn man schon mit den Händen interagiert, man hat zwar visuelles feedback aber das haptische fehlt dann\n- bei autonomen Fahren: wenn er schon seine hand bewegt und etwas physisches macht, dann kann er auch gleich einen knopf nutzen\n- Gesten sind aber theoretisch schneller mal gemacht als Sprache, auch tasten am lenkrad sind einfacher und schneller"
    ],
    [
        "P08",
        "- wechseln der Eingabe\n- Slider regulieren genauer mit Geste, wäre mit Sprache unpräziser\n- während Telefonat auch Geste gut\n- sehr eindeutige intuitive Gesten",
        "- Sprache/Geste wurde ausgewählt weil Unsicherheit\n- Abnehmen war ihr die Geste nicht klar welche sie nehmen hätte sollen, deeshalb hat sie Sprache genommen\n- Sprachassistanz immer wieder nennen müssen",
        "- Mal so mal so\n- Untermenü: Sprachsteuerung\n- wenns was ist was man einfach mit ner Geste machen kann dann Geste\n- wenn Gespräch im Auto würde sie Geste nehmen\n- je nach Situation"
    ],
    [
        "P09",
        "- sehr intuitive Gesten\n- die Kombination aus Sprache & Geste",
        "- das Fahren an sich war sehr ungewohnt\n- die Radfahrer und anderen Autos haben etwas verwirrt",
        "- eine Kombination je nach Situation\n- Gesten oftmals effizienter besonders für kleinere Tasks\n- Sprache war das Problem der Wakeup Call"
    ],
    [
        "P10",
        "",
        "",
        ""
    ],
    [
        "P11",
        "- beides (sprache und geste) am besten\n- man kann sich aussuchen was am besten gefällt oder am einfachsten ist\n- sprachsteuerung sicherer da beide hände am lenkrad\n- gestensteuerung geht schneller, man muss sich nicht wiederholen, schneller",
        "- gesten anspruchsvoller\n- eine hand nicht am lenkrad\n- mehr überlegen welche geste für was\n- swipen = lenkrad im weg\n- nachfragen führen zu zusätzlicher anstrengung da man sie lesen muss",
        "- beide gemischt\n- mehr auswahl und verschiedene möglichkeiten\n- würde sprachsteuerung bevorzugen, aber daumen hoch und lautstärke regeln generell schneller und einfacher\n- [Autonomes Fahren]: Gesten würden dann besser gehen, weil man mehr zeit hat es anzuzeigen; bei sprache nicht so viel unterschied, aber beim lesen würde man sich sicherer fühlen und wäre generell einfacher"
    ],
    [
        "P12",
        "- Gesten wurden gut erkannt\n- Gesten wurden besser als Sprache erkannt\n- Beides leicht verständlich",
        "- musste bei Sprache manche Sachen mehrmals sagen\n- bei Geste einmal den Fall, dass sie nicht wusste wie man ablehnt (Daumen nach unten?, Swipen?)",
        "- Gemischt\n- selbst entscheiden können was je nach Aufgabe und Kontext eingesetzt wird\n- situationsbedingt handeln können\n- manchmal war die Geste und manchmal die Sprache leichter"
    ],
    [
        "P13",
        "- Pure Spracherkennung war das beste\n- Gesture+Voice war gut, vor allem konnte User so auf Voice vertrauen & konnte sich so besser auf das Autofahren fokussieren",
        "- User fand mit der Geste umständlich + parallel mit Auto fahren\n- gestikulieren hat viel mehr gestört als reden",
        "- Voice am ehesten und vielleicht in Kombi mit Gesture\n- Niemals nur Gesture"
    ],
    [
        "P14",
        "- Pure Spracherkennung war das beste\n- UI und feedback loops bei unklarheiten, wurden als gut empfunden",
        "- User fand mit der Geste umständlich + parallel mit Auto fahren\n- gestikulieren hat viel mehr gestört als reden",
        "- Voice und haptische knöpfe"
    ],
    [
        "P15",
        "- Die Kombination nutze ich bereits täglich in meinem bmw\n- UI und feedback loops bei unklarheiten, wurden als gut empfunden",
        "",
        "- Voice, haptische Knöpfe + Gesten. Finde ich gut die Kombination."
    ],
    [
        "P16",
        "- Sprache war sehr einfach für mich",
        "- Gestensteuerung benutze ich nicht so oft, daher war das sehr ungewohnt",
        "- am liebsten Sprache, gesten können vlt einige wenige Befehle praktisch sein"
    ],
    [
        "P17",
        "- Sprache und geste fand ich eigentlich gut zu nutzen",
        "- Ich habe nicht ganz verstanden, wann ich eine Geste wiederholen muss. Vorallem beim Song Vorschlag annehmen, musste ich mehrmals Wiederholen",
        "- Ich kenne das bereits von meinem Auto, da benutze ich Gesten aber selten und am liebsten touch und nur in Situationen wo ich nicht hinschauen kann voice"
    ],
    [
        "P18",
        "- gesten fand ich einfach auszuführen",
        "- Sprachsteuerung ist nicht so cool bei einem telefonat. Ich kann nicht auflegen, ohne das es die andere Person merkt.\n- Das Lenkrad war super leicht und ich hatte schwierigkeiten die Spur zu halten",
        "- Sprache benutz ich oft im Auto für das Navi. Gesten kenn ich so noch garnicht, fand diese nach 4 Aufgaben schon bischen anstrengend, auch wenn sie Intuitiv waren"
    ]
]

with open(out_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"Successfully saved all {len(rows)} participants (P01 to P18) to {out_file}")
