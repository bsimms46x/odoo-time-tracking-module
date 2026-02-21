from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestTimeEntry(TransactionCase):
    def setUp(self):
        super().setUp()
        self.employee = self.env['hr.employee'].create({'name': 'Test Contractor'})
        try:
            self.policy = self.env.ref('time_tracking_module.time_tracking_policy_standard_hourly')
        except ValueError:
            self.policy = self.env['x_time_rule_policy'].create({
                'name': 'Hourly Test Policy',
                'price_per_unit': 100.0,
            })

    def _create_entry(self, state='draft'):
        return self.env['x_time_entry'].create({
            'employee_id': self.employee.id,
            'duration': 2.0,
            'billable': True,
            'policy_id': self.policy.id,
            'state': state,
        })

    def test_policy_amount_applies(self):
        entry = self._create_entry()
        self.assertEqual(entry.unit_amount, self.policy.compute_amount(entry))
        entry.duration = 3.5
        entry._apply_policy()
        self.assertAlmostEqual(entry.unit_amount, self.policy.compute_amount(entry), places=2)

    def test_state_transitions(self):
        entry = self._create_entry()
        entry.action_submit()
        self.assertEqual(entry.state, 'submitted')
        entry.action_approve()
        self.assertEqual(entry.state, 'approved')
        entry.action_reset()
        self.assertEqual(entry.state, 'draft')
        entry.action_submit()
        entry.action_reject(reason='Not accurate')
        self.assertEqual(entry.state, 'rejected')

    def test_timer_controls(self):
        entry = self._create_entry()
        entry.timer_state = 'stopped'
        entry.start_time = fields.Datetime.now() - timedelta(hours=1)
        entry.timer_state = 'running'
        entry.action_stop_timer()
        self.assertGreater(entry.duration, 0)
        self.assertEqual(entry.timer_state, 'stopped')
        entry.action_start_timer()
        self.assertEqual(entry.timer_state, 'running')
        entry.action_pause_timer()
        self.assertEqual(entry.timer_state, 'paused')
