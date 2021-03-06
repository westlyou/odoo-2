# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class FleetVehicle(models.Model):
    """
     车辆
    """
    _inherit = 'fleet.vehicle'

    repair_ids = fields.One2many("maintain.manage.repair", 'vehicle_id', string='Repairs',
                                                            domain = [('state', 'in', ['completed'])])
    repair_count = fields.Integer(compute="_compute_repair_count", string='Repairs')

    def _compute_repair_count(self):
        for record in self:
            record.repair_count = self.env['maintain.manage.repair'].search_count([('vehicle_id', '=', record.id),
                                                                            ('state', 'in', ['completed'])])

    @api.multi
    def action_to_open(self):
        """
        报修单:
            功能：跳转到车辆的维修单
        """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('vehicle_maintain', xml_id)
            res.update(
                context=dict(self.env.context, default_vehicle_id=self.id),
                domain=[('vehicle_id', '=', self.id), ('state', 'in', ['completed'])]
            )
            return res
        return False