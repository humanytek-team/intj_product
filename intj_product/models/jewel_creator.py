from odoo import _, api, fields, models


class JewelCreator(models.TransientModel):
    _name = "jewel_creator"
    _description = "jewel Creator"

    template_id = fields.Many2one(
        comodel_name="product.template",
        required=True,
    )
    gold_cost = fields.Float(
        compute="_compute_gold_cost",
    )
    attribute_caratage_id = fields.Many2one(
        comodel_name="product.attribute",
        compute="_compute_attribute_ids",
    )
    attribute_weight_id = fields.Many2one(
        comodel_name="product.attribute",
        compute="_compute_attribute_ids",
    )
    attribute_labor_id = fields.Many2one(
        comodel_name="product.attribute",
        compute="_compute_attribute_ids",
    )
    caratage_id = fields.Many2one(
        comodel_name="product.attribute.value",
        required=True,
    )
    caratage = fields.Float(
        compute="_compute_caratage",
    )
    weight_id = fields.Many2one(
        comodel_name="product.attribute.value",
        required=True,
    )
    weight = fields.Float(
        compute="_compute_weight",
    )
    labor_id = fields.Many2one(
        comodel_name="product.attribute.value",
        required=True,
    )
    labor = fields.Float(
        compute="_compute_labor",
    )
    waste = fields.Float(
        string="Waste (%)",
        required=True,
    )
    utility = fields.Float(
        string="Utility (%)",
        required=True,
    )

    cost = fields.Float(
        compute="_compute_cost",
        help="((Caratage / 24) * Gold cost * ((100 + Waste) / 100)) + Labor cost) * Weight",
    )
    price = fields.Float(
        compute="_compute_price",
        help="Cost * (100 + Utility / 100)",
    )

    product_id = fields.Many2one(
        comodel_name="product.product",
        compute="_compute_product_id",
    )

    @api.depends("caratage", "weight", "labor", "waste", "gold_cost")
    def _compute_cost(self):
        for record in self:
            record.cost = (
                (record.labor + record.gold_cost / 24 * record.caratage)
                * record.waste
                * record.weight
            )

    @api.depends("cost", "utility")
    def _compute_price(self):
        for record in self:
            record.price = record.cost * record.utility

    @api.depends("template_id", "caratage_id", "weight_id", "labor_id")
    def _compute_product_id(self):
        if not all([self.template_id, self.caratage_id, self.weight_id, self.labor_id]):
            self.product_id = None
            return
        self.product_id = self.template_id.get_product_if_exists(
            self.caratage_id, self.weight_id, self.labor_id
        )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.waste = self.product_id.jewel_waste
        self.utility = self.product_id.jewel_utility

    def create_jewel(self):
        ptav = self.template_id.get_product_template_attribute_value(
            self.caratage_id, self.weight_id, self.labor_id
        )
        ptav.ensure_one()

        combination = self.template_id._get_closest_possible_combination(ptav)

        product = self.template_id._create_product_variant(  # This creates or gets the product variant
            combination
        )

        product.jewel_waste = self.waste
        product.jewel_utility = self.utility
        product.caratage_id = self.caratage_id
        product.weight_id = self.weight_id
        product.labor_id = self.labor_id
        product.gold_cost = self.gold_cost

        return {
            "name": _("Created Jewel"),
            "view_mode": "form",
            "res_model": "product.product",
            "res_id": product.id,
            "type": "ir.actions.act_window",
            "target": "current",
        }

    @api.onchange("template_id")
    def _compute_attribute_ids(self):
        self.attribute_caratage_id = self.env.ref("intj_product.attribute_caratage")
        self.attribute_weight_id = self.env.ref("intj_product.attribute_weight")
        self.attribute_labor_id = self.env.ref("intj_product.attribute_labor")

    @api.depends("template_id")
    def _compute_gold_cost(self):
        self.gold_cost = self.env.ref("intj_product.product_gold").standard_price

    @api.depends("caratage_id")
    def _compute_caratage(self):
        self.caratage = self.value_to_float(self.caratage_id)

    @api.depends("weight_id")
    def _compute_weight(self):
        self.weight = self.value_to_float(self.weight_id)

    @api.depends("labor_id")
    def _compute_labor(self):
        self.labor = self.value_to_float(self.labor_id)

    def value_to_float(self, value):
        if not value:
            return 0.0
        return float("".join([c for c in value.name if c.isdigit() or c == "."]))
