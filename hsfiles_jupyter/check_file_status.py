from .utils import (
    HydroShareAuthError,
    ResourceFileCacheManager,
)


async def check_file_status(file_path: str):
    """Checks if the selected local file is also in Hydroshare and if they are identical"""

    rfc_manager = ResourceFileCacheManager()
    try:
        res_info = rfc_manager.get_hydroshare_resource_info(file_path)
    except HydroShareAuthError as e:
        return {"error": str(e)}

    success_response = {
        "success": f"File {res_info.hs_file_path} exists in HydroShare" f" resource: {res_info.resource_id}",
        "status": "Exists in HydroShare",
    }
    for res_file in res_info.files:
        if res_info.hs_file_relative_path == res_file:
            local_checksum = rfc_manager.compute_checksum(file_path)
            if local_checksum == res_file.checksum:
                success_response["status"] = "Exists in HydroShare and they are identical"
            else:
                success_response["status"] = "Exists in HydroShare but they are different"
            return success_response

    if not res_info.refresh:
        files, _ = rfc_manager.get_files(res_info.resource, refresh=True)
        if res_info.hs_file_relative_path in files:
            return success_response
    return {
        "success": f"File {res_info.hs_file_path} does not exist in HydroShare" f" resource: {res_info.resource_id}",
        "status": "Does not exist in HydroShare",
    }
