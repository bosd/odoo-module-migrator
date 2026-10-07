from odoo import _, models
from odoo.tools.translate import _lt

LOGIN_MESSAGE = "The login must be unique!"


class ResUsers(models.Model):
    _inherit = "res.users"

    _sql_constraints = [
        ("code_uniq", "unique(login)", _("Discount code must be unique !")),
        ("lazy_check", "CHECK(id > 0)", _lt("Lazy translated message")),
        ("login_uniq", "unique(login)", LOGIN_MESSAGE),
    ]


class ResUsersSettings(models.Model):
    _inherit = "res.users.settings"

    _sql_constraints = [
        ("bracket_check", "CHECK(name NOT LIKE '%]%')", "No brackets"),
    ]
