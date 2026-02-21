from odoo import fields, models


class TimeRulePolicy(models.Model):
    _name = "time.rule.policy"
    _description = "Time entry billing/rate policy"

    name = fields.Char(required=True)
    billable_type = fields.Selection([
        ("hourly", "Hourly"),
        ("fixed", "Fixed"),
        ("project", "Project rate"),
    ], default="hourly")
    price_per_unit = fields.Float(default=0.0)
    account_id = fields.Many2one("account.account", string="Revenue Account")
    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic Account")
    project_ids = fields.Many2many("project.project", string="Projects")
    tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")

    def compute_amount(self, entry):
        if not entry.duration:
            return 0.0
        if self.billable_type == "hourly":
            return self.price_per_unit * entry.duration
        elif self.billable_type == "fixed":
            return self.price_per_unit
        elif self.billable_type == "project" and entry.project_id:
            return self.price_per_unit * entry.duration
        return 0.0

    def name_get(self):
        return [(policy.id, policy.name) for policy in self]
