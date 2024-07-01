from django.utils.deprecation import MiddlewareMixin
from asgiref.sync import sync_to_async
import asyncio

class SyncToAsyncMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Convertir la vue en une fonction asynchrone si nécessaire
        if not asyncio.iscoroutinefunction(view_func):
            view_func = sync_to_async(view_func)
        return view_func(request, *view_args, **view_kwargs)
