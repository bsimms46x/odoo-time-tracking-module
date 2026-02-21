from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TimeEntry(models.Model):
    _name = "x_time_entry"
    _description = "Tracked time entry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(string="Reference", default="New time entry", tracking=True)
    employee_id = fields.Many2one("hr.employee", required=True, default=lambda self: self.env.user.employee_ids[:1])
    user_id = fields.Many2one("res.users", related="employee_id.user_id", store=True, readonly=True)
    project_id = fields.Many2one("project.project", string="Project")
    task_id = fields.Many2one("project.task", string="Task")
    date = fields.Date(default=fields.Date.context_today, required=True)
    duration = fields.Float(string="Hours", digits="Time", default=0.0, help="Total duration in hours")
    billable = fields.Boolean(default=True)
    description = fields.Text()
    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, readonly=True)
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", store=True, readonly=True)
    unit_amount = fields.Monetary(string="Amount", currency_field="currency_id")
    state = fields.Selection([
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ], default="draft", tracking=True)
    timer_state = fields.Selection([
        ("stopped", "Stopped"),
        ("running", "Running"),
        ("paused", "Paused"),
    ], default="stopped")
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    batch_id = fields.Many2one("x_time_entry_batch", string="Batch")
    approval_ids = fields.One2many("x_time_entry_approval", "entry_id", string="Approvals")
    policy_id = fields.Many2one("x_time_rule_policy", string="Billing Policy")
    budget_exceeded = fields.Boolean(compute="_compute_budget_exceeded", store=True)

    @api.depends("duration", "task_id")
    def _compute_budget_exceeded(self):
        for entry in self:
            if entry.task_id and entry.task_id.planned_hours:
                total = sum(
                    self.env['x_time_entry'].search([('task_id', '=', entry.task_id.id)]).mapped('duration'))
                entry.budget_exceeded = total > (entry.task_id.planned_hours or 0.0)
            else:
                entry.budget_exceeded = False

    @api.model
    def create(self, vals):
        entry = super().create(vals)
        entry._apply_policy()
        return entry

    def write(self, vals):
        res = super().write(vals)
        self._apply_policy()
        return res

    def _apply_policy(self):
        for entry in self:
            policy = entry.policy_id
            if not policy and entry.project_id:
                policy = self.env['x_time_rule_policy'].search([
                    ('project_ids', 'in', entry.project_id.id)], limit=1)
            if policy and entry.billable and entry.duration:
                entry.unit_amount = policy.compute_amount(entry)
            else:
                entry.unit_amount = 0.0

    def action_start_timer(self):
        now = fields.Datetime.now()
        for entry in self:
            if entry.timer_state == 'running':
                continue
            entry.start_time = now
            entry.timer_state = 'running'
            entry.state = 'draft'

    def action_pause_timer(self):
        now = fields.Datetime.now()
        for entry in self.filtered(lambda r: r.timer_state == 'running'):
            entry.duration += (now - entry.start_time).total_seconds() / 3600 if entry.start_time else 0.0
            entry.end_time = now
            entry.timer_state = 'paused'

    def action_stop_timer(self):
        now = fields.Datetime.now()
        for entry in self.filtered(lambda r: r.timer_state in ('running', 'paused')):
            running_duration = 0.0
            if entry.start_time:
                running_duration = (now - entry.start_time).total_seconds() / 3600
            entry.duration += running_duration
            entry.end_time = now
            entry.timer_state = 'stopped'
            entry.state = 'draft'

    def action_submit(self):
        for entry in self:
            if entry.state not in ('draft', 'rejected'):
                raise ValidationError(_('Only draft or rejected entries can be submitted.'))
            entry.state = 'submitted'
            entry.message_post(body=_('Entry submitted for approval.'))

    def action_approve(self):
        for entry in self:
            if entry.state != 'submitted':
                raise ValidationError(_('Only submitted entries can be approved.'))
            entry.state = 'approved'
            self.env['x_time_entry_approval'].create({
                'entry_id': entry.id,
                'manager_id': self.env.user.id,
                'state': 'approved',
                'comment': _('Approved by %s') % self.env.user.name,
            })
            entry.message_post(body=_('Entry approved.'))

    def action_reject(self, reason=''):
        for entry in self:
            if entry.state != 'submitted':
                raise ValidationError(_('Only submitted entries can be rejected.'))
            entry.state = 'rejected'
            self.env['x_time_entry_approval'].create({
                'entry_id': entry.id,
                'manager_id': self.env.user.id,
                'state': 'rejected',
                'comment': reason or _('Rejected by %s') % self.env.user.name,
            })
            entry.message_post(body=_('Entry rejected.'))

    def action_reset(self):
        for entry in self:
            entry.state = 'draft'
            entry.batch_id = False

    def action_prepare_batch(self):
        batch = self.env['x_time_entry_batch'].create({
            'name': 'Batch %s' % fields.Date.today(),
            'date_from': min(self.mapped('date')),
            'date_to': max(self.mapped('date')),
            'entry_ids': [(6, 0, self.ids)],
        })
        return batch

    def get_invoice_line_values(self):
        self.ensure_one()
        if not self.billable or self.state != 'approved':
            return {}
        return {
            'product_id': False,
            'name': self.name,
            'quantity': self.duration,
            'price_unit': self.unit_amount / self.duration if self.duration else 0.0,
            'analytic_account_id': self.project_id.analytic_account_id.id if self.project_id else False,
            'account_id': self.policy_id.account_id.id if self.policy_id else False,
        }

    @api.model
    def _cron_notify_pending_entries(self):
        pending = self.search([('state', '=', 'submitted')])
        if not pending:
            return
        pending.message_post(body=_('There are pending time entries awaiting approval.'))
        return True

    @api.model
    def _get_default_name(self):
        return _('Time entry %s') % fields.Date.context_today(self)

    def name_get(self):
        result = []
        for entry in self:
            name = entry.name or entry._get_default_name()
            if entry.employee_id:
                name = '[%s] %s' % (entry.employee_id.name, name)
            result.append((entry.id, name))
        return result
