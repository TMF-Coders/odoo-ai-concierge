from odoo import http
from odoo.http import request

class AiConciergeController(http.Controller):
    @http.route('/ai/v1/chat', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def process_chat(self, message, **kw):
        """
        Receives chat payloads from the OWL component and routes them
        to the ADK Orchestrator. Requires an authenticated active session.
        """
        if not message:
            return {'type': 'error', 'message': 'Empty message received.'}
            
        orchestrator = request.env['ai.concierge.orchestrator']
        # Extract history from the request payload if available (assumed to come from kwargs)
        history = kw.get('history', [])
        return orchestrator.process_chat_message(message, history=history)
