"""Konfiguration der Wissensdatenbank-Übernahme.

Quelle ist die LeadConnector-Hilfe. Die Artikel werden ins Deutsche übersetzt
und dabei auf UmsatzAgent umgeschrieben. Wer die Übersetzung korrigieren will,
ändert GLOSSAR und KATEGORIEN — nicht die erzeugten .mdx-Dateien, die werden
beim nächsten Lauf überschrieben.
"""

QUELLE = "https://help.leadconnectorhq.com"
SITEMAP = f"{QUELLE}/support/sitemap.xml"

# Zielverzeichnis der erzeugten Artikel, relativ zum Repo-Root.
ZIEL = "wissen"
BILDER = "images/wissen"

# Bilder herunterladen und selbst ausliefern? Standardmäßig nein: die Auswahl
# umfasst rund 350 Artikel mit zusammen etwa 300 MB Screenshots, das gehört
# nicht ins Git-Repo. Die Quelle ist Greylabel, ihre Bilder dürfen sichtbar
# bleiben, also wird direkt auf ihr CDN verlinkt. Wer die Bilder doch selbst
# halten will, setzt das hier auf True — dann braucht es einen Objektspeicher.
BILDER_LOKAL = False

# Welche Relevanzklassen aus auswahl.py gebaut werden.
#   kern = Onboarding, Einrichtung, tägliche Arbeit, typische Probleme
#   rand = Spezialfälle, später
#   raus = Agentur, Reseller, US-Themen, reine Fehlercode-Listen
AUSWAHL_KLASSEN = {"kern"}

MODELL = "gemini-3.7-flash"

# --- White-Label -----------------------------------------------------------
# Fremdmarken, die in keinem ausgelieferten Text stehen dürfen. Reihenfolge
# zählt: längere Begriffe zuerst, sonst zerlegt eine kürzere Regel sie.
MARKEN = [
    # Domains zuerst. Stünde "LeadConnector" davor, zerlegte es
    # "help.leadconnectorhq.com" zu "help.UmsatzAgenthq.com".
    ("help.leadconnectorhq.com", "support.umsatzagent.com"),
    ("app.gohighlevel.com", "app.umsatzagent.com"),
    ("leadconnectorhq.com", "umsatzagent.com"),
    ("gohighlevel.com", "umsatzagent.com"),

    ("GoHighLevel", "UmsatzAgent"),
    ("Go High Level", "UmsatzAgent"),
    ("HighLevel", "UmsatzAgent"),
    ("High Level", "UmsatzAgent"),
    ("LeadConnector", "UmsatzAgent"),
    ("Lead Connector", "UmsatzAgent"),
    ("LC Phone", "UmsatzAgent Telefon"),
    ("LC Email", "UmsatzAgent E-Mail"),
    ("LC-Phone", "UmsatzAgent Telefon"),
    # Agentur-Sprache mechanisch geradeziehen. Das Modell hält sich nicht
    # zuverlässig daran, die Begriffe sind aber eindeutig ersetzbar: Der
    # Leser hat genau ein Konto.
    ("in deinem Sub-Account", "in deinem Konto"),
    ("in deinem Unterkonto", "in deinem Konto"),
    ("des Sub-Accounts", "des Kontos"),
    ("des Unterkontos", "des Kontos"),
    ("Sub-Account-Einstellungen", "Kontoeinstellungen"),
    ("Unterkonto-Einstellungen", "Kontoeinstellungen"),
    ("Sub-Accounts", "Konten"),
    ("Sub-Account", "Konto"),
    ("Unterkonten", "Konten"),
    ("Unterkonto", "Konto"),
]

# Begriffe, die nach dem Übersetzen NICHT vorkommen dürfen. Findet der Prüfer
# einen davon, gilt der Artikel als nicht auslieferbar.
VERBOTEN = [
    "highlevel", "high level", "gohighlevel", "leadconnector", "lead connector",
    "leadconnectorhq", "freshdesk", "twilio", "mailgun",
    # Agentur-Sprache. Der Leser hat ein Konto, keine Konten-Hierarchie.
    "unterkonto", "sub-account", "subaccount", "agenturkonto",
]

