from .utils import (
    FileCacheUpdateType,
    HydroShareAuthError,
    ResourceFileCacheManager,
)


async def check_file_status(file_path: str):
    """Checks if the selected local file is also in Hydroshare and if they are identical"""

    rfc_manager = ResourceFileCacheManager()
    try:
        res_info = rfc_manager.get_hydroshare_resource_info(file_path)
    except (HydroShareAuthError, ValueError) as e:
        return {"error": str(e)}

    success_response = {
        "success": f"File {res_info.hs_file_path} exists in HydroShare resource: {res_info.resource_id}",
        "status": "Exists in HydroShare",
    }

    # check file exists in HydroShare
    res_file = res_info.resource.file(path=res_info.hs_file_relative_path, search_aggregations=True)
    if res_file is None:
        return {
        "success": f"File {res_info.hs_file_path} does not exist in HydroShare resource: {res_info.resource_id}",
        "status": "Does not exist in HydroShare",
    }

    if res_file not in res_info.files:
        # update the files cache for the resource
        rfc_manager.update_resource_files_cache(
            resource=res_info.resource,
            res_file=res_file,
            update_type=FileCacheUpdateType.ADD
        )

    local_checksum = rfc_manager.compute_checksum(file_path)
    if local_checksum == res_file.checksum:
        success_response["status"] = "Exists in HydroShare and they are identical"
    else:
        success_response["status"] = "Exists in HydroShare but they are different"
    return success_response
