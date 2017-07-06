# This file is part of the sale_weight module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Id

__all__ = ['Sale']


class Sale:
    __metaclass__ = PoolMeta
    __name__ = 'sale.sale'
    weight_uom = fields.Many2One('product.uom', 'Weight Uom',
        domain=[('category', '=', Id('product', 'uom_cat_weight'))],
        states={
            'readonly': Eval('state') != 'draft',
        }, depends=['state'])
    weight_digits = fields.Function(fields.Integer('Weight Digits'),
        'on_change_with_weight_digits')
    weight = fields.Float('Weight', digits=(16, Eval('weight_digits', 2)),
            states={
                'readonly': Eval('state') != 'draft',
            }, depends=['state', 'weight_digits'])
    weight_lines = fields.Function(fields.Float('Weight of Lines',
            digits=(16, Eval('weight_digits', 2)),
            depends=['weight_digits']), 'get_weight_lines')

    @classmethod
    def __setup__(cls):
        super(Sale, cls).__setup__()

        for fname in ('weight',):
            if fname not in cls.lines.on_change:
                cls.lines.on_change.add(fname)
        for fname in cls.lines.on_change:
            if hasattr(cls, 'carrier') and fname not in cls.carrier.on_change:
                cls.carrier.on_change.add(fname)

    @classmethod
    def get_weight_lines(cls, sales, names):
        pool = Pool()
        Config = pool.get('stock.configuration')
        Uom = pool.get('product.uom')

        config = Config(1)
        if config.weight_uom:
            default_uom = config.weight_uom
        else:
            default_uom, = Uom.search([('symbol', '=', 'g')], limit=1)

        weight = {}
        for sale in sales:
            weight[sale.id] = 0.0
            to_uom = sale.weight_uom or default_uom
            for line in sale.lines:
                if line.quantity and line.product and line.product.weight:
                    from_uom = line.product.weight_uom
                    weight[sale.id] += Uom.compute_qty(from_uom,
                        line.product.weight * line.quantity, to_uom,
                        round=False)
        return {'weight_lines': weight}

    @fields.depends('weight_uom')
    def on_change_with_weight_digits(self, name=None):
        if self.weight_uom:
            return self.weight_uom.digits
        return 2

    @fields.depends('carrier', 'party', 'currency', 'sale_date', 'lines',
        'weight')
    def on_change_weight(self):
        self.on_change_lines()

    def _get_carrier_context(self):
        context = super(Sale, self)._get_carrier_context()

        if self.carrier.carrier_cost_method != 'weight':
            return context

        context = context.copy()
        if self.weight:
            context['weights'] = [self.weight]
        return context

    def create_shipment(self, shipment_type):
        shipments = super(Sale, self).create_shipment(shipment_type)
        if not shipments:
            return

        for shipment in shipments:
            if self.weight or self.weight_uom:
                shipment.weight = self.weight
                shipment.weight_uom = self.weight_uom
                shipment.save()
        return shipments

    def create_invoice(self):
        invoice = super(Sale, self).create_invoice()
        if not invoice:
            return

        if self.weight or self.weight_uom:
            invoice.weight_uom = self.weight_uom
            invoice.weight = self.weight
            invoice.save()

        return invoice
