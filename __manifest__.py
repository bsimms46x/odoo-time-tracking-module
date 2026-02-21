{
    "name": "Time Tracking Plus",
    "version": "1.0",
    "summary": "Advanced time entry, approval, billing, and reporting for Odoo 18",
    "description": """
        Modular time tracking solution with timers, approvals, budgeting, and exports.
        Extends Projects, HR, Accounting, and Timesheets for precise billing and payroll alignment.
    """,
    "category": "Human Resources",
    "author": "OpenClaw Team",
    "depends": [
        "base",
        "hr",
        "project",
        "hr_timesheet",
        "account",
        "analytic",
        "hr_attendance"
    ],
    "data": [
        "views/time_menu_views.xml",
        "security/time_tracking_security.xml",
        "security/ir.model.access.csv",
        "views/time_entry_views.xml",
        "views/time_template_views.xml",
        "views/time_batch_views.xml",
        "views/time_rule_views.xml",
        "views/quick_entry_views.xml",
        "data/time_tracking_data.xml",
    ],
    "demo": [
        "demo/time_tracking_demo.xml"
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "post_init_hook": "post_init_hook",
    "auto_install": False
}
