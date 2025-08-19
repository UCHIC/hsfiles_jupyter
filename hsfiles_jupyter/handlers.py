import json

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
from tornado import web

from .check_file_status import check_file_status
from .delete_file import delete_file_from_hydroshare
from .refresh_file import refresh_file_from_hydroshare
from .upload_file import upload_file_to_hydroshare


class BaseFileHandler(APIHandler):
    async def handle_request(self, operation):
        try:
            data = self.get_json_body()
            file_path = data["path"]
            response = await operation(file_path)
            await self.finish(json.dumps({"response": response}))
        except Exception as e:
            self.set_status(500)
            await self.finish(json.dumps({"response": {"error": str(e)}}))


class UploadFileHandler(BaseFileHandler):
    @web.authenticated
    async def post(self):
        await self.handle_request(upload_file_to_hydroshare)


class RefreshFileHandler(BaseFileHandler):
    @web.authenticated
    async def post(self):
        await self.handle_request(refresh_file_from_hydroshare)


class DeleteFileHandler(BaseFileHandler):
    @web.authenticated
    async def post(self):
        await self.handle_request(delete_file_from_hydroshare)


class CheckFileStatusHandler(BaseFileHandler):
    @web.authenticated
    async def post(self):
        await self.handle_request(check_file_status)


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    upload_route_pattern = url_path_join(base_url, "hydroshare", "upload")
    refresh_route_pattern = url_path_join(base_url, "hydroshare", "refresh")
    delete_route_pattern = url_path_join(base_url, "hydroshare", "delete")
    check_file_status_route_pattern = url_path_join(base_url, "hydroshare", "status")
    web_app.add_handlers(
        host_pattern,
        [
            (upload_route_pattern, UploadFileHandler),
            (refresh_route_pattern, RefreshFileHandler),
            (delete_route_pattern, DeleteFileHandler),
            (check_file_status_route_pattern, CheckFileStatusHandler),
        ],
    )
