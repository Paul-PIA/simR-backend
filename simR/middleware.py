import asyncio
from django.utils.deprecation import MiddlewareMixin
from asgiref.sync import sync_to_async

class SyncToAsyncMiddleware(MiddlewareMixin):
    def __call__(self, request):
        response = self.get_response(request)
        if asyncio.iscoroutine(response):
            return sync_to_async(response)
        return response
