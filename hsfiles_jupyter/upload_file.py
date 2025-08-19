import os

from .utils import (
    HydroShareAuthError,
    ResourceFileCacheManager,
    get_local_absolute_file_path,
    logger,
)


async def upload_file_to_hydroshare(file_path: str):
    """Uploads a file 'file_path' to a HydroShare resource"""

    rfc_manager = ResourceFileCacheManager()
    try:
        res_info = rfc_manager.get_hydroshare_resource_info(file_path)
    except HydroShareAuthError as e:
        return {"error": str(e)}
    if res_info.hs_file_relative_path in res_info.files:
        err_msg = f"File {res_info.hs_file_path} already exists in HydroShare resource: {res_info.resource_id}"
        return {"error": err_msg}

    file_folder = os.path.dirname(res_info.hs_file_relative_path)
    absolute_local_file_path = get_local_absolute_file_path(file_path)

    try:
        res_info.resource.file_upload(absolute_local_file_path, destination_path=file_folder)
        rfc_manager.refresh_files_cache(res_info.resource)
        success_msg = (
            f"File {res_info.hs_file_path} uploaded successfully to HydroShare" f" resource: {res_info.resource_id}"
        )
        return {"success": success_msg}
    except Exception as e:
        hs_error = str(e)
        if "already exists" in hs_error:
            err_msg = f"File {res_info.hs_file_path} already exists in HydroShare resource: {res_info.resource_id}"
            return {"error": err_msg}
        err_msg = (
            f"Failed to upload file: {res_info.hs_file_path} to HydroShare resource: {res_info.resource_id}."
            f" Error: {hs_error}"
        )
        logger.error(err_msg)
        return {"error": err_msg}
