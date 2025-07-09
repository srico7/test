from operator import itemgetter

from markupsafe import Markup

from odoo import http
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools import groupby as groupbyelem
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.osv.expression import OR, AND


class CustomerPortal(portal.CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        return values

    def _prepare_home_portal_values(self, orders):
        values = super()._prepare_home_portal_values(orders)
        if 'custom_order_count' in orders:
            values['custom_order_count'] = (
                request.env['custom.order'].search_count(self._prepare_custom_order_domain())
                if request.env['custom.order'].check_access_rights('read', raise_exception=False)
                else 0
            )
        return values

    def _prepare_custom_order_domain(self):
        return []

    def _custom_order_get_page_view_values(self, custom_order, access_token, **kwargs):
        values = {
            'page_name': 'Custom Order',
            'custom_order': custom_order,
            'preview_object': custom_order,
        }
        return self._get_page_view_values(custom_order, access_token, values, False, **kwargs)

    def _prepare_custom_order_values(self, page=1, date_begin=None, date_end=None, sortby=None, filterby='all', search=None, groupby='none', search_in='content'):
        values = self._prepare_portal_layout_values()
        domain = self._prepare_custom_order_domain()

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'reference': {'label': _('Reference'), 'order': 'id desc'},
            'name': {'label': _('Subject'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'custom_state'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            # 'assigned': {'label': _('Assigned'), 'domain': [('user_id', '!=', False)]},
            # 'unassigned': {'label': _('Unassigned'), 'domain': [('user_id', '=', False)]},
            # 'open': {'label': _('Open'), 'domain': [('close_date', '=', False)]},
            # 'closed': {'label': _('Closed'), 'domain': [('close_date', '!=', False)]},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': Markup(_('Search <span class="nolabel"> (in Content)</span>'))},
            # 'ticket_ref': {'input': 'ticket_ref', 'label': _('Search in Reference')},
            # 'message': {'input': 'message', 'label': _('Search in Messages')},
            # 'user': {'input': 'user', 'label': _('Search in Assigned to')},
            # 'status': {'input': 'status', 'label': _('Search in Stage')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'stage': {'input': 'custom_state', 'label': _('Status')},
        }

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # if filterby in ['last_message_sup', 'last_message_cust']:
        #     discussion_subtype_id = request.env.ref('mail.mt_comment').id
        #     messages = request.env['mail.message'].search_read([('model', '=', 'custom.order')], order='date desc')
        #     last_author_dict = {}
        #     for message in messages:
        #         if message['res_id'] not in last_author_dict:
        #             last_author_dict[message['res_id']] = message['author_id'][0]
        #
        #     ticket_author_list = request.env['custom.order'].search_read(fields=['id', 'partner_id'])
        #     ticket_author_dict = dict([(ticket_author['id'], ticket_author['partner_id'][0] if ticket_author['partner_id'] else False) for ticket_author in ticket_author_list])
        #
        #     last_message_cust = []
        #     last_message_sup = []
        #     ticket_ids = set(last_author_dict.keys()) & set(ticket_author_dict.keys())
        #     for ticket_id in ticket_ids:
        #         if last_author_dict[ticket_id] == ticket_author_dict[ticket_id]:
        #             last_message_cust.append(ticket_id)
        #         else:
        #             last_message_sup.append(ticket_id)
        #
        #     if filterby == 'last_message_cust':
        #         domain = AND([domain, [('id', 'in', last_message_cust)]])
        #     else:
        #         domain = AND([domain, [('id', 'in', last_message_sup)]])
        #
        # else:
        #     domain = AND([domain, searchbar_filters[filterby]['domain']])
        #
        # if date_begin and date_end:
        #     domain = AND([domain, [('create_date', '>', date_begin), ('create_date', '<=', date_end)]])
        #
        # # search
        # if search and search_in:
        #     search_domain = []
        #     if search_in == 'ticket_ref':
        #         search_domain = OR([search_domain, [('ticket_ref', 'ilike', search)]])
        #     if search_in == 'content':
        #         search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
        #     if search_in == 'user':
        #         search_domain = OR([search_domain, [('user_id', 'ilike', search)]])
        #     if search_in == 'message':
        #         discussion_subtype_id = request.env.ref('mail.mt_comment').id
        #         search_domain = OR([search_domain, [('message_ids.body', 'ilike', search), ('message_ids.subtype_id', '=', discussion_subtype_id)]])
        #     if search_in == 'status':
        #         search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
        #     domain = AND([domain, search_domain])

        # pager
        custom_order_count = request.env['custom.order'].search_count(domain)
        pager = portal_pager(
            url="/my/customOrders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'search_in': search_in, 'search': search, 'groupby': groupby, 'filterby': filterby},
            total=custom_order_count,
            page=page,
            step=self._items_per_page
        )

        custom_orders = request.env['custom.order'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        # request.session['my_tickets_history'] = tickets.ids[:100]

        if not custom_orders:
            grouped_custom_orders = []
        elif groupby != 'none':
            grouped_custom_orders = [request.env['custom.order'].concat(*g) for k, g in groupbyelem(custom_orders, itemgetter(searchbar_groupby[groupby]['input']))]
        else:
            grouped_custom_orders = [custom_orders]

        values.update({
            'date': date_begin,
            'grouped_custom_orders': grouped_custom_orders,
            'page_name': 'Custom Orders',
            'default_url': '/my/customOrders',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'sortby': sortby,
            'groupby': groupby,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
        })
        return values

    @http.route(['/my/customOrders', '/my/customOrders/page/<int:page>'], type='http', auth="user", website=True)
    def my_custom_orders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby='all', search=None,
                            groupby='none', search_in='content', **kw):
        values = self._prepare_custom_order_values(page, date_begin, date_end, sortby, filterby, search, groupby,
                                                 search_in)
        return request.render("vkd_clearance_process.portal_custom_order", values)

    @http.route("/my/customOrder", type="http", auth="user", website=True)
    def custom_order_follow(self, access_token=None, **kw):
        """Controller to display the current custom order"""
        try:
            # Fetch the current user's custom order (example: the latest or active one)
            custom_order = request.env['custom.order'].sudo().search(
                [], limit=1)

            if not custom_order:
                raise MissingError("No custom order found for the current user.")
        except (AccessError, MissingError):
            # Redirect to 'my account' page if access is denied or record is missing
            return request.redirect('/my')

        # Prepare values for rendering
        values = {
            'custom_order': custom_order,
            'object': custom_order,
        }
        return request.render("vkd_clearance_process.custom_order_followup", values)