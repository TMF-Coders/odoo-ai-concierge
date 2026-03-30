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
                from datetime import date, datetime
                # Sanitize datetime fields and bytes for JSON serialization safely
                def json_serial(obj):
                    if isinstance(obj, (datetime, date)):
                        return obj.isoformat()
                    if isinstance(obj, bytes):
                        return obj.decode('utf-8', errors='ignore')
                    return str(obj)

                return f"Found {len(records)} records: " + json.dumps(records, default=json_serial)
                
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

        def create_odoo_record(model_name: str, values_str: str) -> str:
            """
            Creates a new record in the specified Odoo model.
            
            Args:
                model_name: The technical name of the model (e.g., 'res.partner').
                values_str: A stringified dictionary of field names and their values (e.g., "{'name': 'New Company', 'is_company': True}").
            """
            try:
                if model_name not in self.env:
                    return f"Error: Model '{model_name}' does not exist or you lack access rights."
                
                import ast
                try:
                    values = ast.literal_eval(values_str)
                    if not isinstance(values, dict):
                        return "Error: Internal mapping error, values must evaluate to a dictionary."
                except Exception:
                    return f"Error: Invalid values string format. Must be a valid dictionary string like \"{{'name': 'Example'}}\""

                new_record = self.env[model_name].create(values)
                return f"Successfully created record in '{model_name}' with ID: {new_record.id}"
                
            except Exception as e:
                _logger.error("AI Tool create_odoo_record failed: %s", str(e))
                hint = ""
                if model_name == 'product.template' and 'categ_id' in str(e):
                    hint = " Hint: product.template requires a category. Please check available categories first."
                return f"Execution Error on create in {model_name}: {str(e)}{hint}"

        def update_odoo_record(model_name: str, record_id: int, values_str: str) -> str:
            """
            Updates an existing record in the specified Odoo model.
            
            Args:
                model_name: The technical name of the model (e.g., 'res.partner').
                record_id: The integer ID of the record to update.
                values_str: A stringified dictionary of fields to update (e.g., "{'phone': '+123456789'}").
            """
            try:
                if model_name not in self.env:
                    return f"Error: Model '{model_name}' does not exist or you lack access rights."
                
                import ast
                try:
                    values = ast.literal_eval(values_str)
                    if not isinstance(values, dict):
                        return "Error: Internal mapping error, values must evaluate to a dictionary."
                except Exception:
                    return f"Error: Invalid values string format. Must be a valid dictionary string like \"{{'phone': '+123456789'}}\""

                record = self.env[model_name].browse(record_id)
                if not record.exists():
                    return f"Error: Record with ID {record_id} not found in model '{model_name}'."
                
                record.write(values)
                return f"Successfully updated record {record_id} in '{model_name}' with values: {values_str}"
                
            except Exception as e:
                _logger.error("AI Tool update_odoo_record failed: %s", str(e))
                return f"Execution Error on update: {str(e)}"

        def execute_odoo_method(model_name: str, record_id: int, method_name: str) -> str:
            """
            Executes a Python business method on a specific Odoo record.
            
            Args:
                model_name: The technical name of the model (e.g., 'sale.order').
                record_id: The integer ID of the target record.
                method_name: The name of the python method to execute (e.g., 'action_confirm').
            """
            try:
                if model_name not in self.env:
                    return f"Error: Model '{model_name}' does not exist or you lack access rights."
                
                record = self.env[model_name].browse(record_id)
                if not record.exists():
                    return f"Error: Record with ID {record_id} not found in model '{model_name}'."
                
                method = getattr(record, method_name, None)
                if not method or not callable(method):
                     return f"Error: Method '{method_name}' not found or is not callable on model '{model_name}'."
                
                # Execute the method
                result = method()
                return f"Successfully executed '{method_name}' on '{model_name}' ID {record_id}. Result: {result}"
                
            except Exception as e:
                _logger.error("AI Tool execute_odoo_method failed: %s", str(e))
                return f"Execution Error on method {method_name}: {str(e)}"

        def log_internal_note(model_name: str, record_id: int, body: str) -> str:
            """
            Logs an internal note/message in the Chatter thread of an Odoo record.
            
            Args:
                model_name: The technical name of the model (e.g., 'res.partner', 'sale.order').
                record_id: The integer ID of the target record.
                body: The text or HTML body of the note to log.
            """
            try:
                if model_name not in self.env:
                    return f"Error: Model '{model_name}' does not exist or you lack access rights."
                
                record = self.env[model_name].browse(record_id)
                if not record.exists():
                    return f"Error: Record with ID {record_id} not found in model '{model_name}'."
                
                if not hasattr(record, 'message_post'):
                    return f"Error: Model '{model_name}' does not support Chatter/message_post."
                
                note = record.message_post(body=body, message_type='comment', subtype_xmlid='mail.mt_note')
                return f"Successfully logged internal note to '{model_name}' ID {record_id} with note ID {note.id}."
                
            except Exception as e:
                _logger.error("AI Tool log_internal_note failed: %s", str(e))
                return f"Execution Error on log_internal_note: {str(e)}"

        def analyze_odoo_data(model_name: str, domain_str: str, groupby_fields_str: str, fields_to_aggregate_str: str) -> str:
            """
            Performs grouped data aggregation and analytics in Odoo without fetching large volumes of raw records.
            Equivalent to SQL GROUP BY queries.
            
            Args:
                model_name: The technical name of the model (e.g., 'sale.order').
                domain_str: A stringified python list representing the search domain (e.g., "[('state', '=', 'sale')]").
                groupby_fields_str: A stringified python list of fields to group by (e.g., "['partner_id', 'date_order:month']").
                fields_to_aggregate_str: A stringified python list of fields to summarize/aggregate (e.g., "['amount_total']").
            """
            try:
                if model_name not in self.env:
                    return f"Error: Model '{model_name}' does not exist or you lack access rights."
                
                import ast
                import json
                from datetime import date, datetime
                
                try:
                    domain = ast.literal_eval(domain_str) if domain_str and domain_str.strip() not in ['[]', 'None', "''", '""'] else []
                    groupby = ast.literal_eval(groupby_fields_str)
                    fields = ast.literal_eval(fields_to_aggregate_str)
                except Exception as parse_error:
                    return f"Error: Arguments must be valid stringified lists. Details: {parse_error}"

                # Ensure that fields include groupby fields for standard read_group compliance if needed
                aggregated_data = self.env[model_name].read_group(
                    domain=domain,
                    fields=fields,
                    groupby=groupby
                )
                
                # Sanitize datetime fields safely for JSON output
                def json_serial(obj):
                    if isinstance(obj, (datetime, date)):
                        return obj.isoformat()
                    if hasattr(obj, '__class__') and obj.__class__.__name__ == 'LazyString':
                        # In case Odoo returns translated string proxies
                        return str(obj)
                    if isinstance(obj, tuple):
                         return str(obj)
                    return str(obj)

                return f"Aggregated {len(aggregated_data)} groups: " + json.dumps(aggregated_data, default=json_serial)
                
            except Exception as e:
                _logger.error("AI Tool analyze_odoo_data failed: %s", str(e))
                return f"Analytics Execution Error: {str(e)}"

        def list_odoo_models(search_term: str = None) -> str:
            """
            Lists the technical names of available Odoo models.
            Use this if you are unsure which model to use (e.g. searching for 'product' or 'sale').
            
            Args:
                search_term: Optional keyword to filter model names or descriptions (e.g., 'product').
            """
            try:
                domain = []
                if search_term:
                    domain = ['|', ('model', 'ilike', search_term), ('name', 'ilike', search_term)]
                
                models = self.env['ir.model'].search_read(domain, ['model', 'name'], limit=20)
                if not models:
                    return f"No models found matching '{search_term}'."
                
                return f"Available models matching '{search_term}': " + str([{m['model']: m['name']} for m in models])
            except Exception as e:
                return f"Discovery Error: {str(e)}"

        def get_record_count(model_name: str, domain_str: str = "[]") -> str:
            """
            Returns the total number of records matching a domain for a specific model.
            Use this for questions like 'How many X do we have?'.
            
            Args:
                model_name: The technical name of the model (e.g., 'product.template').
                domain_str: A stringified python list representing the search domain.
            """
            try:
                if model_name not in self.env:
                    return f"Error: Model '{model_name}' inaccessible."
                
                import ast
                try:
                    domain = ast.literal_eval(domain_str)
                except Exception:
                    domain = []
                
                count = self.env[model_name].search_count(domain)
                return f"Total count for {model_name}: {count}"
            except Exception as e:
                return f"Count Error: {str(e)}"

        def get_dashboard_data(dashboard_id: int) -> str:
            """
            Retrieves the raw JSON data of an Odoo Spreadsheet Dashboard.
            """
            try:
                dash = self.env['spreadsheet.dashboard'].browse(dashboard_id)
                if not dash.exists():
                    return f"Error: Dashboard ID {dashboard_id} not found."
                return dash.spreadsheet_data or "{}"
            except Exception as e:
                return f"Get Data Error: {str(e)}"

        def update_dashboard_data(dashboard_id: int, spreadsheet_data: str) -> str:
            """
            Updates an existing Odoo Spreadsheet Dashboard with new JSON data.
            """
            try:
                dash = self.env['spreadsheet.dashboard'].browse(dashboard_id)
                if not dash.exists():
                    return f"Error: Dashboard ID {dashboard_id} not found."
                dash.write({'spreadsheet_data': spreadsheet_data})
                return f"Dashboard {dashboard_id} updated successfully."
            except Exception as e:
                return f"Update Error: {str(e)}"

        def list_dashboard_groups() -> str:
            """
            Returns a list of all available Spreadsheet Dashboard groups (ID and Name).
            Use this to find where to place a new dashboard.
            """
            try:
                groups = self.env['spreadsheet.dashboard.group'].search([])
                result = "Available Dashboard Groups:\n"
                for g in groups:
                    result += f"- ID {g.id}: {g.name}\n"
                return result
            except Exception as e:
                return f"List Groups Error: {str(e)}"

        def list_dashboards(group_id: int = None) -> str:
            """
            Returns a list of existing dashboards, optionally filtered by group ID.
            """
            try:
                domain = [('dashboard_group_id', '=', group_id)] if group_id else []
                dashboards = self.env['spreadsheet.dashboard'].search(domain)
                result = f"Dashboards (Group {group_id if group_id else 'All'}):\n"
                for d in dashboards:
                    result += f"- ID {d.id}: {d.name} (Group: {d.dashboard_group_id.name})\n"
                return result
            except Exception as e:
                return f"List Dashboards Error: {str(e)}"

        def create_dashboard(name: str, group_id: int, spreadsheet_data: str = "{}") -> str:
            """
            Creates a new persistent Odoo Spreadsheet Dashboard.
            
            Args:
                name: The name for the new dashboard.
                group_id: The ID of the group to assign it to (use list_dashboard_groups to find one).
                spreadsheet_data: The JSON string for the spreadsheet content.
            """
            try:
                new_dash = self.env['spreadsheet.dashboard'].create({
                    'name': name,
                    'dashboard_group_id': group_id,
                    'spreadsheet_data': spreadsheet_data
                })
                return f"Dashboard '{name}' created successfully with ID {new_dash.id}."
            except Exception as e:
                return f"Create Error: {str(e)}"

        def search_attachments(search_query: str, limit: int = 5) -> str:
            """
            Searches for documents and files attached in Odoo (ir.attachment).
            Returns metadata like filename, model, and ID.
            
            Args:
                search_query: Keyword to search in filename or description.
                limit: Max results.
            """
            try:
                domain = ['|', ('name', 'ilike', search_query), ('description', 'ilike', search_query)]
                atts = self.env['ir.attachment'].search_read(domain, ['id', 'name', 'res_model', 'res_id', 'mimetype'], limit=limit)
                if not atts:
                    return f"No attachments found for query: {search_query}"
                return f"Found {len(atts)} attachments: " + str(atts)
            except Exception as e:
                return f"Error searching attachments: {str(e)}"

        return {
            'search_odoo_records': search_odoo_records,
            'navigate_to_action': navigate_to_action,
            'get_model_schema': get_model_schema,
            'create_odoo_record': create_odoo_record,
            'update_odoo_record': update_odoo_record,
            'execute_odoo_method': execute_odoo_method,
            'log_internal_note': log_internal_note,
            'analyze_odoo_data': analyze_odoo_data,
            'list_odoo_models': list_odoo_models,
            'get_record_count': get_record_count,
            'get_dashboard_data': get_dashboard_data,
            'update_dashboard_data': update_dashboard_data,
            'search_attachments': search_attachments,
        }
