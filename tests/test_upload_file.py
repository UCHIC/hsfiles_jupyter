from unittest.mock import MagicMock, patch

import pytest
from hsclient.hydroshare import File

from hsfiles_jupyter.upload_file import upload_file_to_hydroshare
from hsfiles_jupyter.utils import FileCacheUpdateType, HydroShareAuthError


@pytest.mark.asyncio
async def test_upload_file_to_hydroshare_success():
    """Test successful file upload to HydroShare."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    res_file_path = f"{resource_id}/data/contents/example.txt"
    res_file_url_path = f"https://www.hydroshare.org/resource/{res_file_path}"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.upload_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info
        mock_res_info = MagicMock()
        mock_res_info.resource_id = resource_id
        mock_res_info.hs_file_path = res_file_path
        mock_res_info.hs_file_relative_path = "example.txt"
        mock_res_info.files = []  # File doesn't exist in HydroShare yet
        mock_res_info.resource = MagicMock()

        # Mock resource.file() to return None initially (file doesn't exist yet)
        uploaded_file = File("example.txt", res_file_url_path, "abc123")
        mock_res_info.resource.file.side_effect = [None, uploaded_file]

        mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

        # Mock get_local_absolute_file_path
        with patch("hsfiles_jupyter.upload_file.get_local_absolute_file_path") as mock_get_path:
            mock_get_path.return_value = f"/user/jovyan/Downloads/{res_file_path}"

            # Mock file_upload
            mock_res_info.resource.file_upload = MagicMock()

            # Call the function
            result = await upload_file_to_hydroshare(res_file_path)

            # Verify the result
            assert "success" in result
            assert mock_res_info.resource_id in result["success"]
            assert mock_res_info.hs_file_path in result["success"]

            # Verify the mocks were called correctly
            mock_rfc_manager.get_hydroshare_resource_info.assert_called_once_with(res_file_path)
            mock_get_path.assert_called_once_with(res_file_path)
            mock_res_info.resource.file_upload.assert_called_once()
            mock_rfc_manager.update_resource_files_cache.assert_called_once_with(
                resource=mock_res_info.resource,
                res_file=uploaded_file,
                update_type=FileCacheUpdateType.ADD
            )


@pytest.mark.asyncio
async def test_upload_file_to_hydroshare_auth_error():
    """Test file upload with authentication error."""
    local_file_path = "15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.upload_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info to raise HydroShareAuthError
        mock_rfc_manager.get_hydroshare_resource_info.side_effect = HydroShareAuthError("Auth error")

        # Call the function
        result = await upload_file_to_hydroshare(local_file_path)

        # Verify the result
        assert "error" in result
        assert "Auth error" in result["error"]


@pytest.mark.asyncio
async def test_upload_file_to_hydroshare_file_exists():
    """Test file upload when file already exists in HydroShare."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    res_file_path = f"{resource_id}/data/contents/example.txt"
    res_file_url_path = f"https://www.hydroshare.org/resource/{res_file_path}"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.upload_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info
        mock_res_info = MagicMock()
        mock_res_info.resource_id = resource_id
        mock_res_info.hs_file_path = res_file_path
        mock_res_info.hs_file_relative_path = "example.txt"

        # Create File object for existing file
        existing_file = File("example.txt", res_file_url_path, "abc123")
        mock_res_info.files = [existing_file]  # File already exists in HydroShare
        mock_res_info.resource = MagicMock()

        # Mock resource.file() to return the existing File object
        mock_res_info.resource.file.return_value = existing_file

        mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

        # Call the function
        result = await upload_file_to_hydroshare(res_file_path)

        # Verify the result
        assert "error" in result
        assert "already exists" in result["error"]


