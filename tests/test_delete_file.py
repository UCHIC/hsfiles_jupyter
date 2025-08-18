from unittest.mock import MagicMock, patch

import pytest
from hsclient.hydroshare import File

from hsfiles_jupyter.delete_file import delete_file_from_hydroshare
from hsfiles_jupyter.utils import FileCacheUpdateType, HydroShareAuthError


@pytest.mark.asyncio
async def test_delete_file_from_hydroshare_success():
    """Test successful file deletion from HydroShare."""
    res_file_path = "15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"
    res_url_path = f"https://www.hydroshare.org/resource/{res_file_path}"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.delete_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info
        mock_res_info = MagicMock()
        mock_res_info.resource_id = "15723969f1d7494883ef5ad5845aac5f"
        mock_res_info.hs_file_path = f"{res_file_path}"
        mock_res_info.hs_file_relative_path = "example.txt"

        # Create an actual File object
        mock_file = File("example.txt", res_url_path, "abc123")
        mock_res_info.files = [mock_file]  # File exists in cache

        mock_res_info.resource = MagicMock()
        mock_res_info.refresh = False
        mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

        # Call the function
        result = await delete_file_from_hydroshare(res_file_path)

        # Verify the result
        assert "success" in result
        assert mock_res_info.resource_id in result["success"]
        assert mock_res_info.hs_file_path in result["success"]

        # Verify the mocks were called correctly
        mock_rfc_manager.get_hydroshare_resource_info.assert_called_once_with(res_file_path)
        mock_res_info.resource.file_delete.assert_called_once_with(mock_file)
        mock_rfc_manager.update_resource_files_cache.assert_called_once_with(
            resource=mock_res_info.resource,
            res_file=mock_file,
            update_type=FileCacheUpdateType.DELETE
        )


@pytest.mark.asyncio
async def test_delete_file_from_hydroshare_auth_error():
    """Test file deletion with authentication error."""
    file_path = "Downloads/15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.delete_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info to raise HydroShareAuthError
        mock_rfc_manager.get_hydroshare_resource_info.side_effect = HydroShareAuthError("Auth error")

        # Call the function
        result = await delete_file_from_hydroshare(file_path)

        # Verify the result
        assert "error" in result
        assert "Auth error" in result["error"]


@pytest.mark.asyncio
async def test_delete_file_from_hydroshare_file_not_found():
    """Test file deletion when file is not found in HydroShare."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    res_file_path = f"{resource_id}/data/contents/example.txt"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.delete_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info
        mock_res_info = MagicMock()
        mock_res_info.resource_id = resource_id
        mock_res_info.hs_file_path = res_file_path
        mock_res_info.hs_file_relative_path = "example.txt"
        mock_res_info.files = []  # File doesn't exist in HydroShare
        mock_res_info.refresh = True  # Already refreshed

        # Mock resource.file() to return None (file not found)
        mock_res_info.resource.file.return_value = None

        mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

        # Call the function
        result = await delete_file_from_hydroshare(res_file_path)

        # Verify the result
        assert "error" in result
        assert "doesn't exist" in result["error"]


@pytest.mark.asyncio
async def test_delete_file_from_hydroshare_file_not_found_with_refresh():
    """Test file deletion when file is not found in HydroShare, even after refreshing."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    res_file_path = f"{resource_id}/data/contents/example.txt"
    res_url_path = f"https://www.hydroshare.org/resource/{res_file_path}"
    file_path = f"Downloads/{res_file_path}"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.delete_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info
        mock_res_info = MagicMock()
        mock_res_info.resource_id = resource_id
        mock_res_info.hs_file_path = res_file_path
        mock_res_info.hs_file_relative_path = "example.txt"
        mock_res_info.files = []  # File doesn't exist in HydroShare
        mock_res_info.refresh = False  # Not refreshed yet
        mock_res_info.resource = MagicMock()

        # Mock resource.file() to return None (file not found)
        mock_res_info.resource.file.return_value = None

        mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

        # Mock get_files to return a list not containing our file
        mock_file = File("example.txt", res_url_path, "xyz789")
        mock_rfc_manager.get_files.return_value = ([mock_file], True)

        # Call the function
        result = await delete_file_from_hydroshare(file_path)

        # Verify the result
        assert "error" in result
        assert "doesn't exist" in result["error"]


