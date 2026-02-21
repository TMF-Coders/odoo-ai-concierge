import os
from odoo import models, api, _
from odoo.exceptions import UserError
import logging

try:
    from google.adk.agents import LlmAgent
    from google.adk.tools import FunctionTool
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False

_logger = logging.getLogger(__name__)

class AiAgentOrchestrator(models.AbstractModel):
    """
    Core orchestrator that instantiates the ADK LlmAgent on the fly 
    using the dynamic configuration stored in Odoo.
    """
    _name = 'ai.concierge.orchestrator'
    _description = 'AI Concierge ADK Orchestrator'

    def _init_adk_agent(self):
        """ Initializes the ADK Agent with current Config Settings and injected Tools. """
        if not ADK_AVAILABLE:
            raise UserError(_("The 'google-adk' Python library is not installed. Please pip install google-adk."))

        # 1. Fetch Dynamic Settings
        config = self.env['ir.config_parameter'].sudo()
        api_key = config.get_param('ai_concierge.api_key')
        if not api_key:
             raise UserError(_("Google Gemini API Key is missing. Please configure it in General Settings."))
             
        model_name = config.get_param('ai_concierge.model', 'gemini-1.5-pro')
        system_prompt = config.get_param('ai_concierge.system_prompt', "You are a helpful ERP assistant.")

        # Temporarily inject API Key into environment for ADK to pick it up
        os.environ["GOOGLE_API_KEY"] = api_key

        # 2. Rehydrate Tools bound to current user's self.env
        tools_repo = self.env['ai.concierge.tools'].get_odoo_tools()
        adk_tools = [
            FunctionTool.from_function(tools_repo['search_odoo_records']),
            FunctionTool.from_function(tools_repo['navigate_to_action']),
            FunctionTool.from_function(tools_repo['get_model_schema']),
        ]

        # 3. Build the Agent
        agent = LlmAgent(
            name="odoo-concierge",
            description="Intelligent Assistant embedded in Odoo ERP",
            model=model_name,
            instruction=system_prompt,
            tools=adk_tools
        )
        return agent

    @api.model
    def process_chat_message(self, message_text, history=None):
        """
        Main entry point for the OWL Frontend.
        Receives the user string, runs the ADK Agent, and returns the response.
        """
        try:
            agent = self._init_adk_agent()
            
            # TODO: If history is provided, we should inject it into the ADK run context.
            # For this MVP step, we run stateless or rely on ADK's default run semantics.
            
            response = agent.run(message_text)
            
            # Check if the AI returned a special ACTION_DIRECTIVE
            if '[[ACTION_DIRECTIVE:' in response.text:
                # Extract the action XML ID and tell the frontend to navigate
                parts = response.text.split('[[ACTION_DIRECTIVE:')
                if len(parts) > 1:
                    action_id = parts[1].split(']]')[0].strip()
                    return {
                        'type': 'action',
                        'action_xml_id': action_id,
                        'message': response.text.replace(f'[[ACTION_DIRECTIVE: {action_id}]]', '').strip()
                    }

            return {
                'type': 'text',
                'message': response.text
            }
            
        except Exception as e:
            _logger.exception("AI Concierge Agent Error")
            return {
                'type': 'error',
                'message': _("My neural circuits encountered an error: %s") % str(e)
            }
