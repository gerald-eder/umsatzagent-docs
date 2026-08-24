# UmsatzAgent Support

Quelle für **support.umsatzagent.com** — das Help Center für UmsatzAgent-Kunden.
Gebaut mit [Mintlify](https://mintlify.com), publiziert aus diesem Repo.

## Wie das funktioniert

Alles hier ist Text. Es gibt keinen Admin-Bereich, in dem Inhalte "irgendwo"
liegen:

- **Inhalte** sind `.mdx`-Dateien — Markdown mit ein paar Komponenten (`<Card>`,
  `<Steps>`, `<Note>`, `<Warning>`).
- **Navigation, Farben, Logo, Footer** stehen in `docs.json`.
- **Publiziert wird per `git push` auf `main`.** Mintlify baut und deployt
  automatisch.

Das heißt: Änderungen laufen wie Code — Branch, Pull Request, Merge. Und ein
Agent kann sie schreiben.

## Lokal ansehen

```bash
npm i -g mint
mint dev
```

## Inhalt pflegen

Fachliche Quelle ist die Company Brain:
`Geteilte Ablagen/UmsatzAgent/ABOUT/anna-knowledgebase-2026-08.md` (Stand
2026-08-12). Das ist die einzige gültige Fassung.

**Nicht verwenden:** `ABOUT/faq.md` — als überholt markiert (enthält eine
60-Tage-Garantie, die es nie gab, alte Preise und umsatzai.com-Links).

## Regeln

- Deutsch, per Du, Umlaute ausschreiben
- Keine Zahl und keine Zusage, die nicht in der Wissensdatenbank steht
- Rechtliche Pflichten des Kunden (KI-Kennzeichnung, Aufzeichnung,
  Werbeanrufe) offen benennen, nicht verstecken
