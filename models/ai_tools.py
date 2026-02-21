from odoo import models
import logging

_logger = logging.getLogger(__name__)

class AiTools(models.AbstractModel):
    """
    Registry of Python functions that will be converted into ADK FunctionTools.
    All methods here must be designed to run with `self.env` to ensure strict RBAC.
    """
    _name = 'ai.concierge.tools'
    _description = 'AI Concierge Tool Registry'

    def get_odoo_tools(self):
        """
        Returns a dictionary of tool functions ready to be wrapped by ADK.
        Crucially, these python functions capture `self` in their closure, 
        giving the ADK Agent secure access to the current user's Odoo Environment.
        """
        
        def search_odoo_records(model_name: str, domain_str: str, limit: int = 5) -> str:
            """
            Searches the Odoo database for records matching a domain.
            
            Args:
                model_name: The technical name of the model (e.g., 'sale.order', 'res.partner').
                domain_str: A stringified python list representing the Odoo search domain (e.g., "[('name', 'ilike', 'John')]").
                limit: Maximum number of records to return.
            """
            try:
                # Basic safety check to ensure the model exists and the user has access
                if model_name not in self.env:
                    return f"Error: Model '{model_name}' does not exist or you lack access rights."
                
                import ast
                try:
                    domain = ast.literal_eval(domain_str)
                except Exception:
                    return f"Error: Invalid domain string format. Must be a valid python list like \"[('field', '=', 'value')]\""

                records = self.env[model_name].search_read(domain, limit=limit)
                if not records:
                    return f"No records found in {model_name} matching {domain}."
                
                import json
                # Sanitize datetime fields for JSON serialization if necessary, but search_read handles most
                return f"Found {len(records)} records: " + json.dumps(records, default=str)
                
            except Exception as e:
                _logger.error("AI Tool search_odoo_records failed: %s", str(e))
                return f"Execution Error: {str(e)}"

        def navigate_to_action(action_xml_id: str) -> str:
            """
            Tells the frontend to navigate the user to a specific Odoo Action.
            Returns a special JSON directive that the OWL Chat Component intercepts.
            
            Args:
                action_xml_id: The fully qualified XML ID of the action (e.g., 'sale.action_orders').
            """
            try:
                # We return a specially formatted string that the OWL controller will parse as a command
                return f'[[ACTION_DIRECTIVE: {action_xml_id}]]'
            except Exception as e:
                return f"Navigation Error: {str(e)}"

        def get_model_schema(model_name: str) -> str:
            """
            Returns the list of fields available for a specific Odoo model.
            Use this if you need to know what fields you can search or create.
            
            Args:
                model_name: The technical name of the model (e.g., 'res.partner').
            """
            try:
                if model_name not in self.env:
                     return f"Error: Model '{model_name}' inaccessible."
                fields_data = self.env[model_name].fields_get()
                summary = {k: v.get('type') for k, v in fields_data.items()}
                return f"Schema for {model_name}: {summary}"
            except Exception as e:
                 return f"Schema Error: {str(e)}"

        return {
            'search_odoo_records': search_odoo_records,
            'navigate_to_action': navigate_to_action,
            'get_model_schema': get_model_schema
        }
