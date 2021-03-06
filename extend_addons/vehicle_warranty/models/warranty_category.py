# -*- coding: utf-8 -*-
from odoo import models, fields, api,exceptions,_

class WarrantyCategory(models.Model): # 维保类别
    _name = 'warranty_category'
    _order = "idpath asc"

    name = fields.Char(string="Warranty Category Name", required=True) # 名称
    code = fields.Char(string='Warranty Category Code', required=True) # 代码

    idpath = fields.Char(string="ID Path") # id路径
    level = fields.Integer() # 层级

    #2017年7月24日 新增字段：保养时长
    maintenance_time = fields.Float(string='Maintenance time',digits=(9,1))

    @api.constrains('maintenance_time')
    def _check_maintenance_time(self):
        '''保养时长值校验'''
        for order in self:
            if order.maintenance_time < 0:
                raise exceptions.ValidationError(_("maintenance_time must be greater than or equal to zero"))


    state = fields.Selection([ # 状态
        ('use', "use"), # 在用
        ('done', "Filing"),  # 归档
    ], default='use', string="MyState")

    active = fields.Boolean(string="MyActive", default=True)

    @api.multi
    def action_in_use(self):
        self.state = 'use'
        self.active = True

    @api.multi
    def action_filing(self):
        self.state = 'done'
        self.active = False

    manhour = fields.Float(digits=(6, 1), default=0 , compute='_compute_manhour') # 工时定额

    # 额定工时
    quota_workhour = fields.Float(string="work hour quota")

    # 额定费用
    quota_cost = fields.Float(string="quota cost")

    # 活动里程
    active_mileage = fields.Integer(string="active mileage")

    remark = fields.Char()  # 备注

    parent_id = fields.Many2one('warranty_category', index=True, domain=[('state','=','use')],readonly="true") # 父分类
    child_ids = fields.One2many('warranty_category', 'parent_id') # 子分类

    project_ids = fields.Many2many('warranty_project', domain=[('state','=','use')]) # 保修项目

    sum_categorie_manhour = fields.Float(digits=(6, 1), default=0, compute='_compute_manhour') # 子类工时汇总

    sum_project_manhour = fields.Float(digits=(6, 1), default=0, compute='_compute_manhour') # 项目工时汇总

    is_top_level = fields.Boolean(string='Is Top Level', default=False) # 是否是顶级类别

    warranty_type = fields.Selection([ # 维保类型
        ('warranty', 'Warranty'),
        ('maintain', 'Maintain'),
        ], string="Warranty Type", default="warranty")

    warranty_level = fields.Many2one('warranty_level', 'Warranty Level', ondelete="set null") # 维保级别

    def category_manhour_get(self):
        result = []
        for record in self:
            sum_manhour = 0
            if record.child_ids:
                for child_record in record.child_ids:
                    sum_manhour += sum(child_record.project_ids.mapped('manhour'))
                    sum_manhour += child_record.category_manhour_get()[0][1]
            result.append((record.id, sum_manhour))
        return result

    @api.depends('project_ids', 'child_ids')
    def _compute_manhour(self):
        for category in self:
            # temp_category_manhour=category.category_manhour_get()
            category.sum_categorie_manhour = category.category_manhour_get()[0][1]
            category.sum_project_manhour = sum(category.project_ids.mapped('manhour'))
            category.manhour=category.sum_categorie_manhour+category.sum_project_manhour

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.parent_id:
                name = "%s / %s" % (record.parent_id.name_get()[0][1], name)
            result.append((record.id, name))
        return result

    def idpath_get(self):
        result = []
        for record in self:
            idpath = record.id
            if record.parent_id:
                idpath = "%s/%s" % (record.parent_id.idpath_get()[0][1], idpath)
            result.append((record.id, idpath))
        return result

    @api.model
    def create(self, vals):
        result = super(WarrantyCategory, self).create(vals)
        idpath = "/" + str(result.idpath_get()[0][1]) + "/"
        result.idpath=idpath
        count = idpath.count("/")-1
        result.level = count
        if count == 1:
            result.is_top_level=True
        else:
            result.is_top_level = False
        return result

    @api.multi
    def write(self, vals):
        idpath ="/"+str(self.idpath_get()[0][1])+"/"
        vals['idpath'] = idpath
        count = idpath.count("/")-1
        vals['level'] = count
        if count == 1:
            vals['is_top_level']=True
        else:
            vals['is_top_level'] = False
        return super(WarrantyCategory, self).write(vals)


