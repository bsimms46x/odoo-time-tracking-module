from odoo import api, fields, models


class TimeSheetTemplate(models.Model):
    _name = "time.sheet.template"
    _description = "Time entry template"

    name = fields.Char(required=True)
    default_project_id = fields.Many2one("project.project", string="Project")
    default_task_id = fields.Many2one("project.task", string="Task")
    default_duration = fields.Float(default=1.0, digits="Time")
    billable_default = fields.Boolean(default=True)
    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")
    default_description = fields.Text()
    policy_id = fields.Many2one("time.rule.policy", string="Billing Policy")

    def action_create_entry(self):
        self.ensure_one()
        entry = self.env["time.entry"].create({
            "name": self.name,
            "project_id": self.default_project_id.id,
            "task_id": self.default_task_id.id,
            "duration": self.default_duration,
            "billable": self.billable_default,
            "analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)],
            "description": self.default_description,
            "policy_id": self.policy_id.id,
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "time.entry",
            "res_id": entry.id,
            "view_mode": "form",
        }

    def name_get(self):
        return [(template.id, template.name) for template in self]
