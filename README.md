# Fragenbank & Übungs-App zur PMP®-Zertifizierungsprüfung

Übungssystem für den Kurs Version 8 (PMBOK® Guide, 8th Edition · PMP® Examination Content Outline 2026). Enthält die
Single-Choice-Fragen aus der Excel-Datei **und** die neuen interaktiven
Prüfungsformate 2026 in einem gemeinsamen JSON-Format.

## Inhalt

| Datei | Zweck |
|---|---|
| `pmp_question_bank.json` | Alle 246 Fragen (202 Single Choice + 44 interaktiv) |
| `app.py` | Streamlit-App zum Üben aller Fragetypen |
| `requirements.txt` | Abhängigkeiten |

## Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

`app.py` und `pmp_question_bank.json` müssen im selben Verzeichnis liegen.

## Umfang

* **202 Single-Choice-Fragen** – identisch mit der Excel-Datei, inklusive
  Begründung für **jede** Option (`option_rationales`).
* **44 interaktive Fragen** – genau **2 pro Abschnitt** über alle 22 Abschnitte
  der vier Module.

Verteilung der interaktiven Formate:

| Typ | Bedeutung | Anzahl |
|---|---|---|
| `matching` | Paare zuordnen | 9 |
| `drag_drop` | Elemente in Kategorien einsortieren | 8 |
| `ordering` | Reihenfolge herstellen | 7 |
| `multiple_response` | Mehrfachauswahl | 5 |
| `fill_in_blank` | Lückentext mit Auswahl | 4 |
| `graphic_interpretation` | Grafik lesen, Dropdowns befüllen | 4 |
| `hotspot` | Point & Click auf einer Grafik | 4 |
| `case_study` | Szenario mit mehreren Teilfragen | 3 |

## JSON-Schema

Jede Frage ist ein Objekt in `questions`:

```jsonc
{
  "id": "PR-3-I1",              // eindeutig
  "module": "Process",           // Querschnitt | Business Environment | People | Process
  "section": "3 · Schedule",     // entspricht dem Foliensatz-Abschnitt
  "type": "hotspot",
  "prompt": "Fragetext",
  "payload": { /* typabhängig, s. u. */ },
  "answer":  { /* typabhängig */ },
  "rationale": "Erläuterung der Lösung"
}
```

### Payload und Answer je Typ

| Typ | `payload` | `answer` |
|---|---|---|
| `single_choice` | `options:[{id,text}]` | `"b"` |
| `multiple_response` | `options:[{id,text}]`, `select_hint` | `["a","c"]` |
| `matching` | `items:[{id,text}]`, `targets:[{id,text}]` | `{"i1":"t2", ...}` |
| `drag_drop` | `items:[{id,text}]`, `categories:[{id,text}]` | `{"i1":"c2", ...}` |
| `ordering` | `items:[{id,text}]` | `["i2","i1", ...]` (Sollreihenfolge) |
| `fill_in_blank` | `sentence` mit `[[b1]]`, `blanks:[{id,options}]` | `{"b1":"Text"}` |
| `graphic_interpretation` | `svg`, `blanks:[{id,label,options}]` | `{"b1":"Text"}` |
| `hotspot` | `svg`, `regions:[{id,label}]` | `"B"` |
| `case_study` | `scenario`, `subquestions:[{id,type,prompt,options,answer,rationale}]` | `null` (liegt in den Teilfragen) |

Nur `single_choice` besitzt zusätzlich `option_rationales` – ein Objekt mit einer
Begründung je Option.

Grafiken sind als **Inline-SVG** hinterlegt: keine externen Bilddateien nötig,
die JSON-Datei ist vollständig eigenständig.

## Hinweise zur Umsetzung

* **Point & Click / Drag & Drop:** Streamlit hat keine native Maus-Interaktion
  auf Grafiken. Die App zeigt die Grafik mit sichtbar beschrifteten Bereichen
  (A–D) und lässt den Bereich per Auswahl wählen; Drag & Drop ist als Zuordnung
  über Auswahlfelder umgesetzt. Fachlich identisch, technisch einfacher.
  Für echtes Ziehen ließe sich später z. B. `streamlit-sortables` ergänzen –
  das Schema müsste dafür nicht geändert werden.
* **Bewertung:** `grade()` in `app.py` liefert `(korrekt, feedback_zeilen)` und
  deckt alle neun Typen ab. Bei Single Choice wird für jede Option die
  Begründung angezeigt, sonst die Musterzuordnung.
