import json
from rest_framework.utils.encoders import JSONEncoder

from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response


class CustomResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def data_without_message_key(self, data):
        if isinstance(data, dict):
            data.pop('message', None)
        return data

    def data_without_detail_key(self, data):
        data.pop('detail', None)
        return data

    def get_error_message(self, response_data):
        default_error_message = str(_("An error occurred"))

        message = response_data.get("detail", default_error_message)
        return message[0] if isinstance(message, list) else message

    def get_success_message(self, response_data):
        default_success_message = str(_("Done successfully"))

        if not isinstance(response_data, dict):
            return default_success_message

        message = response_data.get("message", default_success_message)

        return message[0] if isinstance(message, list) else message

    def __call__(self, request):
        response = self.get_response(request)

        if getattr(request, 'skip_custom_response', False):
            return response  # skip formatting

        if isinstance(response, Response):
            # Skip wrapping for 204 No Content responses
            if response.status_code == 204:
                return response

            # Check if response is an error or a success
            if 200 <= response.status_code < 300:
                response.data = {
                    "success": True,
                    "message": self.get_success_message(response.data),
                    "data": self.data_without_message_key(response.data),
                }
            else:
                response.data = {
                    "success": False,
                    "message": self.get_error_message(response.data),
                    "errors": self.data_without_detail_key(response.data),
                }

            # Ensure the response content type is JSON
            response.content = json.dumps(response.data, cls=JSONEncoder)
        return response
