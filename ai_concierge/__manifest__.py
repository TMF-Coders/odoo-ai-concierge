# -*- coding: utf-8 -*-
{
    'name': "AI Concierge (Odoo Copilot)",
    'summary': "Universal LLM Agent integrated into Odoo (Google ADK)",
    'description': """
AI Concierge (Odoo Copilot)
===========================
This application embeds a powerful AI assistant powered by Google Agent Development Kit (ADK) directly into your Odoo ERP.
It operates completely within Odoo's security model (RBAC), capable of answering operational questions, navigating the interface, 
and automating tasks securely across any module (CRM, Sales, Inventory, Accounting, etc.) using 'FunctionTool's.

Features:
- Global Configuration (API Key & Model Selection, supports Gemini & OpenAI).
- Native ADK Orchestration & Autonomous Navigation.
- Extensible Tool Registry for any Odoo Model.
- Persistent Chat History & Context Awareness.
- Modern OWL Sidebar Interface.

Target Audience: Built for any sector (Services, Retail, Logistics, Manufacturing, etc.).
    """,
    'author': "TMFCoders SL",
    'website': 'https://tmfcoders.com',
    'category': 'Productivity/Discuss',
    'images': ['static/description/banner.png', 'static/description/screenshot_1.png', 'static/description/screenshot_2.png'],
    'version': '19.0.1.0.0',
    'price': 89.00,
    'currency': 'EUR',
    'license': 'OPL-1',
    'depends': ['base', 'web', 'mail'],
    'external_dependencies': {
        'python': ['google-adk'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ai_concierge/static/src/components/chat/chat.js',
            'ai_concierge/static/src/components/chat/a2ui_surface.js',
            'ai_concierge/static/src/components/chat/chat.xml',
            'ai_concierge/static/src/components/chat/a2ui_surface.xml',
            'ai_concierge/static/src/components/chat/chat.scss',
            'ai_concierge/static/src/components/systray_item/systray_item.js',
            'ai_concierge/static/src/components/systray_item/systray_item.xml',
            'ai_concierge/static/src/components/systray_item/systray_item.scss',
        ],
    },
    'installable': True,
    'application': True,
}
