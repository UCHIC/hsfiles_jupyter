from unittest.mock import MagicMock, patch

import pytest
from hsclient.hydroshare import File

from hsfiles_jupyter.download_file import (
    download_file_from_hydroshare,
    list_available_files_for_download,
)
from hsfiles_jupyter.utils import FileCacheUpdateType, HydroShareAuthError


@pytest.mark.asyncio
async def test_download_file_from_hydroshare_success():
    """Test successful file download from HydroShare."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    file_path = "example.txt"
    res_file_url_path = f"https://www.hydroshare.org/resource/{resource_id}/data/contents/{file_path}"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.download_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock the resource
        mock_resource = MagicMock()
        mock_resource.resource_id = resource_id
        mock_rfc_manager.get_resource.return_value = mock_resource

        # Create File object for testing
        mock_file = File(file_path, f"{res_file_url_path}", "abc123")

        # Mock resource.file() to return the File object
        mock_resource.file.return_value = mock_file

        # Mock file_download as a regular mock (not async)
        mock_resource.file_download = MagicMock()

        # Mock get_hydroshare_resource_download_dir to return the Downloads directory path
        with patch("hsfiles_jupyter.download_file.get_hydroshare_resource_download_dir") as mock_get_download_dir:
            mock_get_download_dir.return_value = "/tmp/Downloads"

            # Mock os.path.exists to return True for directory existence checks
            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = True

                # Mock os.makedirs
                with patch("os.makedirs") as mock_makedirs:
                    # Mock get_local_absolute_file_path
                    with patch("hsfiles_jupyter.download_file.get_local_absolute_file_path") as mock_get_path:
                        mock_get_path.return_value = f"/tmp/Downloads/{resource_id}/data/contents/{file_path}"

                        # Call the function
                        result = await download_file_from_hydroshare(
                            resource_id=resource_id,
                            hs_file_path=file_path,
                            base_path=mock_get_download_dir.return_value
                        )

                        # Verify the result
                        assert "success" in result
                        assert resource_id in result["success"]
                        assert file_path in result["success"]

                        # Verify the mocks were called correctly
                        mock_rfc_manager.get_resource.assert_called_once_with(resource_id)
                        mock_resource.file.assert_called_once_with(path=file_path, search_aggregations=True)
                        mock_resource.file_download.assert_called_once()
                        mock_makedirs.assert_called_once()

                        # Verify that the cache was updated
                        mock_rfc_manager.update_resource_files_cache.assert_called_once_with(
                            resource=mock_resource,
                            res_file=mock_file,
                            update_type=FileCacheUpdateType.ADD
                        )


@pytest.mark.asyncio
async def test_download_file_from_hydroshare_auth_error():
    """Test file download with authentication error."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    file_path = "example.txt"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.download_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_resource to raise HydroShareAuthError
        mock_rfc_manager.get_resource.side_effect = HydroShareAuthError("Auth error")

        # Call the function
        result = await download_file_from_hydroshare(
            resource_id=resource_id,
            hs_file_path=file_path,
            base_path="Downloads"
        )

        # Verify the result
        assert "error" in result
        assert "Auth error" in result["error"]


@pytest.mark.asyncio
async def test_download_file_from_hydroshare_file_not_found():
    """Test file download when file is not found in HydroShare."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    file_path = "nonexistent.txt"
    res_file_url_path = f"https://www.hydroshare.org/resource/{resource_id}/data/contents/{file_path}"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.download_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock the resource
        mock_resource = MagicMock()
        mock_resource.resource_id = resource_id
        mock_rfc_manager.get_resource.return_value = mock_resource

         # Create File object for other file (not the one we're looking for)
        other_file = File("other_file.txt", res_file_url_path, "def456")

        # Mock get_files to return a list not containing our file
        mock_rfc_manager.get_files.return_value = ([other_file], True)

        # Mock resource.file() to return None (file not found)
        mock_resource.file.return_value = None

        # Mock get_hydroshare_resource_download_dir to return the Downloads directory path
        with patch("hsfiles_jupyter.download_file.get_hydroshare_resource_download_dir") as mock_get_download_dir:
            mock_get_download_dir.return_value = "/tmp/Downloads"

            # Call the function
            result = await download_file_from_hydroshare(
                resource_id=resource_id,
                hs_file_path=file_path,
                base_path=mock_get_download_dir.return_value
            )

            # Verify the result
            assert "error" in result
            assert "not found" in result["error"]

@pytest.mark.asyncio
async def test_download_file_from_outside_download_dir_fails():
    """Test file download from outside the HydroShare download directory should fail."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    file_path = "example.txt"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.download_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_download_dir to return the Downloads directory path
        with patch("hsfiles_jupyter.download_file.get_hydroshare_resource_download_dir") as mock_get_download_dir:
            mock_get_download_dir.return_value = "/tmp/Downloads"

            # Mock os.path.exists to return True for directory existence checks
            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = True

                # Call the function
                result = await download_file_from_hydroshare(
                    resource_id=resource_id,
                    hs_file_path=file_path,
                    base_path="/tmp/OtherDir"
                )

                # Verify the result
                assert "error" in result
                assert "Select the option to download from within the resource id folder in the HydroShare download"
                " directory." in result["error"]


@pytest.mark.asyncio
async def test_list_available_files_for_download():
    """Test listing files available for download."""
    resource_id = "15723969f1d7494883ef5ad5845aac5f"
    res_file_base_url = f"https://www.hydroshare.org/resource/{resource_id}/data/contents/"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.download_file.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock the resource
        mock_resource = MagicMock()
        mock_resource.resource_id = resource_id
        mock_rfc_manager.get_resource.return_value = mock_resource

        # Create File objects for testing
        file1 = File("file1.txt", f"{res_file_base_url}file1.txt", "abc123")
        file2 = File("file2.txt", f"{res_file_base_url}file2.txt", "def456")
        file3 = File("file3.txt", f"{res_file_base_url}file3.txt", "ghi789")
        remote_files = [file1, file2, file3]

        # Mock get_files to return a list of File objects
        mock_rfc_manager.get_files.return_value = (remote_files, True)

        # Mock get_hydroshare_resource_download_dir to return the Downloads directory path
        with patch("hsfiles_jupyter.download_file.get_hydroshare_resource_download_dir") as mock_get_download_dir:
            mock_get_download_dir.return_value = "/tmp/Downloads"

            # Mock os.path.exists and os.walk to simulate some files already downloaded
            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = True

                with patch("os.walk") as mock_walk:
                    mock_walk.return_value = [
                        ("/tmp/path", [], ["file1.txt"]),  # file1.txt already exists locally
                    ]

                    # Mock get_local_absolute_file_path
                    with patch("hsfiles_jupyter.download_file.get_local_absolute_file_path") as mock_get_path:
                        mock_get_path.return_value = "/tmp/path"

                        # Call the function
                        result = await list_available_files_for_download(
                            resource_id=resource_id,
                            base_path=mock_get_download_dir.return_value
                        )

                        # Verify the result
                        assert "resource_id" in result
                        assert result["resource_id"] == resource_id
                        assert "available_files" in result
                        assert "file1.txt" not in result["available_files"]  # Should be filtered out
                        assert "file2.txt" in result["available_files"]
                        assert "file3.txt" in result["available_files"]