@pytest.mark.asyncio
async def test_delete_file_from_hydroshare_delete_error():
    """Test file deletion with an error during deletion."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    res_file_path = f"{resource_id}/data/contents/example.txt"
    res_url_path = f"https://www.hydroshare.org/resource/{res_file_path}"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.delete_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info
        mock_res_info = MagicMock()
        mock_res_info.resource_id = resource_id
        mock_res_info.hs_file_path = res_file_path
        mock_res_info.hs_file_relative_path = "example.txt"

        # Create an actual File object
        mock_file = File("example.txt", res_url_path, "abc123")
        mock_res_info.files = [mock_file]  # File exists in cache

        mock_res_info.resource = MagicMock()
        mock_res_info.refresh = False
        mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

        # Mock file_delete to raise an exception
        mock_res_info.resource.file_delete.side_effect = Exception("Delete failed")

        # Call the function
        result = await delete_file_from_hydroshare(res_file_path)

        # Verify the result
        assert "error" in result
        assert "Failed to delete file" in result["error"]
        assert "Delete failed" in result["error"]


@pytest.mark.asyncio
async def test_delete_file_from_hydroshare_file_not_in_download_dir_error():
    """Test file deletion when file is not in the designated download directory."""
    local_file_path = "tmp/Downloads/15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"

    # Mock get_hydroshare_resource_download_dir to return "Downloads"
    with patch("hsfiles_jupyter.utils.get_hydroshare_resource_download_dir") as mock_download_dir:
        mock_download_dir.return_value = "Downloads"

        # Call the function (should get validation error)
        result = await delete_file_from_hydroshare(local_file_path)

        # Verify we get an error for path validation
        assert "error" in result
        assert "is not within the HydroShare download directory" in result["error"]


@pytest.mark.asyncio
async def test_delete_file_from_hydroshare_file_in_correct_download_dir():
    """Test file deletion when file is in the correct download directory."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    res_file_path = f"{resource_id}/data/contents/test_folder/example.txt"
    res_url_path = f"https://www.hydroshare.org/resource/{res_file_path}"
    local_file_path = f"Downloads/{res_file_path}"

    # Mock get_hydroshare_resource_download_dir to return "Downloads"
    with patch("hsfiles_jupyter.utils.get_hydroshare_resource_download_dir") as mock_download_dir:
        mock_download_dir.return_value = "Downloads"

        # Mock the ResourceFileCacheManager
        with patch("hsfiles_jupyter.delete_file.ResourceFileCacheManager") as mock_rfc_manager_class:
            mock_rfc_manager = MagicMock()
            mock_rfc_manager_class.return_value = mock_rfc_manager

            # Mock get_hydroshare_resource_info - should pass validation
            mock_res_info = MagicMock()
            mock_res_info.resource_id = resource_id
            mock_res_info.hs_file_path = res_file_path
            mock_res_info.hs_file_relative_path = "test_folder/example.txt"

            # Create an actual File object
            mock_file = File("test_folder/example.txt", res_url_path, "abc123")
            mock_res_info.files = [mock_file]  # File exists in cache

            mock_res_info.resource = MagicMock()
            mock_res_info.refresh = False
            mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

            # Call the function
            result = await delete_file_from_hydroshare(local_file_path)

            # Verify we get success (not a validation error)
            assert "success" in result
            assert mock_res_info.resource_id in result["success"]
            assert mock_res_info.hs_file_path in result["success"]

            # Verify the mocks were called correctly
            mock_rfc_manager.get_hydroshare_resource_info.assert_called_once_with(local_file_path)
            mock_res_info.resource.file_delete.assert_called_once_with(mock_file)
            mock_rfc_manager.update_resource_files_cache.assert_called_once_with(
                resource=mock_res_info.resource,
                res_file=mock_file,
                update_type=FileCacheUpdateType.DELETE
            )
