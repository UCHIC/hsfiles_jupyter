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


class TestHandlers(AsyncHTTPTestCase):
    def get_app(self):
        return Application(
            [
                (r"/hydroshare/upload", UploadFileHandler),
                (r"/hydroshare/refresh", RefreshFileHandler),
                (r"/hydroshare/delete", DeleteFileHandler),
                (r"/hydroshare/status", CheckFileStatusHandler),
            ],
            cookie_secret="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            xsrf_cookies=False,
        )

    async def run_test(self, url, mock_function, mock_return_value, mock_current_user, mock_prepare):
        mock_current_user.return_value = "test_user"
        mock_prepare.return_value = None
        mock_function.return_value = mock_return_value
        response = await self.http_client.fetch(
            self.get_url(url),
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"path": "test_file_path"}),
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