# --- Terminologie ----------------------------------------------------------
# Links der englische Begriff aus der Quelle, rechts die deutsche Entsprechung
# GENAU SO, WIE SIE IN DER APP STEHT. Abgelesen am Hauptmenü von
# app.umsatzagent.com (Screenshot Gerald, 02.09.2026).
#
# Die Oberfläche ist in sich nicht konsequent — sie schreibt "KI fragen" und
# "KI-Studio", aber "AI-Assistenten". Das wird hier nicht geglättet: die Doku
# muss den Knopf so nennen, wie er dasteht, sonst findet ihn niemand.
GLOSSAR = {
    # Hauptmenü, abgelesen
    "Conversations": "Konversationen",
    "Conversation": "Konversation",
    "Calendars": "Kalender",
    "Calendar": "Kalender",
    "Contacts": "Kontakte",
    "Contact": "Kontakt",
    "Opportunities": "Chancen",
    "Opportunity": "Chance",
    "Payments": "Zahlungen",
    "Payment": "Zahlung",
    "AI Agents": "AI-Assistenten",
    "AI Agent": "AI-Assistent",
    "Conversation AI": "AI-Assistent",
    "Marketing": "Marketing",
    "Automation": "Automatisierung",
    "Automations": "Automatisierung",
    "Workflow": "Automatisierung",
    "Workflows": "Automatisierung",
    "Sites": "Seiten",
    "Memberships": "Mitgliedschaften",
    "Membership": "Mitgliedschaft",
    "Media Storage": "Medien-Drive",
    "Reputation": "Ruf",
    "Reputation Management": "Ruf",
    "Reporting": "Berichterstattung",
    "App Marketplace": "App-Marktplatz",
    "Marketplace": "App-Marktplatz",
    "Settings": "Einstellungen",
    "Dashboard": "Dashboard",
    "Launchpad": "Launchpad",

    # Begriffe innerhalb der Bereiche
    "Pipeline": "Pipeline",
    "Trigger": "Trigger",
    "Action": "Aktion",
    "Campaign": "Kampagne",
    "Appointment": "Termin",
    "Funnel": "Funnel",
    "Website": "Website",
    "Form": "Formular",
    "Survey": "Umfrage",
    "Quiz": "Quiz",
    "Tag": "Tag",
    "Custom Field": "Benutzerdefiniertes Feld",
    "Custom Value": "Benutzerdefinierter Wert",
    "Merge Field": "Platzhalter",
    "Smart List": "Smart List",
    "Review": "Bewertung",
    "Community": "Community",
    "Social Planner": "Social Planner",
    "Email Builder": "E-Mail-Builder",
    "Invoice": "Rechnung",
    "Estimate": "Angebot",
    "Subscription": "Abo",
    "Coupon": "Gutschein",
    "Gift Card": "Gutscheinkarte",
    "Phone Number": "Telefonnummer",
    "Voicemail": "Mailbox",
    "Missed Call Text Back": "Rückruf-SMS bei verpasstem Anruf",
    "Bot": "Assistent",
    "Prompt": "Prompt",
}

# Fälle, in denen eine feste Ersetzung nicht reicht, weil derselbe englische
# Begriff je nach Zusammenhang anders heißt. Wird der Übersetzung wörtlich
# mitgegeben.
HINWEISE = [
    'Was die Quelle "Opportunities" nennt, heißt in der App durchgängig '
    '"Chancen" — der Menüpunkt ebenso wie der einzelne Datensatz ("Chance"). '
    'Schreibe niemals "Opportunity" oder "Lead" dafür.',
    'Der Menüpunkt für Automationen heißt "Automatisierung". Ein einzelner '
    'Ablauf darin heißt weiterhin "Workflow".',
    'Die Oberfläche schreibt "KI fragen" und "KI-Studio", aber "AI-Assistenten". '
    'Übernimm diese Schreibweisen genau so, auch wenn sie uneinheitlich wirken.',
    'Der Bereich für Websites, Funnels, Formulare und Umfragen heißt im Menü '
    '"Seiten".',
    '"Reputation" heißt nur dann "Ruf", wenn der Menüpunkt für Bewertungen '
    'gemeint ist. Geht es um E-Mail-Zustellbarkeit, ist die Absender-Reputation '
    'gemeint — dann schreibe "Absender-Reputation", niemals "Ruf".',
    'Der Leser hat genau ein Konto. Schreibe nie "Unterkonto", "Sub-Account", '
    '"Agentur" oder "Hauptkonto" — die Quelle sieht eine Agentur mit vielen '
    'Konten, unser Leser nicht. Aus "in your sub-account settings" wird '
    'schlicht "in den Einstellungen".',
]

