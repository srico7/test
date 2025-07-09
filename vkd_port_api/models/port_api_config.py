import logging
from functools import wraps
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import requests
from requests.exceptions import RequestException, HTTPError
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def handle_api_errors(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except HTTPError as http_err:
            _logger.error(f"{func.__name__} HTTP error: {http_err}")
            return False
        except RequestException as req_err:
            _logger.error(f"{func.__name__} request error: {req_err}")
            return False
        except Exception as e:
            _logger.error(f"{func.__name__} unexpected error: {e}")
            return False

    return wrapper


class PortAPIConfig(models.Model):
    _name = 'port.api.config'
    _description = 'Port API Configuration'

    name = fields.Char(required=True, default='Port API')
    api_url = fields.Char('API URL', required=True, default='https://my.port.mv')
    username = fields.Char('Username', required=True)
    password = fields.Char('Password', required=True)
    token = fields.Text('Access Token', readonly=True)
    token_expiry = fields.Datetime('Token Expiry')
    active = fields.Boolean(default=True)

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                      data: Optional[Dict] = None, require_auth: bool = True) -> Dict[str, Any]:
        url = f"{self.api_url}/api/{endpoint}"
        headers = {}

        if require_auth:
            if not self.token:
                raise UserError(_("No valid token found. Please authenticate first."))
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params or {},
                json=data if method.lower() == 'post' else None,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise UserError(_("Request timed out. Please try again later."))
        except requests.exceptions.ConnectionError:
            raise UserError(_("Could not connect to the server. Please check your internet connection."))

    @handle_api_errors
    def _get_auth_token(self):
        result = self._make_request(
            'POST',
            'login',
            data={'username': self.username, 'password': self.password},
            require_auth=False
        )

        self.token = result.get('token')
        return bool(self.token)

    @handle_api_errors
    def _refresh_token(self):
        result = self._make_request('GET', 'refresh_token')
        self.token = result.get('token')
        return bool(self.token)

    def get_valid_token(self):
        self.ensure_one()

        if not self.token:
            return self._get_auth_token()
        else:
            return self._refresh_token()

    def test_connection(self):
        return self.get_valid_token()

    @handle_api_errors
    def fetch_bl_list(self):
        self.ensure_one()
        if not self.get_valid_token():
            return False

        bl_data = self._make_request(
            endpoint='bill_of_lading_documents',
            method='GET',
        )

        if not bl_data or not isinstance(bl_data, list):
            raise ValueError("Invalid response format from API")

        self.env['port.bl'].create_or_update(bl_data, self.id)

    @handle_api_errors
    def fetch_bl_details(self, bl_id=None, port_bl_id=None):
        self.ensure_one()
        if not self.get_valid_token():
            return False

        bl_data = self._make_request(
            endpoint=f"bill_of_lading_documents/{bl_id}",
            method='GET',
        )

        if not bl_data or not isinstance(bl_data, dict):
            raise ValueError("Invalid response format from API")

        self.env['port.bl.details'].create_or_update(bl_data, port_bl_id=port_bl_id)

    @handle_api_errors
    def fetch_bl_by_search(self, bl_name=None):
        self.ensure_one()
        if not self.get_valid_token():
            return False

        # bl_data = self._make_request(
        #     endpoint=f"bl_search?search={bl_name}",
        #     method='GET',
        # )
        bl_data = self._make_request(
            endpoint=f"bill_of_lading_documents?query={bl_name}",
            method='GET',
        )

        if not bl_data or not isinstance(bl_data, list):
            raise ValueError("Invalid response format from API")

        self.env['port.bl'].create_or_update(bl_data, self.id)


