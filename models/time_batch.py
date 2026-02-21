from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TimeEntryBatch(models.Model):
    _name = "time.entry.batch"
    _description = "Batch of time entries for reviews"
    _order = "date_from desc, id desc"

    name = fields.Char(default=lambda self: _("Manual Batch"), required=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("review", "In Review"),
        ("ready", "Ready for Billing"),
        ("invoiced", "Invoiced"),
    ], default="draft")
    entry_ids = fields.One2many("time.entry", "batch_id", string="Entries")
    total_hours = fields.Float(compute="_compute_totals", store=True)
    billable_amount = fields.Monetary(compute="_compute_totals", store=True, currency_field="company_currency")
    company_currency = fields.Many2one("res.currency", compute="_compute_currency", store=True)

    @api.depends("entry_ids.currency_id")
    def _compute_currency(self):
        for batch in self:
            batch.company_currency = batch.entry_ids[:1].currency_id if batch.entry_ids else self.env.company.currency_id

    @api.depends("entry_ids.duration", "entry_ids.unit_amount", "entry_ids.billable")
    def _compute_totals(self):
        for batch in self:
            duration = sum(batch.entry_ids.mapped("duration"))
            billable_amount = sum(batch.entry_ids.filtered(lambda r: r.billable).mapped("unit_amount"))
            batch.total_hours = duration
            batch.billable_amount = billable_amount

    def action_request_review(self):
        for batch in self:
            if not batch.entry_ids:
                raise ValidationError(_("Please add entries before requesting review."))
            batch.state = "review"

    def action_ready_for_billing(self):
        for batch in self:
            if any(entry.state != "approved" for entry in batch.entry_ids):
                raise ValidationError(_("All entries must be approved before billing."))
            batch.state = "ready"

    def action_mark_invoiced(self):
        for batch in self:
            if batch.state != "ready":
                raise ValidationError(_("Batch must be ready for billing before marking invoiced."))
            batch.state = "invoiced"