* **Filter:** Modul, Abschnitt, Fragetyp, „nur interaktive Formate", Mischen und
  Fragenanzahl. Damit lässt sich z. B. ein 10-Fragen-Quiz nur zu
  „4 · Cost & Earned Value" ziehen.

## Eigene Fragen ergänzen

Neue Fragen einfach an `questions` anhängen – die App erkennt sie automatisch,
solange `type` einer der neun Typen ist und `payload`/`answer` dem Schema oben
entsprechen. Sinnvoll ist ein Validierungslauf gegen dieselben Regeln, die beim
Erzeugen der Bank verwendet wurden (eindeutige IDs, Antwortwerte müssen in den
Optionen vorkommen, `ordering` muss eine Permutation sein).

## In eine WordPress-Seite (Divi) einbinden

Möglich, aber nur für **öffentlich** deployte Apps: Streamlit Community Cloud
unterstützt das Einbetten öffentlicher Apps per iframe und oEmbed; für private
Apps gibt es ausdrücklich keinen offiziellen Support.

In Divi ein **Code-Modul** einfügen:

```html
<iframe
  src="https://IHRE-APP.streamlit.app/?embed=true&compact=1"
  style="width:100%; height:900px; border:none;"
  loading="lazy"
  title="Übungsfragen">
</iframe>
```

### Kompakt-Modus

`?compact=1` (oder `?embed=true`) schaltet die App einbettungsfreundlich:

* Die Seitenleiste wird ausgeblendet.
* Die Auswahl wandert als aufklappbarer Bereich **„Auswahl"** in den Hauptbereich
  und ist zweispaltig – funktioniert auch auf schmalen Bildschirmen.
* Oberer Rand reduziert, damit die App nicht wie eine Seite in der Seite wirkt.

### Vorgefiltertes Quiz per URL

So lässt sich pro Seite ein passendes Quiz einbetten, ohne dass Teilnehmende
etwas einstellen müssen:

| Parameter | Wirkung | Beispiel |
|---|---|---|
| `module` | Modul(e), kommagetrennt | `module=Process` |
| `section` | Abschnitt(e), kommagetrennt | `section=4 · Cost %26 Earned Value` |
| `type` | Fragetyp(en) | `type=hotspot,matching` |
| `interactive` | nur interaktive Formate | `interactive=1` |
| `n` | Anzahl Fragen (0 = alle) | `n=10` |
| `autostart` | Runde sofort starten | `autostart=1` |

Beispiel – 10 gemischte Fragen zum Process-Modul, sofort startend:

```html
<iframe src="https://IHRE-APP.streamlit.app/?embed=true&compact=1&autostart=1&module=Process&n=10"
        style="width:100%; height:900px; border:none;" loading="lazy"></iframe>
```

Ungültige Werte werden ignoriert und fallen auf „alles" zurück, die App stürzt
also nicht ab. Kaufmännische Und-Zeichen in Abschnittsnamen müssen als `%26`
kodiert werden.

### Weitere Praxishinweise

* **Höhe fest einplanen:** iframes wachsen nicht mit dem Inhalt. 800–1000 px sind
  realistisch; bei Fragen mit Grafik eher mehr.
* **Schlafende Apps:** Community-Cloud-Apps werden nach längerer Inaktivität
  pausiert und zeigen dann zuerst einen Aufweck-Bildschirm.
* Die Alternative ohne iframe ist ein Button, der die App in einem neuen Tab
  öffnet – weniger elegant, dafür ohne Höhen- und Mobilprobleme.

## Namensgebung bei öffentlichem Deployment

PMI untersagt Dritten, seine Marken in **Produktnamen, Domainnamen oder URLs**
aufzunehmen. Eine Adresse wie `pmp-trainer.streamlit.app` wäre daher nicht
zulässig. Zu wählen ist ein neutraler Repo- und App-Name, z. B.
`pm-zertifizierung-uebung` → `pm-zertifizierung-uebung.streamlit.app`.

Die Verwendung der Marke in der **Kursbezeichnung** („Prüfungsvorbereitung
PMP®-Zertifizierung") ist Trainingsanbietern gestattet, sofern der Markenhinweis
erfolgt – dieser steht in der App in der Seitenleiste und in der Fußzeile.

## Rechtlicher Hinweis

PMI, PMP, PMBOK und das PMI-Logo sind eingetragene Marken des Project Management
Institute, Inc. Diese Übungssammlung ist ein eigenständiges Angebot von
Mielke PM Training & Coaching und wird von PMI weder unterstützt noch
geprüft, autorisiert oder zertifiziert. Die Fragen sind eigens für diesen Kurs
formuliert und sind **keine Originalfragen des PMI**, (c)Nicole Schelter.
