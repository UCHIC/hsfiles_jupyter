from unittest.mock import MagicMock, patch

import pytest

from hsfiles_jupyter.check_file_status import check_file_status
from hsfiles_jupyter.utils import HydroShareAuthError


@pytest.mark.asyncio
async def test_check_file_status_exists_identical():
    """Test checking file status when file exists in HydroShare and is identical."""
    file_path = "Downloads/15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.check_file_status.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info
        mock_res_info = MagicMock()
        mock_res_info.resource_id = "15723969f1d7494883ef5ad5845aac5f"
        mock_res_info.hs_file_path = "example.txt"
        mock_res_info.hs_file_relative_path = "example.txt"

        # Create a mock file with a checksum
        mock_file = MagicMock()
        mock_file.checksum = "abc123"
        # Make the mock file behave like a string for equality comparison
        mock_file.__eq__ = lambda self, other: other == mock_res_info.hs_file_relative_path
        mock_res_info.files = [mock_file]  # File exists in HydroShare

        mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

        # Mock compute_checksum to return the same checksum
        mock_rfc_manager.compute_checksum.return_value = "abc123"

        # Call the function
        result = await check_file_status(file_path)

        # Verify the result
        assert "success" in result
        assert mock_res_info.resource_id in result["success"]
        assert mock_res_info.hs_file_path in result["success"]
        assert result["status"] == "Exists in HydroShare and they are identical"

        # Verify the mocks were called correctly
        mock_rfc_manager.get_hydroshare_resource_info.assert_called_once_with(file_path)
        mock_rfc_manager.compute_checksum.assert_called_once_with(file_path)


@pytest.mark.asyncio
async def test_check_file_status_exists_different():
    """Test checking file status when file exists in HydroShare but is different."""
    file_path = "Downloads/15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.check_file_status.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info
        mock_res_info = MagicMock()
        mock_res_info.resource_id = "15723969f1d7494883ef5ad5845aac5f"
        mock_res_info.hs_file_path = "example.txt"
        mock_res_info.hs_file_relative_path = "example.txt"

        # Create a mock file with a checksum
        mock_file = MagicMock()
        mock_file.checksum = "abc123"
        # Make the mock file behave like a string for equality comparison
        mock_file.__eq__ = lambda self, other: other == mock_res_info.hs_file_relative_path
        mock_res_info.files = [mock_file]  # File exists in HydroShare

        mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

        # Mock compute_checksum to return a different checksum
        mock_rfc_manager.compute_checksum.return_value = "def456"

        # Call the function
        result = await check_file_status(file_path)

        # Verify the result
        assert "success" in result
        assert mock_res_info.resource_id in result["success"]
        assert mock_res_info.hs_file_path in result["success"]
        assert result["status"] == "Exists in HydroShare but they are different"

        # Verify the mocks were called correctly
        mock_rfc_manager.get_hydroshare_resource_info.assert_called_once_with(file_path)
        mock_rfc_manager.compute_checksum.assert_called_once_with(file_path)


@pytest.mark.asyncio
async def test_check_file_status_exists_no_checksum():
    """Test checking file status when file exists in HydroShare but without checksum comparison."""
    file_path = "Downloads/15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.check_file_status.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info
        mock_res_info = MagicMock()
        mock_res_info.resource_id = "15723969f1d7494883ef5ad5845aac5f"
        mock_res_info.hs_file_path = "example.txt"
        mock_res_info.hs_file_relative_path = "example.txt"
        # In this test, we'll use an empty files list and mock the refresh path
        mock_res_info.files = []
        mock_res_info.refresh = False
        mock_res_info.resource = MagicMock()
        mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

        # Mock get_files to return a list containing our file
        mock_rfc_manager.get_files.return_value = (["example.txt"], True)

        # Call the function
        result = await check_file_status(file_path)

        # Verify the result
        assert "success" in result
        assert mock_res_info.resource_id in result["success"]
        assert mock_res_info.hs_file_path in result["success"]
        assert result["status"] == "Exists in HydroShare"

        # Verify the mocks were called correctly
        mock_rfc_manager.get_hydroshare_resource_info.assert_called_once_with(file_path)
        mock_rfc_manager.get_files.assert_called_once_with(mock_res_info.resource, refresh=True)


@pytest.mark.asyncio
async def test_check_file_status_not_exists():
    """Test checking file status when file does not exist in HydroShare."""
    file_path = "Downloads/15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.check_file_status.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info
        mock_res_info = MagicMock()
        mock_res_info.resource_id = "15723969f1d7494883ef5ad5845aac5f"
        mock_res_info.hs_file_path = "example.txt"
        mock_res_info.hs_file_relative_path = "example.txt"
        mock_res_info.files = []  # File doesn't exist in HydroShare
        mock_res_info.refresh = True  # Already refreshed
        mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

        # Call the function
        result = await check_file_status(file_path)

        # Verify the result
        assert "success" in result
        assert mock_res_info.resource_id in result["success"]
        assert mock_res_info.hs_file_path in result["success"]
        assert result["status"] == "Does not exist in HydroShare"

        # Verify the mocks were called correctly
        mock_rfc_manager.get_hydroshare_resource_info.assert_called_once_with(file_path)


