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
            ('gemini-1.5-pro', 'Gemini 1.5 Pro (Powerful, Reasoning)'),
            ('gemini-1.5-flash', 'Gemini 1.5 Flash (Fast, Lightweight)'),
            ('gemini-2.0-flash', 'Gemini 2.0 Flash (Next-Gen Speed)'),
        ],
        string="Default AI Model",
        config_parameter='ai_concierge.model',
        default='gemini-1.5-pro',
        help="Select the ADK agent's reasoning engine model."
    )
    
    ai_concierge_system_prompt = fields.Text(
        string="Agent Persona / System Prompt",
        config_parameter='ai_concierge.system_prompt',
        default="You are the AI Concierge of this company's ERP. Answer politely, concisely, and execute Odoo tasks when requested.",
        help="Define the default personality and instructions for the agent."
    )