# --- Navigation ------------------------------------------------------------
# Deutsche Namen der LeadConnector-Kategorien. Kategorien ohne Eintrag werden
# von der Übersetzung benannt; wer sie festzurren will, trägt sie hier ein.
KATEGORIEN = {
    "Getting Started Category": "Erste Schritte",
    "Conversations Tab": "Posteingang",
    "Contacts / SmartLists": "Kontakte & Listen",
    "Pipelines & Opportunities": "Pipelines & Opportunities",
    "Scheduling & Calendars (Bookings)": "Kalender & Termine",
    "Marketing Category": "Marketing",
    "Workflow": "Workflows",
    "Funnels & Websites Category": "Funnels & Websites",
    "Surveys, Forms, QR Codes and Quizzes": "Formulare, Umfragen & Quizze",
    "Phone Category": "Telefonie",
    "Phone/ SMS Category": "Telefonie & SMS",
    "LeadConnector Email": "E-Mail",
    "WhatsApp Integration": "WhatsApp",
    "Conversation AI Bot": "KI-Assistent",
    "AI Agents": "KI-Agenten",
    "Payments, Invoices & Estimates": "Zahlungen & Rechnungen",
    "Subscription Products": "Abo-Produkte",
    "E-Commerce": "Online-Shop",
    "Reputation & Review Management": "Bewertungen",
    "Membership and Communities": "Mitgliederbereiche & Community",
    "LeadConnector Integrations": "Integrationen",
    "Marketplace Apps": "Marketplace-Apps",
    "WordPress Integration": "WordPress",
    "Lead Connector Mobile & Desktop App": "Mobile & Desktop App",
    "Client Portal Web and Mobile APP": "Kundenportal",
    "Reporting & Attribution": "Reporting & Attribution",
    "Prospecting Tool": "Prospecting",
    "Location Settings": "Unterkonto-Einstellungen",
    "User Settings": "Benutzereinstellungen",
    "Custom Objects": "Benutzerdefinierte Objekte",
    "Merge Fields & Custom Variables": "Platzhalter & Variablen",
    "External Tracking": "Externes Tracking",
    "Domains": "Domains",
    "SMTP": "SMTP",
    "SEO": "SEO",
    "Blogs": "Blog",
    "GMB": "Google Unternehmensprofil",
    "Events": "Events",
    "Company": "Unternehmen",
    "Billing": "Abrechnung",
    "The Affiliate Manager": "Affiliate-Manager",
}

# Kategorien, die nicht übernommen werden: Funktionen, die UmsatzAgent nicht
# verkauft, oder Inhalte, die den White-Label-Eindruck zerstören.
AUSGESCHLOSSEN = {
    "The Affiliate Manager",
    "Prospecting Tool",
}

# Die Seitenleiste spiegelt das Hauptmenü der App, in dessen Reihenfolge. Wer
# in der App auf "Support" klickt, findet die Doku so sortiert vor wie das
# Menü, aus dem er gerade kommt. Links der Name aus der App, rechts die
# Quell-Kategorien, die dort hineingehören.
# Was hier nicht auftaucht, landet unter "Weitere Themen".
THEMEN = [
    ("Erste Schritte", ["Getting Started Category"]),
    ("Konversationen", ["Conversations Tab", "WhatsApp Integration",
                        "Phone Category", "Phone/ SMS Category", "LeadConnector Email",
                        "SMTP"]),
    ("Kalender", ["Scheduling & Calendars (Bookings)", "Events"]),
    ("Kontakte", ["Contacts / SmartLists", "Custom Objects"]),
    ("Chancen", ["Pipelines & Opportunities"]),
    ("Zahlungen", ["Payments, Invoices & Estimates", "E-Commerce", "Subscription Products"]),
    ("AI-Assistenten", ["Conversation AI Bot", "AI Agents"]),
    ("Marketing", ["Marketing Category"]),
    ("Automatisierung", ["Workflow", "Merge Fields & Custom Variables"]),
    ("Seiten", ["Funnels & Websites Category", "Surveys, Forms, QR Codes and Quizzes",
                "Blogs", "SEO", "External Tracking"]),
    ("Mitgliedschaften", ["Membership and Communities", "Client Portal Web and Mobile APP"]),
    ("Ruf", ["Reputation & Review Management", "GMB"]),
    ("Berichterstattung", ["Reporting & Attribution"]),
    ("App-Marktplatz", ["LeadConnector Integrations", "Marketplace Apps"]),
    ("Mobile App", ["Lead Connector Mobile & Desktop App"]),
    ("Einstellungen", ["Location Settings", "User Settings", "Company", "Billing", "Domains"]),
]