@pytest.mark.asyncio
async def test_check_file_status_not_exists_with_refresh():
    """Test checking file status when file is not found in HydroShare, even after refreshing."""
    file_path = "Downloads/15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.check_file_status.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info
        mock_res_info = MagicMock()
        mock_res_info.resource_id = "15723969f1d7494883ef5ad5845aac5f"
        mock_res_info.hs_file_path = "example.txt"
        mock_res_info.hs_file_relative_path = "example.txt"
        mock_res_info.files = []  # File doesn't exist in HydroShare
        mock_res_info.refresh = False  # Not refreshed yet
        mock_res_info.resource = MagicMock()
        mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

        # Mock get_files to return a list not containing our file
        mock_rfc_manager.get_files.return_value = (["other_file.txt"], True)

        # Call the function
        result = await check_file_status(file_path)

        # Verify the result
        assert "success" in result
        assert mock_res_info.resource_id in result["success"]
        assert mock_res_info.hs_file_path in result["success"]
        assert result["status"] == "Does not exist in HydroShare"

        # Verify the mocks were called correctly
        mock_rfc_manager.get_hydroshare_resource_info.assert_called_once_with(file_path)
        mock_rfc_manager.get_files.assert_called_once_with(mock_res_info.resource, refresh=True)


@pytest.mark.asyncio
async def test_check_file_status_auth_error():
    """Test checking file status with authentication error."""
    file_path = "Downloads/15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"

    # Mock the ResourceFileCacheManager
    with patch("hsfiles_jupyter.check_file_status.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock get_hydroshare_resource_info to raise HydroShareAuthError
        mock_rfc_manager.get_hydroshare_resource_info.side_effect = HydroShareAuthError("Auth error")

        # Call the function
        result = await check_file_status(file_path)

        # Verify the result
        assert "error" in result
        assert "Auth error" in result["error"]


@pytest.mark.asyncio
async def test_check_file_status_file_not_in_download_dir_error():
    """Test checking file status with file not in download directory error."""
    # Use a file path that does NOT start with the expected download directory
    file_path = "tmp/Downloads/15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"

    # Mock the download directory to be different from the file path prefix
    with patch("hsfiles_jupyter.utils.get_hydroshare_resource_download_dir") as mock_get_download_dir:
        # File path starts with 'tmp/Downloads', so validation should fail
        mock_get_download_dir.return_value = "Downloads"

        # Call the function - this should trigger the validation error
        result = await check_file_status(file_path)

        # Verify the result contains an error due to path validation failure
        assert "error" in result
        assert "is not within the HydroShare download directory" in result["error"]
        assert "Downloads" in result["error"]  # Should mention the expected download directory
        assert file_path in result["error"]  # Should mention the problematic file path


@pytest.mark.asyncio
async def test_check_file_status_file_in_correct_download_dir():
    """Test checking file status when file IS in the correct download directory."""
    # Use a file path that DOES start with the expected download directory
    file_path = "Downloads/15723969f1d7494883ef5ad5845aac5f/data/contents/example.txt"

    # Mock the ResourceFileCacheManager to avoid actual HydroShare calls
    with patch("hsfiles_jupyter.check_file_status.ResourceFileCacheManager") as mock_rfc_manager_class:
        mock_rfc_manager = MagicMock()
        mock_rfc_manager_class.return_value = mock_rfc_manager

        # Mock the download directory to match the file path prefix
        with patch("hsfiles_jupyter.utils.get_hydroshare_resource_download_dir") as mock_get_download_dir:
            # File path starts with 'Downloads', so validation should pass
            mock_get_download_dir.return_value = "Downloads"

            # Mock get_hydroshare_resource_info to return a valid response
            mock_res_info = MagicMock()
            mock_res_info.resource_id = "15723969f1d7494883ef5ad5845aac5f"
            mock_res_info.hs_file_path = "example.txt"
            mock_res_info.hs_file_relative_path = "example.txt"
            mock_res_info.files = []  # File doesn't exist in HydroShare
            mock_res_info.refresh = True  # Already refreshed
            mock_rfc_manager.get_hydroshare_resource_info.return_value = mock_res_info

            # Call the function - this should NOT trigger a validation error
            result = await check_file_status(file_path)

            # Verify the result - should be a success response, not an error
            # This proves that path validation is working: correct path = no error
            assert "error" not in result
            assert "success" in result
