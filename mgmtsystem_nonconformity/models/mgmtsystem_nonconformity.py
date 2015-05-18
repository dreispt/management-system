# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, fields, netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

import time


class MgmtsystemNonconformity(models.Model):

    _name = "mgmtsystem.nonconformity"
    _description = "Nonconformity"
    _rec_name = "description"
    _inherit = ['mail.thread']
    _order = "date desc"
    _track = {
        'field': {
            'mgmtsystem_nonconformity.mt_stage': (
                lambda s, c, u, o, ctx=None: True),
        },
    }

    @api.model
    def _get_default_stage(self):
        return self.stage_id.get_default_state()

    name = fields.Char('Name')

    # 1. Description
    ref = fields.Char(
        'Reference',
        required=True,
        readonly=True,
        default="NEW"
    )
    date = fields.Date(
        'Date',
        required=True,
        default=lambda *a: time.strftime(DATE_FORMAT)
    )
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    reference = fields.Char('Related to')
    responsible_user_id = fields.Many2one(
        'res.users',
        'Responsible',
        required=True,
    )
    manager_user_id = fields.Many2one(
        'res.users',
        'Manager',
        required=True,
    )
    author_user_id = fields.Many2one(
        'res.users',
        'Filled in by',
        required=True,
        default=lambda self: self.env.user.id
    )
    origin_ids = fields.Many2many(
        'mgmtsystem.nonconformity.origin',
        'mgmtsystem_nonconformity_origin_rel',
        'nonconformity_id',
        'origin_id',
        'Origin',
        required=True,
    )
    procedure_ids = fields.Many2many(
        'document.page',
        'mgmtsystem_nonconformity_procedure_rel',
        'nonconformity_id',
        'procedure_id',
        'Procedure',
    )
    description = fields.Text('Description', required=True)
    stage_id = fields.Many2one(
        'mgmtsystem.nonconformity.stage', 'Stage',
        default=_get_default_stage, index=True)
    state = fields.Selection(
        related='stage_id.state', string='Stage State',
        store=True, index=True)
    system_id = fields.Many2one('mgmtsystem.system', 'System')

    # 2. Root Cause Analysis
    cause_ids = fields.Many2many(
        'mgmtsystem.nonconformity.cause',
        'mgmtsystem_nonconformity_cause_rel',
        'nonconformity_id',
        'cause_id',
        'Cause',
    )
    severity_id = fields.Many2one(
        'mgmtsystem.nonconformity.severity',
        'Severity',
    )
    analysis = fields.Text('Analysis')
    immediate_action_id = fields.Many2one(
        'mgmtsystem.action',
        'Immediate action',
        domain="[('nonconformity_ids', '=', id)]",
    )
    analysis_date = fields.Datetime(
        'Analysis Date',
        readonly=True,
        track_visibility='onchange',
    )
    analysis_user_id = fields.Many2one(
        'res.users',
        'Analysis by',
        readonly=True,
        track_visibility='onchange',
    )

    # 3. Action Plan
    action_ids = fields.Many2many(
        'mgmtsystem.action',
        'mgmtsystem_nonconformity_action_rel',
        'nonconformity_id',
        'action_id',
        'Actions',
    )
    actions_date = fields.Datetime('Action Plan Date', readonly=True)
    actions_user_id = fields.Many2one(
        'res.users',
        'Action Plan by',
        readonly=True,
    )
    action_comments = fields.Text(
        'Action Plan Comments',
        help="Comments on the action plan.",
    )

    # 4. Effectiveness Evaluation
    evaluation_date = fields.Datetime('Evaluation Date', readonly=True)
    evaluation_user_id = fields.Many2one(
        'res.users',
        'Evaluation by',
        readonly=True,
    )
    evaluation_comments = fields.Text(
        'Evaluation Comments',
        help="Conclusions from the last effectiveness evaluation.",
    )

    # Multi-company
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id.id)

    # Demo data missing fields...
    corrective_action_id = fields.Many2one(
        'mgmtsystem.action',
        'Corrective action',
        domain="[('nonconformity_id', '=', id)]",
    )
    preventive_action_id = fields.Many2one(
        'mgmtsystem.action',
        'Preventive action',
        domain="[('nonconformity_id', '=', id)]",
    )

    @property
    @api.multi
    def verbose_name(self):
        return self.env['ir.model'].search([('model', '=', self._name)]).name

    @api.model
    def create(self, vals):
        vals.update({
            'ref': self.env['ir.sequence'].get('mgmtsystem.nonconformity')
        })
        return super(MgmtsystemNonconformity, self).create(vals)

    @api.multi
    def message_auto_subscribe(self, updated_fields, values=None):
        """Add the responsible, manager and OpenChatter follow list."""
        self.ensure_one()
        user_ids = [
            self.responsible_user_id.id,
            self.manager_user_id.id,
            self.author_user_id.id,
        ]
        self.message_subscribe_users(user_ids=user_ids, subtype_ids=None)
        return super(MgmtsystemNonconformity, self).message_auto_subscribe(
            updated_fields=updated_fields,
            values=values
        )

    @api.multi
    def case_reset(self):
        """Reset to Draft and restart the workflow"""
        wf_service = netsvc.LocalService("workflow")
        for nc in self:
            wf_service.trg_create(self._uid, self._name, nc.id, self._cr)
        return self.write({'state': self.stage_id.state_to_state('draft')})
