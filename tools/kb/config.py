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

MODELL = "gemini-3.7-flash"

# --- White-Label -----------------------------------------------------------
# Fremdmarken, die in keinem ausgelieferten Text stehen dürfen. Reihenfolge
# zählt: längere Begriffe zuerst, sonst zerlegt eine kürzere Regel sie.
MARKEN = [
    ("GoHighLevel", "UmsatzAgent"),
    ("Go High Level", "UmsatzAgent"),
    ("HighLevel", "UmsatzAgent"),
    ("High Level", "UmsatzAgent"),
    ("LeadConnector", "UmsatzAgent"),
    ("Lead Connector", "UmsatzAgent"),
    ("LC Phone", "UmsatzAgent Telefon"),
    ("LC Email", "UmsatzAgent E-Mail"),
    ("LC-Phone", "UmsatzAgent Telefon"),
    ("help.leadconnectorhq.com", "support.umsatzagent.com"),
    ("leadconnectorhq.com", "umsatzagent.com"),
    ("gohighlevel.com", "umsatzagent.com"),
    ("app.gohighlevel.com", "app.umsatzagent.com"),
]

# Begriffe, die nach dem Übersetzen NICHT vorkommen dürfen. Findet der Prüfer
# einen davon, gilt der Artikel als nicht auslieferbar.
VERBOTEN = [
    "highlevel", "high level", "gohighlevel", "leadconnector", "lead connector",
    "leadconnectorhq", "freshdesk", "twilio", "mailgun",
]

# --- Terminologie ----------------------------------------------------------
# Links steht der englische Begriff aus der Quelle, rechts die deutsche
# Entsprechung, wie sie in der App tatsächlich heißt. Bleibt ein Begriff in der
# deutschen Oberfläche englisch, steht rechts derselbe Begriff.
GLOSSAR = {
    "Contacts": "Kontakte",
    "Contact": "Kontakt",
    "Conversations": "Unterhaltungen",
    "Opportunities": "Opportunities",
    "Pipeline": "Pipeline",
    "Workflow": "Workflow",
    "Workflows": "Workflows",
    "Trigger": "Trigger",
    "Action": "Aktion",
    "Campaign": "Kampagne",
    "Calendar": "Kalender",
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
    "Snapshot": "Snapshot",
    "Sub-Account": "Unterkonto",
    "Location": "Unterkonto",
    "Agency": "Agentur",
    "Dashboard": "Dashboard",
    "Settings": "Einstellungen",
    "Inbox": "Posteingang",
    "Reputation Management": "Bewertungs-Management",
    "Review": "Bewertung",
    "Membership": "Mitgliederbereich",
    "Community": "Community",
    "Social Planner": "Social Planner",
    "Email Builder": "E-Mail-Builder",
    "Invoice": "Rechnung",
    "Estimate": "Angebot",
    "Payment": "Zahlung",
    "Subscription": "Abo",
    "Coupon": "Gutschein",
    "Gift Card": "Gutscheinkarte",
    "Phone Number": "Telefonnummer",
    "Voicemail": "Mailbox",
    "Missed Call Text Back": "Rückruf-SMS bei verpasstem Anruf",
    "Conversation AI": "KI-Assistent",
    "Bot": "Assistent",
    "Prompt": "Prompt",
}

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

# 41 Quell-Kategorien sind zu viel für eine Seitenleiste. Sie werden zu diesen
# Themen gebündelt — sortiert danach, wonach Kunden tatsächlich suchen.
# Was hier nicht auftaucht, landet unter "Weitere Themen".
THEMEN = [
    ("Erste Schritte", ["Getting Started Category"]),
    ("Posteingang & Kontakte", ["Conversations Tab", "Contacts / SmartLists",
                                "Pipelines & Opportunities", "Custom Objects"]),
    ("KI-Assistent", ["Conversation AI Bot", "AI Agents"]),
    ("Telefonie & SMS", ["Phone Category", "Phone/ SMS Category", "WhatsApp Integration"]),
    ("E-Mail", ["LeadConnector Email", "SMTP"]),
    ("Marketing & Workflows", ["Marketing Category", "Workflow",
                               "Merge Fields & Custom Variables"]),
    ("Websites & Funnels", ["Funnels & Websites Category", "Blogs", "SEO", "Domains",
                            "External Tracking"]),
    ("Formulare & Umfragen", ["Surveys, Forms, QR Codes and Quizzes"]),
    ("Kalender & Termine", ["Scheduling & Calendars (Bookings)", "Events"]),
    ("Zahlungen & Shop", ["Payments, Invoices & Estimates", "E-Commerce",
                          "Subscription Products"]),
    ("Bewertungen", ["Reputation & Review Management", "GMB"]),
    ("Mitglieder & Community", ["Membership and Communities", "Client Portal Web and Mobile APP"]),
    ("Integrationen & Apps", ["LeadConnector Integrations", "Marketplace Apps",
                              "WordPress Integration", "Lead Connector Mobile & Desktop App"]),
    ("Auswertung", ["Reporting & Attribution"]),
    ("Konto & Einstellungen", ["Location Settings", "User Settings", "Company", "Billing"]),
]
