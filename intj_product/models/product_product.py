from odoo import _, api, fields, models


class Product(models.Model):
    _inherit = ["product.product", "mail.thread"]
    _name = "product.product"

    jewel_waste = fields.Float(
        string="Waste (%)",
    )
    jewel_utility = fields.Float(
        string="Utility (%)",
    )
    caratage_id = fields.Many2one(
        comodel_name="product.attribute.value",
    )
    weight_id = fields.Many2one(
        comodel_name="product.attribute.value",
    )
    labor_id = fields.Many2one(
        comodel_name="product.attribute.value",
    )
    standard_price = fields.Float(
        compute="_compute_cost_jewel",
        store=True,
        readonly=False,
        help="((Caratage / 24) * Gold cost * ((100 + Waste) / 100)) + Labor cost) * Weight",
    )
    gold_cost = fields.Float(
        readonly=True,
    )
    actual_gold_cost = fields.Float(
        compute="_compute_actual_gold_cost",
    )
    jewel_cost = fields.Float(
        compute="_compute_jewel_cost_price",
        store=True,
        readonly=False,
    )

    def _compute_actual_gold_cost(self):
        self.actual_gold_cost = self.env.ref("intj_product.product_gold").standard_price

    @api.depends(
        "caratage_id",
        "weight_id",
        "labor_id",
        "jewel_waste",
        "jewel_utility",
        "gold_cost",
    )
    def _compute_jewel_cost_price(self):
        for record in self:
            if not all([record.caratage_id, record.weight_id, record.labor_id]):
                continue
            caratage = self.env["jewel_creator"].value_to_float(self.caratage_id)
            weight = self.env["jewel_creator"].value_to_float(self.weight_id)
            labor = self.env["jewel_creator"].value_to_float(self.labor_id)
            record.jewel_cost = (
                (caratage / 24) * record.gold_cost * ((100 + record.jewel_waste) / 100)
                + labor
            ) * weight
            record.standard_price = record.jewel_cost

            price = record.jewel_cost * ((100 + record.jewel_utility) / 100)
            ptav = record.product_tmpl_id.get_product_template_attribute_value(
                self.caratage_id, self.weight_id, self.labor_id
            )
            ptav.price_extra = price - record.list_price

            # Leave a message in the chatter

    def write(self, vals):
        if {
            "jewel_waste",
            "jewel_utility",
            "gold_cost",
        }.intersection(vals.keys()):
            body = _("Price changed, waste %s, utility %s, gold cost %s") % (
                vals.get("jewel_waste", self.jewel_waste),
                vals.get("jewel_utility", self.jewel_utility),
                vals.get("gold_cost", self.gold_cost),
            )
            self.message_post(body=body)
        res = super().write(vals)
        return res

    def update_gold_cost(self):
        self.gold_cost = self.actual_gold_cost
