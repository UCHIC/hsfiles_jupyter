import json

from asynctest import CoroutineMock, PropertyMock, patch
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.web import Application, RequestHandler

from hsfiles_jupyter.handlers import (
    CheckFileStatusHandler as OriginalCheckFileStatusHandler,
)
from hsfiles_jupyter.handlers import (
    DeleteFileHandler as OriginalDeleteFileHandler,
)
from hsfiles_jupyter.handlers import (
    DownloadFileHandler as OriginalDownloadFileHandler,
)
from hsfiles_jupyter.handlers import (
    ListFilesHandler as OriginalListFilesHandler,
)
from hsfiles_jupyter.handlers import (
    RefreshFileHandler as OriginalRefreshFileHandler,
)
from hsfiles_jupyter.handlers import (
    UploadFileHandler as OriginalUploadFileHandler,
)


class BaseHandler(RequestHandler):
    def check_xsrf_cookie(self):
        pass


class UploadFileHandler(BaseHandler, OriginalUploadFileHandler):
    pass


class RefreshFileHandler(BaseHandler, OriginalRefreshFileHandler):
    pass


class DeleteFileHandler(BaseHandler, OriginalDeleteFileHandler):
    pass


class CheckFileStatusHandler(BaseHandler, OriginalCheckFileStatusHandler):
    pass


class DownloadFileHandler(BaseHandler, OriginalDownloadFileHandler):
    pass


class ListFilesHandler(BaseHandler, OriginalListFilesHandler):
    pass


