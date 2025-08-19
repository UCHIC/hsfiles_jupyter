import os

from .utils import (
    FileCacheUpdateType,
    HydroShareAuthError,
    ResourceFileCacheManager,
    get_local_absolute_file_path,
    logger,
)


async def refresh_file_from_hydroshare(file_path: str):
    """Download the file 'file_path' from HydroShare and replace the local file"""

    rfc_manager = ResourceFileCacheManager()
    try:
        res_info = rfc_manager.get_hydroshare_resource_info(file_path)
    except (HydroShareAuthError, ValueError) as e:
        return {"error": str(e)}

    # check file exists in HydroShare before trying to download it from HydroShare
    res_file = res_info.resource.file(path=res_info.hs_file_relative_path, search_aggregations=True)
    if res_file is None:
        err_msg = f"File {res_info.hs_file_path} is not found in HydroShare resource: {res_info.resource_id}"
        return {"error": err_msg}

    if res_file not in res_info.files:
        # update the files cache for the resource
        rfc_manager.update_resource_files_cache(
            resource=res_info.resource,
            res_file=res_file,
            update_type=FileCacheUpdateType.ADD
        )

    file_dir = os.path.dirname(file_path)
    downloaded_file_path = get_local_absolute_file_path(file_dir)

    try:
        res_info.resource.file_download(path=res_info.hs_file_relative_path, save_path=downloaded_file_path)
        success_msg = (
            f"File {res_info.hs_file_path} replaced successfully from" f" HydroShare resource: {res_info.resource_id}"
        )
        return {"success": success_msg}
    except Exception as e:
        hs_error = str(e)
        err_msg = (
            f"Failed to replace file: {res_info.hs_file_path} from HydroShare"
            f" resource: {res_info.resource_id}. Error: {hs_error}"
        )
        logger.error(err_msg)
        return {"error": err_msg}
