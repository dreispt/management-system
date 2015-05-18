# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2015 - present Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
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
from openerp import models, fields, api, _


STATES = [
    ('draft', _('Draft')),
    ('analysis', _('Analysis')),
    ('pending', _('Pending Approval')),
    ('open', _('In Progress')),
    ('done', _('Closed')),
    ('cancel', _('Cancelled')),
]


class MgmtsystemNonconformityStage(models.Model):

    _name = 'mgmtsystem.nonconformity.stage'
    _order = 'sequence'

    name = fields.char('Stage Name', required=True, translate=True)
    description = fields.text('Description')
    sequence = fields.integer('Sequence', default=10)
    state = fields.Selection(STATES, 'State')
    fold = fields.boolean(
        'Folded in Kanban View',
        help='This stage is folded in the kanban view when'
             'there are no records in that stage to display.')

    @api.model
    def get_default_stage(self):
        return self.search([('fold', '=', False)], limit=1)

    @api.model
    def state_to_stage(self, state):
        return self.search([('state', '=', state)], limit=1)

