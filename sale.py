# This file is part of the sale_weight module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['Sale']
__metaclass__ = PoolMeta


class Sale:
    __name__ = 'sale.sale'
    weight_uom = fields.Many2One('product.uom', 'Weight Uom',
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
            depends=['weight_digits']), 'get_weight')

    @classmethod
    def __setup__(cls):
        super(Sale, cls).__setup__()

        for fname in ('weight',):
            if fname not in cls.lines.on_change:
                cls.lines.on_change.add(fname)
        for fname in cls.lines.on_change:
            if hasattr(cls, 'carrier') and fname not in cls.carrier.on_change:
                cls.carrier.on_change.add(fname)

    def get_weight(self, name=None):
        return self.sum_weights()

    def sum_weights(self):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        Uom = pool.get('product.uom')

        to_uom = self.weight_uom and self.weight_uom \
                or Uom(ModelData.get_id('product', 'uom_kilogram'))
        weight = 0.0
        for line in self.lines:
            if line.product and line.product.weight:
                from_uom = line.product.weight_uom
                weight += Uom.compute_qty(from_uom, line.product.weight * line.quantity,
                        to_uom, round=False)
        return Uom.compute_qty(from_uom, weight, from_uom, round=True)

    @fields.depends('weight_uom')
    def on_change_with_weight_digits(self, name=None):
        if self.weight_uom:
            return self.weight_uom.digits
        return 2

    @fields.depends('carrier', 'party', 'currency', 'sale_date', 'lines',
        'weight')
    def on_change_weight(self):
        return self.on_change_lines()

    def _get_carrier_context(self):
        Uom = Pool().get('product.uom')

        context = super(Sale, self)._get_carrier_context()

        if self.carrier.carrier_cost_method != 'weight':
            return context

        context = context.copy()
        if self.weight:
            context['weights'] = [self.weight]
        return context

    def create_shipment(self, shipment_type):
        '''Copy weight value from sale to shipment out'''
        shipments = super(Sale, self).create_shipment(shipment_type)
        if shipments:
            for shipment in shipments:
                if self.weight:
                    shipment.weight = self.weight
                    shipment.save()
        return shipments

