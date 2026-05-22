from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_is_member = fields.Boolean(
        string='Is Member',
        default=False
    )

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

    # --- RÀNG BUỘC SỐ ĐIỆN THOẠI ---
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

    # --- RÀNG BUỘC EMAIL ---
    @api.constrains('email')
    def _check_email(self):
        email_regex = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        for record in self:
            if record.email:
                email = record.email.strip()
                if not re.match(email_regex, email):
                    raise ValidationError('Email không đúng định dạng!')
    
    # --- KIỂM TRA TRÙNG LẶP SĐT VÀ EMAIL ---
    @api.constrains('phone', 'email')
    def _check_unique_contact(self):
        for record in self:
            if record.phone:
                existing_phone = self.search([
                    ('id', '!=', record.id),
                    ('phone', '=', record.phone)
                ], limit=1)
                if existing_phone:
                    raise ValidationError(f'Số điện thoại {record.phone} đã tồn tại!')

            if record.email:
                existing_email = self.search([
                    ('id', '!=', record.id),
                    ('email', '=', record.email)
                ], limit=1)
                if existing_email:
                    raise ValidationError(f'Email {record.email} đã tồn tại!')
                
    # --- TÍNH TOÁN HẠNG THÀNH VIÊN ---
    @api.depends('x_loyalty_points', 'x_is_member')
    def _compute_member_tier(self):
        all_tiers = self.env['bicycle.member.tier'].search(
            [],
            order='min_points desc'
        )
        for partner in self:
            if not partner.x_is_member:
                partner.x_member_tier_id = False
                continue

            matching_tier = False
            for tier in all_tiers:
                if partner.x_loyalty_points >= tier.min_points:
                    matching_tier = tier
                    break
            partner.x_member_tier_id = matching_tier