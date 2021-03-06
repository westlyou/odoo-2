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

#对接系统  调度参数基础数据表名

PARAM_TABLE = 'op_param'

_logger = logging.getLogger(__name__)

class Dispatch(models.TransientModel):
    _inherit = 'dispatch.config.settings'

    @api.multi
    def execute(self):
        super(Dispatch, self).execute()
        url = self.env['ir.config_parameter'].get_param('restful.url')
        cityCode = self.env['ir.config_parameter'].get_param('city.code')
        vals = self.read()[0]
        vals = mapping.dict_transfer(self._name, vals)
        vals.update({'id': 1})
        params = Params(type=3, cityCode=cityCode, tableName=PARAM_TABLE, data=vals).to_dict()
        rp = Client().http_post(url, data=params)
        response_check(rp)
        res = self.env['ir.actions.act_window'].for_xml_id('lty_dispatch_config', 'action_dispatch_config_settings')
        return res

class general(models.TransientModel):
    _inherit = 'general.config.settings'

    @api.multi
    def execute(self):
        super(general, self).execute()
        url = self.env['ir.config_parameter'].get_param('restful.url')
        cityCode = self.env['ir.config_parameter'].get_param('city.code')
        vals = self.read()[0]
        vals = mapping.dict_transfer(self._name, vals)
        vals.update({'id': 1})
        params = Params(type=3, cityCode=cityCode, tableName=PARAM_TABLE, data=vals).to_dict()
        rp = Client().http_post(url, data=params)
        response_check(rp)
        res = self.env['ir.actions.act_window'].for_xml_id('lty_dispatch_config', 'action_general_config_settings')
        return res

# class Company(models.Model):
#
#     _inherit = 'res.company'
#
#     '''
#         继承公司，获取调度参数及通用设置,调用restful api
#     '''
#     @api.multi
#     def write(self, vals):
#         '''
#             数据编辑时调用api
#         :param vals:
#         :return:
#         '''
#         url = self.env['ir.config_parameter'].get_param('restful.url')
#         cityCode = self.env['ir.config_parameter'].get_param('city.code')
#         # for r in self:
#         #     try:
#         #         _logger.info('Start write data: %s', self._name)
#         #         vals = mapping.dict_transfer(self._name, vals)
#         #         if vals:
#         #             vals.update({'id': r.id})
#         #             params = Params(type=3, cityCode=cityCode,tableName=PARAM_TABLE, data=vals).to_dict()
#         #             rp = Client().http_post(url, data=params)
#         #     except Exception,e:
#         #         _logger.info('%s', e.message)
#         res = super(Company, self).write(vals)
#         return res