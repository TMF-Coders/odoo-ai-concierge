# AI Concierge (Odoo Copilot)

This application transforms Odoo 19 by embedding a conversational, action-oriented AI Assistant directly into the user interface. Powered by the **Google Agent Development Kit (ADK)** and the Gemini model family.

## Features
- **Native Odoo Experience:** A floating OWL Chat component always available in the Systray.
- **Agentic Navigation:** Ask the AI to "Take me to yesterday's sales" and watch the Odoo UI navigate automatically.
- **Data Searching & Summarization:** The Agent can query the live Postgres database to generate reports on the fly across CRM, Inventory, Sales, and Accounting.
- **100% RBAC Secure:** All AI database interactions are executed using Odoo's internal `self.env`, guaranteeing that the AI can only read or write records the active human user is permitted to see.

## Installation & Configuration
1. Install the Python dependency on your Odoo Server:
   ```bash
   pip3 install google-adk
   ```
2. Install this module via the Odoo Apps menu.
3. Navigate to **Settings -> General Settings -> AI Concierge**.
4. Paste your Google Gemini API Key and select your preferred reasoning model (e.g., `gemini-1.5-pro`).

## Technical Architecture
The module bridges the gap between Odoo's Python ORM and Google's LLMs. We leverage ADK's `FunctionTool` to wrap Odoo's security-first ORM methods (`search_read`, `create`) and inject them into the agent's context dynamically on every user request.
