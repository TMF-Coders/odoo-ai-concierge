import ast
import json
from odoo.tests.common import TransactionCase

class TestAiToolsV2(TransactionCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a test partner for chatter and method tests
        cls.test_partner = cls.env['res.partner'].create({
            'name': 'AI Concierge Test Partner',
            'email': 'ai.test@example.com',
            'is_company': True,
        })
        
        # Load the tools dict using the abstract model's environment
        cls.tools_dict = cls.env['ai.concierge.tools'].get_odoo_tools()

    def test_execute_odoo_method(self):
        """Test the execute_odoo_method tool using toggle_active on res.partner"""
        self.assertTrue(self.test_partner.active, "Partner should be active initially")
        
        tool = self.tools_dict['execute_odoo_method']
        
        # Execute toggle_active
        response = tool('res.partner', self.test_partner.id, 'toggle_active')
        
        self.assertIn('Successfully executed', response)
        self.assertFalse(self.test_partner.active, "Partner should be archived after toggle_active")
        
    def test_log_internal_note(self):
        """Test the log_internal_note tool using res.partner (mail.thread)"""
        tool = self.tools_dict['log_internal_note']
        
        test_message = "<p>This is a test note from ADK</p>"
        response = tool('res.partner', self.test_partner.id, test_message)
        
        self.assertIn('Successfully logged internal note', response)
        
        # Verify the message was actually created
        message = self.env['mail.message'].search([
            ('model', '=', 'res.partner'),
            ('res_id', '=', self.test_partner.id),
            ('body', 'like', test_message)
        ])
        self.assertTrue(message, "Internal note was not found in mail.message")
        
    def test_analyze_odoo_data(self):
        """Test the analyze_odoo_data tool doing a read_group on res.partner"""
        tool = self.tools_dict['analyze_odoo_data']
        
        # we will group partners by is_company
        domain_str = "[]"
        groupby_str = "['is_company']"
        fields_str = "['is_company']"
        
        response = tool('res.partner', domain_str, groupby_str, fields_str)
        
        self.assertIn('Aggregated', response)
        self.assertIn('is_company', response)
        
        # Parsing the JSON from the end of the response
        json_data = response.split("groups: ", 1)[1]
        data = json.loads(json_data)
        
        self.assertTrue(isinstance(data, list), "Response should contain a serialized list.")
        self.assertTrue(len(data) > 0, "There should be at least some groups returned.")
