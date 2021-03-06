# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime
from datetime import timedelta
import pytz
import copy

import logging
_logger = logging.getLogger(__name__)


class BusGroup(models.Model):
    """
    班组管理
    """
    _name = 'bus_group'
    _order = "id desc"

    _sql_constraints = [
        ('record_unique', 'unique(route_id,name)', _('The route and name must be unique!'))
    ]

    name = fields.Char('Group Name', required=True)
    route_id = fields.Many2one('route_manage.route_manage', required=True)
    # is_conductor = fields.Boolean(default=True)

    vehicle_ct = fields.Integer(compute='get_vehicle_ct')
    driver_ct = fields.Integer(compute='get_driver_ct')
    conductor_ct = fields.Integer(compute='get_conductor_ct')

    vehicle_ids = fields.One2many('bus_group_vehicle', 'bus_group_id')
    driver_ids = fields.One2many('bus_group_driver', 'bus_group_id')
    conductor_ids = fields.One2many('bus_group_conductor', 'bus_group_id')

    bus_algorithm_id = fields.Many2one('bus_algorithm', required=True)
    is_algorithm_change = fields.Boolean(default=False)
    bus_algorithm_date = fields.Date(default=fields.Date.context_today)
    bus_driver_algorithm_id = fields.Many2one('bus_driver_algorithm', required=True)
    bus_driver_algorithm_date = fields.Date(default=fields.Date.context_today)
    is_driver_algorithm_change = fields.Boolean(default=False)

    bus_shift_id = fields.Many2one('bus_shift', required=True)

    driver_vehicle_shift_ids = fields.One2many('bus_group_driver_vehicle_shift', 'group_id',
                                               domain=[('active', '=', True)])

    is_not_match = fields.Boolean(default=False, compute='check_vehicle_is_match')
    not_match_reason = fields.Text(compute='check_vehicle_is_match')

    state = fields.Selection([
        ('draft', 'draft'),
        ('wait_check', "wait_check"),
        ('use', "use"),], string='Bus Group State', default='draft', readonly=True)

    direction = fields.Selection([('0', u'上行'), ('1', u'下行')], string='direction')  # required=True)
    # 是否机动
    is_flexible = fields.Boolean(default=False)
    
    

    # @api.multi
    # def action_test1(self):
    #     staff_date = datetime.date.today() + timedelta(days=1)
    #     operation_ct = 3
    #
    #     self.env['bus_staff_group'].action_gen_staff_group(self.route_id, staff_date=staff_date, operation_ct=operation_ct)


    @api.multi
    def action_tomorrow(self):
        """
        生成明天的人车配班
        """
        self.env['bus_group_driver_vehicle_shift'].scheduler_vehicle_shift(self.route_id.id)

    @api.multi
    def write(self, vals):
        """
        司乘轮班算法，车辆轮趟算法，班制 如果发生修改，修改状态为待审核，和记录是否发生改变
        :param vals:
        :return:
        """
        change_list = ['bus_algorithm_id',
                       'bus_driver_algorithm_id',
                       'bus_shift_id',
                       'vehicle_ids',
                       'driver_ids',
                       'conductor_ids',
                       ]

        def is_change(vals):
            for i in change_list:
                if i in vals:
                    return True
            return False
        if is_change(vals):
            vals.update({'state': 'wait_check'})
        if "bus_algorithm_id" in vals:
            vals.update({'is_algorithm_change': True})
        if "bus_driver_algorithm_id" in vals:
            vals.update({'is_driver_algorithm_change': True})
        return super(BusGroup, self).write(vals)

    @api.multi
    def action_submit(self):
        """
        提交审核
        """
        self.write({
            'state': 'wait_check'
        })

    @api.multi
    def action_check_success(self):
        """
        审核通过 修改轮班算法的修改时间
        """
        vals = {'state': 'use'}
        if self.is_algorithm_change:
            vals.update({'bus_algorithm_date':datetime.date.today(), 'is_algorithm_change': False})
        if self.is_driver_algorithm_change:
            vals.update({'bus_driver_algorithm_date': datetime.date.today(), 'is_driver_algorithm_change': False})
        self.write(vals)

    @api.multi
    def action_check_fail(self):
        """
        审核不通过
        """
        vals = {'state': 'draft'}
        self.write(vals)

    @api.depends('vehicle_ids', 'driver_ids', 'bus_shift_id')
    def check_vehicle_is_match(self):
        """
        计算车辆数，司机数和班制的关系
        如果车辆乘以版次数大于司机数 产生警告，并且不能够初始化人车配班
        :return:
        """
        for i in self:
            if not i.is_flexible:
                vehicle_ct = len(i.vehicle_ids)
                driver_ct = len(i.driver_ids)
                if i.bus_shift_id:
                    shift_ct = len(i.bus_shift_id.shift_line_ids)
                    if shift_ct == 0:
                        i.is_not_match = True
                        i.not_match_reason = u'所选班制的班次不存在，请选择正确的班制'
                        if self.state != 'draft':
                            self.write({'state': 'draft'})                       
                    if vehicle_ct and shift_ct and driver_ct:
                        if vehicle_ct * shift_ct > driver_ct:
                            i.is_not_match = True
                            i.not_match_reason = u'所选的班制，车辆数，司机数配置不合理，建议重新选择'
                            if self.state != 'draft':
                                self.write({'state': 'draft'})                       
                if i.driver_vehicle_shift_ids:
                    for line in  i.driver_vehicle_shift_ids :
                        if (line.vehicle_sequence > 0)  and (len(line.driver_id) == 0):
                            i.is_not_match = True
                            i.not_match_reason = u'运营车辆或班组为空，请检查！'
                            if self.state != 'draft':
                                self.write({'state': 'draft'})                       
                        if (line.vehicle_sequence > 0) and (len(line.bus_group_vehicle_id) == 0) :
                            i.is_not_match = True
                            i.not_match_reason = u'运营车辆或班组为空，请检查！'
                            if self.state != 'draft':
                                self.write({'state': 'draft'})                       
                        

    @api.depends('vehicle_ids')
    def get_vehicle_ct(self):
        for i in self:
            i.vehicle_ct = len(i.vehicle_ids)

    @api.depends('driver_ids')
    def get_driver_ct(self):
        for i in self:
            i.driver_ct = len(i.driver_ids)

    @api.depends('conductor_ids')
    def get_conductor_ct(self):
        for i in self:
            i.conductor_ct = len(i.conductor_ids)

    @api.onchange('route_id')
    def _get_route_id_onchange(self):
        """
        创建班组时 选择线路，自动带出线路下面的车辆，司机，售票员
        :return:
        """
        for i in self:
            datas = []
            count = 0
            res = self.env['bus_group'].search([('route_id', '=', i.route_id.id)])
            vehicle_lists = []
            driver_lists = []
            conductor_lists = []

            for k in res:
                if k.name == self.name:
                    continue
                vehicle_lists = vehicle_lists + k.vehicle_ids.mapped('vehicle_id').ids
                driver_lists = driver_lists + k.driver_ids.mapped('driver_id').ids
                conductor_lists += k.conductor_ids.mapped('conductor_id').ids
            vehicle_sequence = 1
            for j in i.route_id.vehicle_res.ids:  #更新车辆
                if j in vehicle_lists:
                    continue
                vals = {
                    # 'sequence': count+len(lists),
                    "route_id": i.route_id.id,
                    'vehicle_id': j,
                    'sequence': vehicle_sequence,
                }
                datas.append((0, 0, vals))
                vehicle_sequence = vehicle_sequence +1
            i.vehicle_ids = datas

            datas = []
            drive_sequence = 1
            for j in i.route_id.human_resource.filtered(lambda field: field.workpost.posttype == "driver").ids: #更新司机
                if j in driver_lists:
                    continue
                vals = {
                    "route_id": i.route_id.id,
                    'driver_id': j,
                    'sequence': drive_sequence,
                }
                datas.append((0, 0, vals))
                drive_sequence = drive_sequence +1
            i.driver_ids = datas

            datas = []
            conductor_sequence = 1
            for j in i.route_id.human_resource.filtered(lambda field: field.workpost.posttype == "conductor").ids: #更新乘务员
                if j in conductor_lists:
                    continue
                vals = {
                    "route_id": i.route_id.id,
                    'conductor_id': j,
                    'sequence': conductor_sequence,
                }
                datas.append((0, 0, vals))
                conductor_sequence = conductor_sequence +1
            i.conductor_ids = datas