class WarrantyProject(models.Model): # 保修项目
    _name = 'warranty_project'
    _order = 'id desc'

    name = fields.Char(string='Project Name', required=True) # 项目名称
    code = fields.Char(string='Project Code', required=True) # 项目编码

    state = fields.Selection([ # 状态
        ('use', "use"), # 在用
        ('done', "Filing"),  # 归档
    ], default='use', string="MyState")

    active = fields.Boolean(string="MyActive", default=True)

    @api.multi
    def action_in_use(self):
        self.state = 'use'
        self.active = True

    @api.multi
    def action_filing(self):
        self.state = 'done'
        self.active = False

    mode = fields.Many2one('warranty_mode', 'Mode', ondelete="set null") # 保修方式

    manhour = fields.Float(digits=(6, 1), default=1) # 工时定额

    remark = fields.Char()  # 备注

    # is_important_product = fields.Boolean() # 是否重要部件

    # important_product_id = fields.Many2one('product.product', string="Important Product", domain=[('is_important', '=', True)]) # 重要部件

    avail_ids = fields.One2many('warranty_project_product', 'project_id', string="Products") # 用料清单

    operational_manual = fields.Text() # 作业手册

    inspection_criteria = fields.Text() # 检验标准

    is_materials = fields.Boolean(string='Is Materials',defaul=False)

    @api.constrains('manhour')
    def check_manhour(self):
        """
            新增验证：
                保存数据时，校验工时定额
        :return:
        """
        for order in self:
                if order.manhour <= 0:
                    raise exceptions.ValidationError(_("manhour Can not be less than or equal to 0！"))

class WarrantyProjectProduct(models.Model): # 维保项目_用料清单
    _name = 'warranty_project_product'

    project_id = fields.Many2one('warranty_project', ondelete='cascade', string="Warranty Project")  # 保养项目

    product_id = fields.Many2one('product.product', string="Product")
    product_code = fields.Char("Product Code", related='product_id.default_code', readonly=True)
    categ_id = fields.Many2one('product.category', related='product_id.categ_id', string='Warranty Category', readonly=True)
    uom_id = fields.Many2one('product.uom', 'Unit of Measure', related='product_id.uom_id', readonly=True)
    onhand_qty = fields.Float('Quantity On Hand', related='product_id.qty_available', readonly=True)
    virtual_available = fields.Float('Forecast Quantity', related='product_id.virtual_available', readonly=True)

    list_price = fields.Float(related='product_id.list_price', readonly=True)

    require_trans = fields.Boolean("Require Trans", related='product_id.require_trans', readonly=True)
    vehicle_model = fields.Many2many(related='product_id.vehicle_model', relation='product_vehicle_model_rec',
                                      string='Suitable Vehicle', readonly=True)

    description = fields.Text("Product Size", related='product_id.description', readonly=True)

    change_count = fields.Integer("Change Count")
    max_count = fields.Integer("Max Count")
    remark = fields.Text("Remark", help="Remark")

    @api.constrains('change_count', 'max_count')
    def _check_change_count(self):
        for r in self:
            if r.change_count > r.max_count:
                raise exceptions.ValidationError(_("max_count must be greater than or equal to change_count"))


class WarrantyMode(models.Model): # 维保方式
    _name = 'warranty_mode'
    # _order = 'sequence asc'

    name = fields.Char(required=True)

    code = fields.Char(required=True) # 编码

    _sql_constraints = [('warranty_mode_name_unique', 'unique(name)', 'Mode name already exists')]