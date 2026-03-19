import os
from odoo import models, api, _
from odoo.exceptions import UserError
import logging

try:
    from google.adk.agents import LlmAgent
    from google.adk.apps.app import App, EventsCompactionConfig
    from google.adk.agents.context_cache_config import ContextCacheConfig
    from google.adk.tools import FunctionTool
    from google.adk.runners import InMemoryRunner
    from google.adk.events.event import Event
    from google.genai import types
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

    def _init_adk_app(self):
        """ Initializes the ADK App and Agent with current Config Settings and injected Tools. """
        if not ADK_AVAILABLE:
            raise UserError(_("The 'google-adk' Python library is not installed. Please pip install google-adk."))

        # 1. Fetch Dynamic Settings
        config = self.env['ir.config_parameter'].sudo()
        api_key = config.get_param('ai_concierge.api_key')
        if not api_key:
             raise UserError(_("Google Gemini API Key is missing. Please configure it in General Settings."))
             
        model_name = config.get_param('ai_concierge.model', 'gemini-1.5-pro')
        system_prompt = config.get_param('ai_concierge.system_prompt', "You are a helpful ERP assistant.")

        # 2. Rehydrate Tools bound to current user's self.env
        tools_repo = self.env['ai.concierge.tools'].get_odoo_tools()
        adk_tools = [
            FunctionTool(tools_repo['search_odoo_records']),
            FunctionTool(tools_repo['navigate_to_action']),
            FunctionTool(tools_repo['get_model_schema']),
            FunctionTool(tools_repo['create_odoo_record']),
            FunctionTool(tools_repo['update_odoo_record']),
            FunctionTool(tools_repo['execute_odoo_method']),
            FunctionTool(tools_repo['log_internal_note']),
            FunctionTool(tools_repo['analyze_odoo_data']),
            FunctionTool(tools_repo['list_odoo_models']),
            FunctionTool(tools_repo['get_record_count']),
            FunctionTool(tools_repo['get_dashboard_data']),
            FunctionTool(tools_repo['update_dashboard_data']),
            FunctionTool(tools_repo['list_dashboard_groups']),
            FunctionTool(tools_repo['list_dashboards']),
            FunctionTool(tools_repo['create_dashboard']),
            FunctionTool(tools_repo['search_attachments']),
        ]

        # 3. Enhance instruction with Odoo-specific knowledge and best practices
        user_lang = self.env.user.lang or 'en_US'
        lang_name = self.env['res.lang']._lang_get(user_lang).name or "English"
        
        base_instruction = (
            f"You are the AI Concierge, a highly intelligent Odoo ERP assistant. "
            f"CRITICAL: You MUST ALWAYS respond in {lang_name}. The user's preferred language is {lang_name}. "
            "\n\nCRITICAL KNOWLEDGE:\n"
            "- PRODUCTS: 'product.template' (standard) or 'product.product' (variant).\n"
            "- ATTACHMENTS: Use 'search_attachments' to find files. You can see images and PDFs sent by the user.\n"
            "- DASHBOARDS: You can manage persistent Odoo Spreadsheet dashboards.\n"
            "  * Use 'list_dashboard_groups' to see categories.\n"
            "  * Use 'list_dashboards' to find existing ones.\n"
            "  * Use 'create_dashboard' to save a new report permanently in Odoo.\n"
            "  * Use 'update_dashboard_data' to edit them.\n"
            "- FINANCIALS (P&L): To generate a P&L or sales summary, use 'analyze_odoo_data' on 'account.move' (for invoices/expenses) or 'sale.order'. \n"
            "  * Revenue corresponds to 'move_type' = 'out_invoice'. \n"
            "  * Expenses correspond to 'move_type' = 'in_invoice'.\n\n"
            "RICH OUTPUTS:\n"
            "- PROACTIVITY: If a user asks for a 'report' or 'summary', DO NOT say you can't do it. Use 'analyze_odoo_data' to get the numbers and then render an A2UI Dashboard/KPIs.\n"
            "- PERSISTENCE: If the user likes a summary and wants to save it, use 'create_dashboard' to make it a permanent part of Odoo.\n"
            "- SEARCHING: Always use 'ilike' with % wildcard. Example: [('name', 'ilike', '%Mouse%')].\n"
            "- VISION/OCR: Analyze images/PDFs provided by the user to extract business data (invoices, products).\n"
            "- A2UI PROTOCOL: Use for dashboards/summaries. Primitives: Text, Image, KPI, Chart.\n"
            "- Example A2UI Sales Summary: [A2UI_BEGIN]{\"components\":[{\"id\":\"r\",\"component\":{\"Column\":{\"children\":{\"explicitList\":[\"h\",\"s\"]}}}},{\"id\":\"h\",\"component\":{\"Text\":{\"text\":\"Ventas\",\"style\":\"HEADER\"}}},{\"id\":\"s\",\"component\":{\"Row\":{\"children\":{\"explicitList\":[\"v\",\"p\"]}}}},{\"id\":\"v\",\"component\":{\"KPI\":{\"value\":\"1500€\",\"label\":\"Total\"}}},{\"id\":\"p\",\"component\":{\"KPI\":{\"value\":\"12\",\"label\":\"Pedidos\"}}}],\"dataModel\":{},\"root\":\"r\"}[A2UI_END]\n"
            "\n- DISCOVERY: Use 'list_odoo_models' and 'get_model_schema' to explore fields and models.\n"
            "\nUSER CONTEXT:\n"
        )
        
        full_instruction = f"{base_instruction}{system_prompt}"

        # 4. Build the Agent.
        os.environ["GOOGLE_API_KEY"] = api_key
        
        # Merge instructions back into single 'instruction' field to ensure 
        # it is treated as system_instruction, especially for smaller models.
        agent = LlmAgent(
            name="odoo_concierge",
            description="Intelligent Assistant embedded in Odoo ERP",
            model=model_name,
            instruction=full_instruction,
            tools=adk_tools
        )

        # 5. Wrap in an App to enable Caching and Compaction
        app = App(
            name="odoo_ai_concierge",
            root_agent=agent,
            context_cache_config=ContextCacheConfig(
                min_tokens=2048,   # Enable caching for instructions > 2k tokens
                ttl_seconds=3600,  # Cache for 1 hour
                cache_intervals=5  # Refresh cache every 5 uses
            ),
            events_compaction_config=EventsCompactionConfig(
                compaction_interval=10, # Summarize history every 10 turns
                overlap_size=1          # Keep 1 event overlap for continuity
            )
        )
        return app

    @api.model
    def process_chat_message(self, message_text, history=None, active_context=None):
        """
        Main entry point for the OWL Frontend.
        Receives the user string or dict, runs the ADK Agent, and returns the response.
        """
        try:
            # Handle dictionary payload from frontend (e.g. including attachments)
            attachments = []
            final_text = ""
            if isinstance(message_text, dict):
                final_text = message_text.get('content', '')
                attachments = message_text.get('attachments', [])
            else:
                final_text = message_text

            app = self._init_adk_app()
            
            # If we received visual context from the OWL UI
            context_injection = ""
            if active_context and type(active_context) is dict:
                active_model = active_context.get('active_model')
                active_id = active_context.get('active_id')
                view_type = active_context.get('view_type')
                
                if active_model:
                    if active_id and view_type == 'form':
                         context_injection = f"[CONTEXT: The user is currently looking at record ID {active_id} of '{active_model}']\n"
                    else:
                         context_injection = f"[CONTEXT: The user is browsing the '{active_model}' view]\n"
            
            # 5. Prepare the new user message parts
            parts = [types.Part(text=f"{context_injection}{final_text}")]
            
            # Map attachments to Gemini Parts
            for att in attachments:
                mime_type = att.get('type')
                data_b64 = att.get('data')
                if mime_type and data_b64:
                    import base64
                    parts.append(types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=base64.b64decode(data_b64)
                        )
                    ))

            new_message = types.Content(role="user", parts=parts)

            # 3. Create a Runner with the App
            runner = InMemoryRunner(app=app)
            user_id = str(self.env.user.id)
            session_id = str(self.env.context.get('ai_session_id', 'default_session'))
            
            # 4. Expert Audit: Inject previous history into the runner's session
            if history:
                session = runner.session_service.get_session_sync(
                    app_name=runner.app_name, 
                    user_id=user_id, 
                    session_id=session_id
                )
                if not session:
                    session = runner.session_service.create_session_sync(
                        app_name=runner.app_name, 
                        user_id=user_id, 
                        session_id=session_id
                    )
                
                # Convert Odoo history format to ADK Events
                session.events = []
                for entry in history:
                    role = entry.get('role', 'user')
                    adk_role = "user" if role == "user" else "model"
                    content_text = ""
                    parts_hist = entry.get('parts', [])
                    if parts_hist:
                        content_text = parts_hist[0].get('text', '')
                    else:
                        content_text = entry.get('content', '')
                        
                    if content_text:
                        event = Event(
                            invocation_id="init_history",
                            author=adk_role,
                            content=types.Content(role=adk_role, parts=[types.Part(text=content_text)])
                        )
                        session.events.append(event)

            # 6. Run the agent. InMemoryRunner.run returns a Generator of Events
            events = list(runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message
            ))

            final_message = ""
            for event in events:
                _logger.debug("ADK Event raw: %s", event)
                
                # Check for content from the model or tools
                if event.content and event.content.parts and event.author != "user":
                    for part in event.content.parts:
                        # 1. Capture direct text from Assistant
                        if hasattr(part, 'text') and part.text:
                            final_message += part.text
                        
                        # 2. Capture Tool Responses if they contain Action Directives
                        # This happens when the agent calls 'navigate_to_action'
                        elif hasattr(part, 'function_response') and part.function_response:
                            resp_content = str(part.function_response.response.get('result', ''))
                            if '[[ACTION_DIRECTIVE:' in resp_content:
                                final_message += resp_content
                            _logger.debug("Tool response from %s: %s", part.function_response.name, resp_content)
                            
                        elif hasattr(part, 'function_call') and part.function_call:
                            _logger.debug("Agent is calling tool: %s with args: %s", 
                                         part.function_call.name, part.function_call.args)
                        # If the agent is returning an action directive but no text, 
                        # we still want to detect it if the ADK formatted it as part of text
                        # but some versions of ADK might put it in other part types.
            
            if not final_message:
                final_message = _("I encountered an error processing your request.")

            # Check if the AI returned a special ACTION_DIRECTIVE
            if '[[ACTION_DIRECTIVE:' in final_message:
                # Extract the action XML ID and tell the frontend to navigate
                parts = final_message.split('[[ACTION_DIRECTIVE:')
                if len(parts) > 1:
                    action_id = parts[1].split(']]')[0].strip()
                    return {
                        'type': 'action',
                        'action_xml_id': action_id,
                        'message': final_message.replace(f'[[ACTION_DIRECTIVE: {action_id}]]', '').strip()
                    }

            return {
                'type': 'text',
                'message': final_message
            }
            
        except Exception as e:
            _logger.exception("AI Concierge Agent Error")
            return {
                'type': 'error',
                'message': _("My neural circuits encountered an error: %s") % str(e)
            }
