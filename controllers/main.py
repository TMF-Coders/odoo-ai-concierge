from odoo import http
from odoo.http import request

class AiConciergeController(http.Controller):
    @http.route('/ai_concierge/chat', type='json', auth='user')
    def process_chat(self, message):
        """
        Receives chat payloads from the OWL component and routes them
        to the ADK Orchestrator. Requires an authenticated active session.
        """
        if not message:
            return {'type': 'error', 'message': 'Empty message received.'}
            
        orchestrator = request.env['ai.concierge.orchestrator']
        return orchestrator.process_chat_message(message)