class BusGroupVehicle(models.Model):
    """
    班组车辆
    """
    _name = 'bus_group_vehicle'
    _rec_name = 'vehicle_id'
    _order = "sequence"

    _sql_constraints = [
        ('record_unique', 'unique(route_id,vehicle_id)', _('The route and vehicle must be unique!')),
    ]

    bus_group_id = fields.Many2one('bus_group', ondelete='cascade')
    route_id = fields.Many2one('route_manage.route_manage')
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle No", help='Vehicle No', required=True,
                                 domain="[('route_id','=',route_id)]")
    vehicle_type = fields.Many2one("fleet.vehicle.model", related='vehicle_id.model_id',
                                   readonly=True, copy=False, string="Vehicle Model")
    ride_number = fields.Integer('Ride Number', related='vehicle_id.ride_number', readonly=True)
    state = fields.Selection(related='vehicle_id.state', readonly=True, string="Vehicle State")
    #台次
    sequence = fields.Integer()
    
#     _sql_constraints = [
#         ('bus_group_id_sequence_unique', 'unique(bus_group_id,sequence)', (u'车辆序号不可重复！'))
#     ]    


class BusGroupDriver(models.Model):
    """
    班组司机
    """
    _name = 'bus_group_driver'
    _rec_name = 'driver_id'
    _order = "sequence"

    _sql_constraints = [
        ('record_unique', 'unique(route_id,driver_id)', _('The route and driver must be unique!')),
    ]

    route_id = fields.Many2one('route_manage.route_manage')
    bus_group_id = fields.Many2one('bus_group', ondelete='cascade')

    driver_id = fields.Many2one('hr.employee', string="driver", required=True,
                                domain="[('workpost.posttype', '=', 'driver'), ('lines', '=', route_id)]")
    jobnumber = fields.Char(string='employee work number', related='driver_id.jobnumber', readonly=True)
    #台次
    sequence = fields.Integer()
    
