from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_config_attr(self):
        config_attribute = self.env.ref("intj_product.attribute_config")
        for line in self.attribute_line_ids:
            if line.attribute_id == config_attribute:
                return line
        return None

    def get_product_template_attribute_value(self, caratage_id, weight_id, labor_id):
        config_attr = self._get_config_attr()
        name = self._name_config_value(caratage_id, weight_id, labor_id)
        if config_attr:
            config_value = self._get_config_attr_value(config_attr, name)
            if config_value:
                return config_value  # Current value already exists
            self._create_config_value(config_attr, name)
            return self._get_config_attr_value(config_attr, name)
        self._create_config_attr_and_value(name)
        config_attr = self._get_config_attr()
        config_value = self._get_config_attr_value(config_attr, name)
        return config_value

    def _create_config_attr_and_value(self, name):
        config_attribute = self.env.ref("intj_product.attribute_config")
        config_value_dict = self._create_config_value_dict(name)
        self.attribute_line_ids.create(
            {
                "attribute_id": config_attribute.id,
                "product_tmpl_id": self.id,
                "value_ids": [
                    (
                        0,
                        False,
                        config_value_dict,
                    )
                ],
            }
        )

    def _name_config_value(self, caratage_id, weight_id, labor_id):
        return f"{caratage_id.name} {weight_id.name} {labor_id.name}"

    def _get_config_attr_value(self, line, name):
        for value in line.product_template_value_ids:
            if value.name == name:
                return value
        return None

    def _create_config_value(self, line, name):
        config_value_dict = self._create_config_value_dict(name)
        line.write(
            {
                "value_ids": [
                    (
                        0,
                        False,
                        config_value_dict,
                    )
                ],
            }
        )

    def _create_config_value_dict(self, name):
        return {
            "attribute_id": self.env.ref("intj_product.attribute_config").id,
            "name": name,
        }

    def get_product_if_exists(self, caratage_id, weight_id, labor_id):
        config_attr = self._get_config_attr()
        if not config_attr:
            return None
        name = self._name_config_value(caratage_id, weight_id, labor_id)
        config_value = self._get_config_attr_value(config_attr, name)
        if not config_value:
            return None
        return self.product_variant_ids.filtered(
            lambda p: p.product_template_attribute_value_ids == config_value
        )