@pytest.mark.asyncio
async def test_upload_file_to_hydroshare_upload_error():
    """Test file upload with an error during upload."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    res_file_path = f"{resource_id}/data/contents/example.txt"
    local_file_path = res_file_path

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.upload_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info
        mock_res_info = MagicMock()
        mock_res_info.resource_id = resource_id
        mock_res_info.hs_file_path = res_file_path
        mock_res_info.hs_file_relative_path = "example.txt"
        mock_res_info.files = []  # File doesn't exist in HydroShare yet
        mock_res_info.resource = MagicMock()

        # Mock resource.file() to return None (file doesn't exist yet)
        mock_res_info.resource.file.return_value = None

        mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

        # Mock get_local_absolute_file_path
        with patch("hsfiles_jupyter.upload_file.get_local_absolute_file_path") as mock_get_path:
            mock_get_path.return_value = f"/user/jovyan/Downloads/{res_file_path}"

            # Mock file_upload to raise an exception
            mock_res_info.resource.file_upload.side_effect = Exception("Upload failed")

            # Call the function
            result = await upload_file_to_hydroshare(local_file_path)

            # Verify the result
            assert "error" in result
            assert "Failed to upload file" in result["error"]
            assert "Upload failed" in result["error"]


@pytest.mark.asyncio
async def test_upload_file_to_hydroshare_file_not_in_download_dir_error():
    """Test file upload when file is not in the designated download directory."""
    file_path = "tmp/Downloads/15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"

    # Mock get_hydroshare_resource_download_dir to return "Downloads"
    with patch("hsfiles_jupyter.utils.get_hydroshare_resource_download_dir") as mock_download_dir:
        mock_download_dir.return_value = "Downloads"

        # Call the function (should get validation error)
        result = await upload_file_to_hydroshare(file_path)

        # Verify we get an error for path validation
        assert "error" in result
        assert "is not within the HydroShare download directory" in result["error"]


@pytest.mark.asyncio
async def test_upload_file_to_hydroshare_file_in_correct_download_dir():
    """Test file upload when file is in the correct download directory."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    res_file_path = f"{resource_id}/data/contents/example.txt"
    res_file_url_path = f"https://www.hydroshare.org/resource/{res_file_path}"
    local_file_path = res_file_path

    # Mock get_hydroshare_resource_download_dir to return "Downloads"
    with patch("hsfiles_jupyter.utils.get_hydroshare_resource_download_dir") as mock_download_dir:
        mock_download_dir.return_value = "Downloads"

        # Mock the ResourceFileCacheManager
        with patch("hsfiles_jupyter.upload_file.ResourceFileCacheManager") as mock_rfc_manager_class:
            mock_rfc_manager = MagicMock()
            mock_rfc_manager_class.return_value = mock_rfc_manager

            # Mock get_hydroshare_resource_info - should pass validation
            mock_res_info = MagicMock()
            mock_res_info.resource_id = resource_id
            mock_res_info.hs_file_path = res_file_path
            mock_res_info.hs_file_relative_path = "example.txt"
            mock_res_info.files = []  # File doesn't exist in HydroShare yet
            mock_res_info.resource = MagicMock()
            mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

            # Mock get_local_absolute_file_path
            with patch("hsfiles_jupyter.upload_file.get_local_absolute_file_path") as mock_get_path:
                mock_get_path.return_value = f"/user/jovyan/Downloads/{res_file_path}"

                # Mock file_upload
                mock_res_info.resource.file_upload = MagicMock()

                # Create File object for after upload
                uploaded_file = File(
                    "example.txt",
                    res_file_url_path,
                    "abc123"
                )

                # Mock resource.file() to return None first (doesn't exist), then the File object after upload
                mock_res_info.resource.file.side_effect = [None, uploaded_file]

                # Call the function
                result = await upload_file_to_hydroshare(local_file_path)

                # Verify we get success (not a validation error)
                assert "success" in result
                assert mock_res_info.resource_id in result["success"]
                assert mock_res_info.hs_file_path in result["success"]

                # Verify the mocks were called correctly
                mock_rfc_manager.get_hydroshare_resource_info.assert_called_once_with(local_file_path)
                mock_get_path.assert_called_once_with(local_file_path)
                mock_res_info.resource.file_upload.assert_called_once()
                mock_rfc_manager.update_resource_files_cache.assert_called_once_with(
                    resource=mock_res_info.resource,
                    res_file=uploaded_file,
                    update_type=FileCacheUpdateType.ADD
                )
