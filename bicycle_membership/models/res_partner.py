from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_is_member = fields.Boolean(string='Is Member', default=False)

    x_total_spent = fields.Monetary(
        string='Total Spent',
        readonly=True,
        currency_field='currency_id'
    )

    x_loyalty_points = fields.Integer(
        string='Loyalty Points',
        readonly=True
    )

    x_member_tier_id = fields.Many2one(
        'bicycle.member.tier',
        string='Current Tier',
        compute='_compute_member_tier',
        store=True
    )

    # Chuẩn hoá tên khi tạo
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = self._normalize_name(vals['name'])
        return super().create(vals_list)

    # Chuẩn hoá tên khi update
    def write(self, vals):
        if 'name' in vals and vals.get('name'):
            vals['name'] = self._normalize_name(vals['name'])
        return super().write(vals)

    def _normalize_name(self, name):
        if not name:
            return name

        cleaned_name = re.sub(r'[^A-Za-zÀ-ỹ\s]', '', name)

        cleaned_name = ' '.join(cleaned_name.split())

        return cleaned_name.title()

    # Validate phone
    @api.constrains('phone')
    def _check_phone(self):
        for record in self:
            if not record.phone:
                raise ValidationError('Số điện thoại là bắt buộc!')

            phone = record.phone.strip()

            if not phone.isdigit():
                raise ValidationError('Số điện thoại chỉ được chứa chữ số!')

            if len(phone) != 10:
                raise ValidationError('Số điện thoại phải gồm đúng 10 số!')

    # Validate email
    @api.constrains('email')
    def _check_email(self):
        email_regex = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

        for record in self:
            if record.email:
                email = record.email.strip()
                if not re.match(email_regex, email):
                    raise ValidationError('Email không đúng định dạng!')

    # Unique phone & email
    @api.constrains('phone', 'email')
    def _check_unique_contact(self):
        for record in self:
            if record.phone:
                if self.search_count([
                    ('id', '!=', record.id),
                    ('phone', '=', record.phone)
                ]):
                    raise ValidationError('Số điện thoại đã tồn tại!')

            if record.email:
                if self.search_count([
                    ('id', '!=', record.id),
                    ('email', '=', record.email)
                ]):
                    raise ValidationError('Email đã tồn tại!')

    # Compute tier
    @api.depends('x_loyalty_points', 'x_is_member')
    def _compute_member_tier(self):
        tiers = self.env['bicycle.member.tier'].search(
            [], order='min_points desc'
        )

        for partner in self:
            if not partner.x_is_member:
                partner.x_member_tier_id = False
                continue

            partner.x_member_tier_id = next(
                (t for t in tiers if partner.x_loyalty_points >= t.min_points),
                False
            )