import json

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
from tornado import web

from .check_file_status import check_file_status
from .delete_file import delete_file_from_hydroshare
from .download_file import download_file_from_hydroshare, list_available_files_for_download
from .refresh_file import refresh_file_from_hydroshare
from .upload_file import upload_file_to_hydroshare
from .utils import get_hydroshare_resource_download_dir


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


class DownloadFileHandler(APIHandler):
    @web.authenticated
    async def post(self):
        try:
            data = self.get_json_body()
            resource_id = data["resource_id"]
            file_path = data["file_path"]
            base_path = data.get("base_path")
            response = await download_file_from_hydroshare(resource_id, file_path, base_path)
            await self.finish(json.dumps({"response": response}))
        except Exception as e:
            self.set_status(500)
            await self.finish(json.dumps({"response": {"error": str(e)}}))


class ListFilesHandler(APIHandler):
    @web.authenticated
    async def post(self):
        try:
            data = self.get_json_body()
            resource_id = data["resource_id"]
            base_path = data.get("base_path")
            response = await list_available_files_for_download(resource_id, base_path)
            await self.finish(json.dumps({"response": response}))
        except Exception as e:
            self.set_status(500)
            await self.finish(json.dumps({"response": {"error": str(e)}}))


class ConfigHandler(APIHandler):
    @web.authenticated
    async def get(self):
        try:
            download_dir = get_hydroshare_resource_download_dir()
            response = {
                "download_dir": download_dir
            }
            await self.finish(json.dumps({"response": response}))
        except Exception as e:
            self.set_status(500)
            await self.finish(json.dumps({"response": {"error": str(e)}}))


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    upload_route_pattern = url_path_join(base_url, "hydroshare", "upload")
    refresh_route_pattern = url_path_join(base_url, "hydroshare", "refresh")
    delete_route_pattern = url_path_join(base_url, "hydroshare", "delete")
    check_file_status_route_pattern = url_path_join(base_url, "hydroshare", "status")
    download_route_pattern = url_path_join(base_url, "hydroshare", "download")
    list_files_route_pattern = url_path_join(base_url, "hydroshare", "list_files")
    config_route_pattern = url_path_join(base_url, "hydroshare", "config")
    web_app.add_handlers(
        host_pattern,
        [
            (upload_route_pattern, UploadFileHandler),
            (refresh_route_pattern, RefreshFileHandler),
            (delete_route_pattern, DeleteFileHandler),
            (check_file_status_route_pattern, CheckFileStatusHandler),
            (download_route_pattern, DownloadFileHandler),
            (list_files_route_pattern, ListFilesHandler),
            (config_route_pattern, ConfigHandler),
        ],
    )
