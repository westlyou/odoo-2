# -*- coding: utf-8 -*-
##############################################################################
#
#
#    Copyright (C) 2017 xiao (715294035@qq.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/lgpl.html>.
#
##############################################################################
from odoo import api, fields, models
from extend_addons.lty_dispatch_restful.core.restful_client import *
import mapping
import logging

#对接系统  车辆资源数据表名

CAR_TABLE = 'op_busresource'

_logger = logging.getLogger(__name__)
class Vehicle(models.Model):

    _inherit = 'scheduleplan.vehicleresource'

    '''
        继承车辆资源数据,调用restful api
    '''

    # #调度数据逐渐
    # fk_id = fields.Char()

    @api.model
    def create(self, vals):
        '''
            数据创建完成调用api
        :param vals:
        :return:
        '''

        res = super(Vehicle, self).create(vals)
        if not self._context.get('dryrun'):
            url = self.env['ir.config_parameter'].get_param('restful.url')
            cityCode = self.env['ir.config_parameter'].get_param('city.code')

            rp = True
            try:
                _logger.info('Start create data: %s', self._name)
                vals = mapping.dict_transfer(self._name, vals)
                vals.update({
                    'id': res.id,
                    'lineId': res.execplan_id.line_id.id,
                    'lineName': res.execplan_id.line_id.line_name,
                    'gprsId': res.execplan_id.line_id.gprs_id,
                    'onBoardId': res.vehicle_id.on_boardid,
                    'carNum': res.vehicle_id.inner_code,
                    'workDate': res.execplan_id.excutedate,
                })
                params = Params(type=1, cityCode=cityCode,tableName=CAR_TABLE, data=vals).to_dict()
                rp = Client().http_post(url, data=params)

            except Exception,e:
                _logger.info('%s', e.message)

            response_check(rp)
        return res

    @api.multi
    def write(self, vals):
        '''
            数据编辑时调用api
        :param vals:
        :return:
        '''

        res = super(Vehicle, self).write(vals)
        url = self.env['ir.config_parameter'].get_param('restful.url')
        cityCode = self.env['ir.config_parameter'].get_param('city.code')
        for r in self:
            seconds = datetime.datetime.utcnow() - datetime.datetime.strptime(r.create_date, "%Y-%m-%d %H:%M:%S")
            if seconds.seconds > 5 and (not self._context.get('dryrun')):
                rp = True
                try:
                    # url = 'http://10.1.50.83:8080/ltyop/syn/synData/'
                    _logger.info('Start write data: %s', self._name)
                    vals = mapping.dict_transfer(self._name, vals)
                    vals.update({
                        'id': r.id,
                        'lineId': r.execplan_id.line_id.id,
                        'lineName': r.execplan_id.line_id.line_name,
                        'gprsId': r.execplan_id.line_id.gprs_id,
                        'onBoardId': r.vehicle_id.on_boardid,
                        'carNum': r.vehicle_id.inner_code,
                        'workDate': r.execplan_id.excutedate,
                    })
                    params = Params(type=3, cityCode=cityCode,tableName=CAR_TABLE, data=vals).to_dict()
                    rp = Client().http_post(url, data=params)

                    # clientThread(url,params,res).start()
                except Exception,e:
                    _logger.info('%s', e.message)

                response_check(rp)
        return res

    @api.multi
    def unlink(self):
        '''
            数据删除时调用api
        :return:
        '''
        # fk_ids = self.mapped('fk_id')
        # vals = {"ids":fk_ids}
        # vals = {"ids": self.ids}

        url = self.env['ir.config_parameter'].get_param('restful.url')
        cityCode = self.env['ir.config_parameter'].get_param('city.code')
        for r in self:
            # url = 'http://10.1.50.83:8080/ltyop/syn/synData/'
            _logger.info('Start unlink data: %s', self._name)
            vals = {'id': r.id}
            params = Params(type = 2, cityCode = cityCode,tableName = CAR_TABLE, data = vals).to_dict()
            res = super(Vehicle, r).unlink()
            rp = Client().http_post(url, data=params)
            response_check(rp)
        return
