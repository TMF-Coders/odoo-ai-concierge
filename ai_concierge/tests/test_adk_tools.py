from odoo.tests.common import TransactionCase

class TestAiConciergeTools(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAiConciergeTools, cls).setUpClass()
        cls.tools_repo = cls.env['ai.concierge.tools']
        
    def test_01_search_odoo_records(self):
        """ Verify the search tool correctly accesses self.env and respects Odoo arguments """
        tools = self.tools_repo.get_odoo_tools()
        search_func = tools['search_odoo_records']
        
        # We search for the base partner (YourCompany)
        res = search_func('res.partner', "[('id', '=', 1)]", limit=1)
        
        # It should return a JSON-serialized string containing the record data
        self.assertIn('Found', res)
        self.assertIn('"id": 1', res)
        
    def test_02_search_invalid_domain(self):
        """ Ensure the agent cannot crash the server with halluciated domains """
        tools = self.tools_repo.get_odoo_tools()
        search_func = tools['search_odoo_records']
        
        # Pass a completely broken domain string
        res = search_func('res.partner', "not_a_list")
        
        self.assertIn("Invalid domain string", res)

    def test_03_navigate_to_action(self):
        """ Verify the navigation directive is correctly formatted """
        tools = self.tools_repo.get_odoo_tools()
        nav_func = tools['navigate_to_action']
        
        res = nav_func('base.action_partner_form')
        self.assertEqual(res, "[[ACTION_DIRECTIVE: base.action_partner_form]]")