#     _sql_constraints = [
#         ('bus_group_id_sequence_unique', 'unique(bus_group_id,sequence)', (u'司机序号不可重复！'))
#     ]    

class BusGroupConductor(models.Model):
    """
    班组乘务员
    """
    _name = 'bus_group_conductor'
    _rec_name = 'conductor_id'
    _order = "sequence"

    _sql_constraints = [
        ('record_unique', 'unique(route_id,conductor_id)', _('The route and conductor must be unique!')),
    ]

    bus_group_id = fields.Many2one('bus_group', ondelete='cascade')
    route_id = fields.Many2one('route_manage.route_manage')
    conductor_id = fields.Many2one('hr.employee', string="conductor", required=True,
                                   domain="[('workpost.posttype', '=', 'conductor'), ('lines', '=', route_id)]")
    jobnumber = fields.Char(string='employee work number', related='conductor_id.jobnumber', readonly=True)
    #台次
    sequence = fields.Integer()
    
#     _sql_constraints = [
#         ('bus_group_id_sequence_unique', 'unique(bus_group_id,sequence)', (u'乘务员序号不可重复！'))
#     ]    
#     


class BusGroupDriverVehicleShift(models.Model):
    _name = 'bus_group_driver_vehicle_shift'

    use_date = fields.Date(default=fields.Date.context_today, readonly=True)
    sequence = fields.Integer("Vehicle Shift Sequence", default=1, readonly=True)

    group_id = fields.Many2one('bus_group', ondelete='cascade', readonly=True)
    route_id = fields.Many2one('route_manage.route_manage', related='group_id.route_id')

    driver_id = fields.Many2one("bus_group_driver")
    driver_jobnumber = fields.Char(string='driver_jobnumber', related='driver_id.jobnumber', readonly=True)

    conductor_id = fields.Many2one("bus_group_conductor")
    conductor_jobnumber = fields.Char(string='conductor_jobnumber', related='conductor_id.jobnumber', readonly=True)

    bus_shift_id = fields.Many2one('bus_shift', readonly=True)
    bus_shift_choose_line_id = fields.Many2one('bus_shift_choose_line')
    choose_sequence = fields.Integer('Shift Sequence', related='bus_shift_choose_line_id.sequence')

    bus_group_vehicle_id = fields.Many2one("bus_group_vehicle")
    vehicle_sequence = fields.Integer("Vehicle Sequence", readonly=True)
    active = fields.Boolean(default=True)

    @api.model
    def scheduler_vehicle_shift(self, route_id=None, use_date=use_date):
        """
        1，查询出所有的线路
        2，查询出线路对应的所有班组及线路是否需要大轮换
        3，查询出班组的车辆轮趟算法 司乘轮班算法
        4，查询人车配班前一天的所有数据
        5，根据前面2，3，4的条件生成今天的人车配班数据
        :return:
        """
        domain = [('state', '=', 'use')]

        if route_id:
            domain += [('route_id', '=', route_id)]

        next_use_date = datetime.datetime.strptime(use_date, "%Y-%m-%d") + timedelta(days=1)

        _logger.info(u"班组管理人车配班同步时间:%s" % (str(next_use_date)))

        res = self.env['bus_group_driver_vehicle_shift'].search(['|',('use_date', '<', str(datetime.date.today()-timedelta(days=2)))
                                                                 ,('driver_id','=',False)])

        if res:
            res.write({'active': False})

        routes = self.env['bus_group'].read_group(domain, ['route_id'], groupby=['route_id'])

        for i in routes:
            res_groups = self.env['bus_group'].search(i['__domain']) #线路下面所有的组
            if not res_groups:
                continue
            is_big_rotation = res_groups[0].route_id.is_big_rotation
            rotation_cycle = res_groups[0].route_id.rotation_cycle
            last_rotation_date = res_groups[0].route_id.last_rotation_date

            route_id = res_groups[0].route_id.id

            res_seq = self.env['bus_group_driver_vehicle_shift'].search(
                                                                [('use_date', '=', use_date),
                                                                 ('route_id', '=', route_id),
                                                                 ('vehicle_sequence', '!=', 0)]).mapped('vehicle_sequence')
            old_t_sequence_list = list(set(res_seq))  #线路内原始顺序
            new_t_sequence_list = sorted(old_t_sequence_list, reverse=True) #线路内逆顺序

            old_group_dict = {}
            new_group_dict = {}
            for j in res_groups:
                group_seq = self.env['bus_group_driver_vehicle_shift'].search([('use_date', '=', use_date),
                                                                            ('route_id', '=', route_id),
                                                                            ('vehicle_sequence', '!=', 0),
                                                                            ('group_id', '=', j.id),]).mapped('vehicle_sequence')

                old_group_dict[j.id] = list(set(group_seq))
                new_group_dict[j.id] = []
            _logger.info(u"同步时间:%s,线路id:%s 所有的组 原始顺序%s"%(str(next_use_date), route_id, old_t_sequence_list))
            _logger.info(u"同步时间:%s,线路id:%s 所有的组 逆序%s" % (str(next_use_date), route_id, new_t_sequence_list))
            _logger.info(u"同步时间:%s,线路id:%s 车辆分组顺序%s" % (str(next_use_date), route_id, old_group_dict))
            _logger.info(u"同步时间:%s,线路id:%s 车辆分组新顺序%s" % (str(next_use_date), route_id, new_group_dict))

            """
            大轮换 start
            """
            if last_rotation_date:
                last_rotation_date = datetime.datetime.strptime(last_rotation_date, "%Y-%m-%d")
            else:
                last_rotation_date = datetime.date.today()


            group_dict = {}
            if is_big_rotation :
                # 满足大轮换 或者 最后一次大轮换时间大于等于指定时间
                if (next_use_date - last_rotation_date).days >= rotation_cycle or str(last_rotation_date) >= use_date:
                    for k, v in old_group_dict.iteritems():
                        tmp = []
                        for m in v:
                            tmp.append(new_t_sequence_list[old_t_sequence_list.index(m)])
                        new_group_dict[k] = tmp
                    group_dict = new_group_dict
                    if str(last_rotation_date) < use_date:
                        res_groups[0].route_id.last_rotation_date = use_date
                    _logger.info(u"同步时间:%s,线路id:%s 线路下所有的组 大轮换后 新顺序%s" % (str(next_use_date), route_id, group_dict))
                else:
                    group_dict = copy.deepcopy(old_group_dict)
                    _logger.info(u"同步时间:%s,线路id:%s 线路下所有的组 大论换 周期没到" % (str(next_use_date), route_id,))
            else:
                group_dict = copy.deepcopy(old_group_dict)
                _logger.info(u"同步时间:%s,线路id:%s 线路下所有的组 没有进行大论换" % (str(next_use_date), route_id, ))

            '''车辆轮趟算法'''
            new_group_dict_vehicle = {}
            for k, v in group_dict.iteritems():
                bus_group_res = self.env['bus_group'].search([('id', '=', k)])
                cycle = bus_group_res[0].bus_algorithm_id.cycle
                direction = bus_group_res[0].bus_algorithm_id.direction
                last_bus_algorithm_date = datetime.datetime.strptime(bus_group_res[0].bus_algorithm_date, "%Y-%m-%d")
                if cycle > 0:
                    # 满足车辆轮趟 或者 最后一次车辆轮趟时间大于等于指定时间
                    if (next_use_date - last_bus_algorithm_date).days >= cycle or str(last_bus_algorithm_date) >= use_date:
                        def leftMove2(list, step):
                            l = list[:step]
                            for m in range(step, len(list)):
                                list[m - step] = list[m]
                            list[len(list) - step:] = l
                            return list

                        if direction == 'positive' and v:  # negative
                            b = v.pop()
                            v.insert(0, b)
                        else:                     #向后移
                            v = leftMove2(v, 1)
                        if str(last_bus_algorithm_date) < use_date:
                            bus_group_res.write({'bus_algorithm_date': use_date})
                new_group_dict_vehicle[k] = v
            _logger.info(u"同步时间:%s,线路id:%s 线路下所有的组 车辆顺序 车辆轮趟算法 新顺序%s" % (str(next_use_date), route_id, new_group_dict_vehicle))

            '''司机轮班算法'''
            for k, v in group_dict.iteritems():
                bus_group_res = self.env['bus_group'].search([('id', '=', k)])
                driver_cycle = bus_group_res[0].bus_driver_algorithm_id.cycle
                driver_direction = bus_group_res[0].bus_driver_algorithm_id.direction
                last_bus_driver_algorithm_date = datetime.datetime.strptime(bus_group_res[0].bus_driver_algorithm_date, "%Y-%m-%d")

                res_group_shift = self.env['bus_group_driver_vehicle_shift'].search(
                    [('route_id', '=', route_id),
                     ('use_date', '=', use_date),
                     ('group_id', '=', k)])
                if not res_group_shift: #如果班组管理人车配班前一天的数据不存在，生成不了第二天的人车配班
                    continue
                else:  #存在第二天的人车配班，先删除
                    self.env['bus_group_driver_vehicle_shift'].search([('route_id', '=', route_id),
                                                                     ('use_date', '=', next_use_date),
                                                                     ('group_id', '=', k)]).unlink()

                shift_list = res_group_shift.mapped('choose_sequence')
                old_shift_list = shift_list[:]
                if driver_cycle > 0:
                    if (next_use_date - last_bus_driver_algorithm_date).days >= driver_cycle or str(last_bus_driver_algorithm_date) >= use_date:
                        def leftMove2(list, step):
                            l = list[:step]
                            for m in range(step, len(list)):
                                list[m - step] = list[m]
                            list[len(list) - step:] = l
                            return list

                        if driver_direction == 'positive' and shift_list:  # negative
                            b = shift_list.pop()
                            shift_list.insert(0, b)
                        else:
                            shift_list = leftMove2(shift_list, 1)
                        if str(last_bus_driver_algorithm_date) < use_date:
                            bus_group_res.write({'bus_driver_algorithm_date': use_date})

                _logger.info(u"同步时间:%s,线路id:%s,组:%s 车辆顺序 司机轮班算法 班次顺序%s" % (str(next_use_date), route_id, k, old_shift_list))
                _logger.info(u"同步时间:%s,线路id:%s,组:%s 车辆顺序 司机轮班算法 新班次顺序%s" % (str(next_use_date), route_id, k, shift_list))

                count = 0
                for j in res_group_shift:  #根据前一天的人车配班的数据生成明天的数据 ，根据轮班算法 更新班次
                    new_choose_sequence = shift_list[count]
                    bus_shift_choose_line_id = None
                    if new_choose_sequence > 0:
                        bus_shift_choose_line = bus_group_res[0].bus_shift_id.shift_line_ids.filtered(
                            lambda x: x.sequence == new_choose_sequence)
                        bus_shift_choose_line_id = bus_shift_choose_line.id   #获取新的班次
                    data = {
                        'sequence': j.sequence,
                        'use_date': next_use_date,
                        'group_id': j.group_id.id,
                        'driver_id': j.driver_id.id,
                        'conductor_id': j.conductor_id.id,
                        'bus_shift_id': j.bus_shift_id.id,
                        'bus_shift_choose_line_id': bus_shift_choose_line_id or None,
                        # 'bus_group_vehicle_id':j.bus_group_vehicle_id.id,

                    }
                    self.env['bus_group_driver_vehicle_shift'].create(data)
                    count += 1

                res_group_shift_next_day = self.env['bus_group_driver_vehicle_shift'].search(
                    [('use_date', '=', next_use_date),
                     ('route_id', '=', route_id),
                     ('group_id', '=', k)
                     ])  #获取生成的下一天的数据

                for choose_line_id in res_group_shift_next_day.mapped('bus_shift_choose_line_id').ids:  #根据班次的数量 配置车辆和车序
                    res_group_shift_line = self.env['bus_group_driver_vehicle_shift'].search(
                        [('use_date', '=', next_use_date),
                         ('route_id', '=', route_id),
                         ('group_id', '=', k),
                         ('bus_shift_choose_line_id', '=', choose_line_id),
                         ])

                    for m in zip(res_group_shift_line, old_group_dict[k]):
                        new_t_sequence = new_group_dict_vehicle[k][old_group_dict[k].index(m[1])]
                        bus_group_vehicle_id = res_group_shift.filtered(lambda x: x.vehicle_sequence == m[1])[0].bus_group_vehicle_id.id
                        data = {
                            'vehicle_sequence': new_t_sequence,
                            'bus_group_vehicle_id':bus_group_vehicle_id,
                        }
                        m[0].write(data)

    @api.model
    def run_scheduler(self):
        """
        班组管理 定时任务的入口
        :return:
        """
        _logger.info(u'Start run_scheduler')
        use_date = datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai'))
        use_date = use_date.strftime('%Y-%m-%d')
        self.scheduler_vehicle_shift(use_date=use_date)
        _logger.info(u'End run_scheduler')