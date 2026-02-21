from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    rule = env.ref("time_tracking_module.rule_time_entry_owner", raise_if_not_found=False)
    if rule:
        rule.sudo().write({
            "domain_force": "[('employee_id.user_id', '=', user.id)]",
        })
    else:
        group = env.ref("time_tracking_module.group_time_tracker", raise_if_not_found=False)
        model = env.ref("time_tracking_module.model_x_time_entry", raise_if_not_found=False)
        if model and group:
            env['ir.rule'].sudo().create({
                'name': 'Time entries: own employee',
                'model_id': model.id,
                'domain_force': "[('employee_id.user_id', '=', user.id)]",
                'groups': [(4, group.id)],
            })
