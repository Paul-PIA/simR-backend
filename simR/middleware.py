from asgiref.sync import sync_to_async
import asyncio

class SyncToAsyncMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if asyncio.iscoroutinefunction(self.get_response):
            response = asyncio.run(self.get_response(request))
        else:
            response = self.get_response(request)
        return response


