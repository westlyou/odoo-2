# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.sql import drop_view_if_exists

class map_line_station_info(models.Model):
    _name = 'map_line_station_info'
    _auto = False
    _order = 'squence asc'
    route_id = fields.Many2one('route_manage.route_manage')
    station_id = fields.Many2one('operation_resources_station')
    station_type = fields.Char()
    squence = fields.Integer()
    latitude = fields.Float()
    longitude = fields.Float()
    state = fields.Char()
    derection = fields.Char()

    @api.model_cr
    def init(self):
        drop_view_if_exists(self._cr, 'map_line_station_info')
        self._cr.execute("""
            CREATE OR REPLACE VIEW map_line_station_info AS (

				select 
				   opertation_resources_station_platform.id  as id,
				   opertation_resources_station_platform.route_id,
				   opertation_resources_station_platform.station_id,
				   opertation_resources_station_platform.station_type,
				   opertation_resources_station_platform.sequence as squence,
				   opertation_resources_station.latitude,
				   opertation_resources_station.longitude,
				   opertation_resources_station.state,
				   opertation_resources_station.name as station_name,
				   opertation_resources_station_platform.direction as direction
				from   
				opertation_resources_station_platform
				left join opertation_resources_station on opertation_resources_station_platform.station_id = opertation_resources_station.id

				where 
				opertation_resources_station.state = 'inuse'
				
            )""")        
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
