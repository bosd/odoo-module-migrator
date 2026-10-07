from odoo import _, models
from odoo.tools.translate import _lt

LOGIN_MESSAGE = "The login must be unique!"


class ResUsers(models.Model):
    _inherit = "res.users"

    _code_uniq = models.Constraint(
        'unique(login)',
        "Discount code must be unique !",
    )
    _lazy_check = models.Constraint(
        'CHECK(id > 0)',
        "Lazy translated message",
    )
    _login_uniq = models.Constraint(
        'unique(login)',
        LOGIN_MESSAGE,
    )


class ResUsersSettings(models.Model):
    _inherit = "res.users.settings"

    _sql_constraints = [
        ("bracket_check", "CHECK(name NOT LIKE '%]%')", "No brackets"),
    ]