class TestHandlers(AsyncHTTPTestCase):
    def get_app(self):
        return Application(
            [
                (r"/hydroshare/upload", UploadFileHandler),
                (r"/hydroshare/refresh", RefreshFileHandler),
                (r"/hydroshare/delete", DeleteFileHandler),
                (r"/hydroshare/status", CheckFileStatusHandler),
                (r"/hydroshare/download", DownloadFileHandler),
                (r"/hydroshare/list_files", ListFilesHandler),
            ],
            cookie_secret="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            xsrf_cookies=False,
        )

    async def run_test(self, url, mock_function, mock_return_value, mock_current_user, mock_prepare, body=None):
        if body is None:
            body = {"path": "test_file_path"}
        mock_current_user.return_value = "test_user"
        mock_prepare.return_value = None
        mock_function.return_value = mock_return_value
        response = await self.http_client.fetch(
            self.get_url(url),
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(body),
        )
        assert response.code == 200
        assert json.loads(response.body) == {"response": mock_return_value}

    @patch("jupyter_server.base.handlers.JupyterHandler.current_user", new_callable=PropertyMock)
    @patch("jupyter_server.base.handlers.JupyterHandler.prepare", new_callable=CoroutineMock)
    @patch("hsfiles_jupyter.handlers.upload_file_to_hydroshare", new_callable=CoroutineMock)
    @gen_test
    async def test_upload_file_handler(self, mock_upload, mock_prepare, mock_current_user):
        url = "/hydroshare/upload"
        await self.run_test(
            url=url,
            mock_function=mock_upload,
            mock_return_value={"success": "File uploaded"},
            mock_current_user=mock_current_user,
            mock_prepare=mock_prepare,
        )

    @patch("jupyter_server.base.handlers.JupyterHandler.current_user", new_callable=PropertyMock)
    @patch("jupyter_server.base.handlers.JupyterHandler.prepare", new_callable=CoroutineMock)
    @patch("hsfiles_jupyter.handlers.refresh_file_from_hydroshare", new_callable=CoroutineMock)
    @gen_test
    async def test_refresh_file_handler(self, mock_refresh, mock_prepare, mock_current_user):
        url = "/hydroshare/refresh"
        await self.run_test(
            url=url,
            mock_function=mock_refresh,
            mock_return_value={"success": "File refreshed"},
            mock_current_user=mock_current_user,
            mock_prepare=mock_prepare,
        )

    @patch("jupyter_server.base.handlers.JupyterHandler.current_user", new_callable=PropertyMock)
    @patch("jupyter_server.base.handlers.JupyterHandler.prepare", new_callable=CoroutineMock)
    @patch("hsfiles_jupyter.handlers.delete_file_from_hydroshare", new_callable=CoroutineMock)
    @gen_test
    async def test_delete_file_handler(self, mock_delete, mock_prepare, mock_current_user):
        url = "/hydroshare/delete"
        await self.run_test(
            url=url,
            mock_function=mock_delete,
            mock_return_value={"success": "File deleted"},
            mock_current_user=mock_current_user,
            mock_prepare=mock_prepare,
        )

    @patch("jupyter_server.base.handlers.JupyterHandler.current_user", new_callable=PropertyMock)
    @patch("jupyter_server.base.handlers.JupyterHandler.prepare", new_callable=CoroutineMock)
    @patch("hsfiles_jupyter.handlers.check_file_status", new_callable=CoroutineMock)
    @gen_test
    async def test_check_file_status_handler(self, mock_check_status, mock_prepare, mock_current_user):
        url = "/hydroshare/status"
        await self.run_test(
            url=url,
            mock_function=mock_check_status,
            mock_return_value={"success": "File exists"},
            mock_current_user=mock_current_user,
            mock_prepare=mock_prepare,
        )

    @patch("jupyter_server.base.handlers.JupyterHandler.current_user", new_callable=PropertyMock)
    @patch("jupyter_server.base.handlers.JupyterHandler.prepare", new_callable=CoroutineMock)
    @patch("hsfiles_jupyter.handlers.download_file_from_hydroshare", new_callable=CoroutineMock)
    @gen_test
    async def test_download_file_handler(self, mock_download, mock_prepare, mock_current_user):
        url = "/hydroshare/download"
        await self.run_test(
            url=url,
            mock_function=mock_download,
            mock_return_value={"success": "File downloaded"},
            mock_current_user=mock_current_user,
            mock_prepare=mock_prepare,
            body={"resource_id": "test_resource_id", "file_path": "test_file_path"},
        )

    @patch("jupyter_server.base.handlers.JupyterHandler.current_user", new_callable=PropertyMock)
    @patch("jupyter_server.base.handlers.JupyterHandler.prepare", new_callable=CoroutineMock)
    @patch("hsfiles_jupyter.handlers.download_file_from_hydroshare", new_callable=CoroutineMock)
    @gen_test
    async def test_download_file_handler_error(self, mock_download, mock_prepare, mock_current_user):
        """Test error handling in the download file handler."""
        url = "/hydroshare/download"
        mock_current_user.return_value = "test_user"
        mock_prepare.return_value = None
        mock_download.return_value = {"error": "File not found"}

        response = await self.http_client.fetch(
            self.get_url(url),
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"resource_id": "test_resource_id", "file_path": "nonexistent_file.txt"}),
        )

        assert response.code == 200
        assert json.loads(response.body) == {"response": {"error": "File not found"}}

    @patch("jupyter_server.base.handlers.JupyterHandler.current_user", new_callable=PropertyMock)
    @patch("jupyter_server.base.handlers.JupyterHandler.prepare", new_callable=CoroutineMock)
    @patch("hsfiles_jupyter.handlers.list_available_files_for_download", new_callable=CoroutineMock)
    @gen_test
    async def test_list_files_handler(self, mock_list_files, mock_prepare, mock_current_user):
        url = "/hydroshare/list_files"
        await self.run_test(
            url=url,
            mock_function=mock_list_files,
            mock_return_value={
                "resource_id": "test_resource_id",
                "available_files": ["file1.txt", "file2.txt"]
            },
            mock_current_user=mock_current_user,
            mock_prepare=mock_prepare,
            body={"resource_id": "test_resource_id"},
        )

    @patch("jupyter_server.base.handlers.JupyterHandler.current_user", new_callable=PropertyMock)
    @patch("jupyter_server.base.handlers.JupyterHandler.prepare", new_callable=CoroutineMock)
    @patch("hsfiles_jupyter.handlers.list_available_files_for_download", new_callable=CoroutineMock)
    @gen_test
    async def test_list_files_handler_empty(self, mock_list_files, mock_prepare, mock_current_user):
        """Test list files handler when no files are available for download."""
        url = "/hydroshare/list_files"
        await self.run_test(
            url=url,
            mock_function=mock_list_files,
            mock_return_value={
                "resource_id": "test_resource_id",
                "available_files": []
            },
            mock_current_user=mock_current_user,
            mock_prepare=mock_prepare,
            body={"resource_id": "test_resource_id"},
        )

    @patch("jupyter_server.base.handlers.JupyterHandler.current_user", new_callable=PropertyMock)
    @patch("jupyter_server.base.handlers.JupyterHandler.prepare", new_callable=CoroutineMock)
    @patch("hsfiles_jupyter.handlers.list_available_files_for_download", new_callable=CoroutineMock)
    @gen_test
    async def test_list_files_handler_error(self, mock_list_files, mock_prepare, mock_current_user):
        """Test error handling in the list files handler."""
        url = "/hydroshare/list_files"
        mock_current_user.return_value = "test_user"
        mock_prepare.return_value = None
        mock_list_files.return_value = {"error": "Authentication error"}

        response = await self.http_client.fetch(
            self.get_url(url),
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"resource_id": "invalid_resource_id"}),
        )

        assert response.code == 200
        assert json.loads(response.body) == {"response": {"error": "Authentication error"}}
