from .utils import (
    FileCacheUpdateType,
    HydroShareAuthError,
    ResourceFileCacheManager,
    logger,
)


async def delete_file_from_hydroshare(file_path: str):
    """
    Deletes a file 'file_path' from HydroShare resource.
    """
    rfc_manager = ResourceFileCacheManager()
    try:
        res_info = rfc_manager.get_hydroshare_resource_info(file_path)
    except (HydroShareAuthError, ValueError) as e:
        return {"error": str(e)}

    hs_file_to_delete = None
    # first check if the file is in the cache
    for res_file in res_info.files:
        if res_info.hs_file_relative_path == res_file.path:
            hs_file_to_delete = res_file
            break

    if hs_file_to_delete is None:
        # check if file exists in HydroShare
        hs_file_to_delete = res_info.resource.file(path=res_info.hs_file_relative_path, search_aggregations=True)
        if hs_file_to_delete is None:
            err_msg = f"File {res_info.hs_file_path} doesn't exist in HydroShare resource: {res_info.resource_id}"
            return {"error": err_msg}

    try:
        # deleting the file from HydroShare
        res_info.resource.file_delete(hs_file_to_delete)

        # update the files cache for the resource
        rfc_manager.update_resource_files_cache(
            resource=res_info.resource,
            res_file=hs_file_to_delete,
            update_type=FileCacheUpdateType.DELETE
        )
    except Exception as e:
        hs_error = str(e)
        err_msg = (
            f"Failed to delete file: {res_info.hs_file_path} from HydroShare"
            f" resource: {res_info.resource_id}. Error: {hs_error}"
        )
        logger.error(err_msg)
        return {"error": err_msg}

    delete_success_msg = f"File {res_info.hs_file_path} was deleted from HydroShare resource: {res_info.resource_id}"
    return {"success": delete_success_msg}
