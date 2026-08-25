# umsatzagent-docs — Help Center (Mintlify)

Quelle für **support.umsatzagent.com**, das Help Center für UmsatzAgent-Kunden.
Repo `gerald-eder/umsatzagent-docs` (privat).

## Wie das deployt

`git push` auf `main` → Mintlify baut und publiziert automatisch. Kein eigener
Build-Schritt, keine CI, kein Worker. Tarif **Starter ($0)**, Cloud-gehostet.

DNS: `support.umsatzagent.com` → `cname.mintlify.builders` (Cloudflare, Zone
`umsatzagent.com`, Account Edervest).

Lokal ansehen:

```bash
npm i -g mint
mint dev
```

## Struktur

- Inhalte sind `.mdx` — Markdown plus Mintlify-Komponenten (`<Card>`, `<Steps>`, `<Note>`, `<Warning>`)
- Navigation, Farben, Logo, Footer stehen in `docs.json`
- Inhaltsgruppen: `erste-schritte/`, `anna/`, `plattform/`, `konto/`, dazu `index.mdx`

## Woher die Inhalte kommen — Einbahnstraße

Fachliche Quelle ist die **Company Brain**, nicht dieses Repo:

```
~/Library/CloudStorage/GoogleDrive-info@umsatzagent.com/Geteilte Ablagen/UmsatzAgent/
```

- Gültige Fassung: `ABOUT/anna-knowledgebase-2026-08.md` (Stand 2026-08-12)
- Inhalte fließen **Brain → Repo, nie umgekehrt.** Wird hier eine Aussage
  korrigiert, gehört die Korrektur zuerst in die Knowledgebase
- **Nicht verwenden:** `ABOUT/faq.md` — als überholt markiert (60-Tage-Garantie,
  die es nie gab, alte Preise, umsatzai.com-Links)
- Projektkontext: `PROJECTS/support-hub/`, Entscheidung:
  `INTELLIGENCE/decisions/2026-08-24-support-hub-mintlify.md`

## Schreibregeln

- Deutsch, per **Du**, Umlaute ausschreiben (ä ö ü ß — niemals ae/oe/ue/ss)
- Keine Zahl und keine Zusage, die nicht in der Knowledgebase steht
- Rechtliche Pflichten des Kunden (KI-Kennzeichnung, Aufzeichnung, Werbeanrufe)
  offen benennen, nicht verstecken
- Primärfarbe `#22A2E3` (Electric Blue), passend zur Website

## Issues

Tasks laufen in **Multica**, Workspace UmsatzAgent.com
(`b9d29630-088c-47ec-bf5a-ddc90ff7cebe`), Präfix `UMS-`. Relevant: UMS-184.

## Hostname

**`support.umsatzagent.com`** — Owner-Entscheidung Gerald, 2026-08-25.
`docs.umsatzagent.com` ist verworfen; der Titel von UMS-184 trägt noch den alten
Namen und ist überholt. Nicht eigenmächtig umstellen.
