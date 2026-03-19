from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_concierge_api_key = fields.Char(
        string="Google Gemini API Key",
        config_parameter='ai_concierge.api_key',
        help="Paste your API Key from Google AI Studio or Vertex."
    )
    
    ai_concierge_model = fields.Selection(
        [
            ('gemini-3.1-pro-preview', 'Gemini 3.1 Pro (Next-Gen Reasoning)'),
            ('gemini-3.1-flash-lite-preview', 'Gemini 3.1 Flash Lite (Ultra Fast)'),
            ('gemini-2.5-flash-lite', 'Gemini 2.5 Flash Lite (Optimized)'),
        ],
        string="Default AI Model",
        config_parameter='ai_concierge.model',
        default='gemini-3.1-flash-lite-preview',
        help="Select the ADK agent's reasoning engine model."
    )
    
    ai_concierge_system_prompt = fields.Char(
        string="Agent Persona / System Prompt",
        config_parameter='ai_concierge.system_prompt',
        default="You are the AI Concierge of this company's ERP. Answer politely, concisely, and execute Odoo tasks when requested.",
        help="Define the default personality and instructions for the agent."
    )
