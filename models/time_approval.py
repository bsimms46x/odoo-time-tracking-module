from odoo import fields, models


class TimeEntryApproval(models.Model):
    _name = "time.entry.approval"
    _description = "Entry approval log"
    _order = "date desc"

    entry_id = fields.Many2one("time.entry", string="Time Entry", required=True, ondelete="cascade")
    manager_id = fields.Many2one("res.users", string="Manager", default=lambda self: self.env.user)
    state = fields.Selection([
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("requested", "Requested"),
    ], default="requested")
    comment = fields.Text()
    date = fields.Datetime(default=fields.Datetime.now)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, f"{record.entry_id.name} - {record.state.title()}"))
        return result
