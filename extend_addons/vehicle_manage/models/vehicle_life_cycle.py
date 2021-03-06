# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import datetime

# 车辆生命周期
class vehicle_life(models.Model):

    # 表名(继承fleet.vehicle)
    _inherit = "fleet.vehicle"

    # 从'cost_type_set.cost_type_set'表中，获取inuse状态的数据，将其中'type_name'字段的值
    # 复制到'investment_cost'表中的'cost_type'字段
    @api.multi
    def _add_default_value(self):
        res = self.env['cost_type_set.cost_type_set'].search([('state', '=', 'inuse')])
        datas = []
        for i in res:
            data = {
                'is_required': i.is_required,
                'cost_type': i.type_name,
            }
            datas.append((0, 0, data))
        return datas

    # 投入期费用
    investment_ids = fields.One2many('investment_cost', 'vehicle_id', string='Investments', default=_add_default_value)

    # 状态（车辆生命周期）
    WORKFLOW_STATE_SELECTION = [
        ('invest_period', 'Invest period'),
        ('operation_period', 'Operation period'),
        ('scrap_period', 'Scrap period')
    ]

    # 生命周期状态
    vehicle_life_state = fields.Selection(WORKFLOW_STATE_SELECTION,
                                          default='invest_period',
                                          string='Vehicle life cycle state',
                                          readonly=True)

    # operation_date = fields.Datetime(string='operation date')
    # scrap_date = fields.Datetime(string='scrap date')

    @api.multi
    def action_operation(self):
        # 设置投入日期
        self.start_service_date = datetime.date.today()
        #修改车辆编码
        self.update_vehicle_code()

        # 费用金额必须大于零
        for item in self.investment_ids:

            if u'yes' == item.is_required:
                if (item.cost_amount <= 0):

                    raise exceptions.except_orm(_('Error'), ('%s %s' % ((item.cost_type) , _('The cost must be greater than zero'))))

        self.vehicle_life_state = 'operation_period'
        self.state = 'normal'
        # self.operation_date = datetime.date.today()
        return True

    def update_vehicle_code(self):
        """
            变更车辆编码
        :return:
        """
        vehicle_code = self.vehicle_code if self.vehicle_code else ""
        year = datetime.date.today().strftime('%Y')
        year = year[len(year)-2:]
        self.vehicle_code = vehicle_code + year

    @api.multi
    def action_scrap(self):
        self.vehicle_life_state = 'scrap_period'
        self.forced_destroy_date = datetime.date.today()
        return True

# 投入期费用
class investment_period_cost(models.Model):

    _name = 'investment_cost'

    _rec_name = 'cost_name'
    # 费用金额
    cost_amount = fields.Float('Cost amount', digits=(10, 2))
    # 费用名称
    cost_name = fields.Char('Cost name')
    # 发生时间
    occurrence_time = fields.Datetime('Occurrence time')
    # 费用类型
    cost_type = fields.Char('Cost type')
    # 是否必填
    is_required = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='yes', string='Is_required')
    # 总金额
    total_amount = fields.Float('Total amount', digits=(10, 2))

    # 状态
    WORKFLOW_STATE_SELECTION = [
        ('inuse', 'In-use'),
        ('archive', 'Archive')
    ]
    vehicle_id = fields.Many2one('fleet.vehicle', string='Investment id')
