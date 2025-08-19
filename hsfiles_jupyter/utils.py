import hashlib
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import lru_cache
from logging.handlers import RotatingFileHandler
from pathlib import Path

from hsclient import HydroShare
from hsclient.hydroshare import Resource
from jupyter_server.serverapp import ServerApp
from requests.exceptions import ConnectionError

# Configure logging
log_file_path = Path.home() / ".hsfiles_jupyter.log"
handler = RotatingFileHandler(
    filename=log_file_path,
    maxBytes=1024 * 1024,  # 1 MB
    backupCount=3,  # Keep 3 backup files
    encoding="utf-8",
)
handler.setLevel(logging.ERROR)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
logger.addHandler(handler)


class HydroShareAuthError(Exception):
    """Exception raised for errors in the HydroShare authentication."""

    pass


class FileCacheUpdateType(Enum):
    ADD = 1
    DELETE = 2


@dataclass
class HydroShareResourceInfo:
    resource: Resource
    resource_id: str
    hs_file_path: str
    files: list
    refresh: bool
    hs_file_relative_path: str


class HydroShareWrapper:
    """A class to manage a HydroShare session."""

    # make this a singleton class
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance") or cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        username, password = get_credentials()
        self.username = username
        self.password = password
        self._user_logged_in = False
        self.hs = self._create_session()

    def _create_session(self):
        hs = HydroShare(username=self.username, password=self.password)
        self._user_logged_in = True
        return hs

    def user_logged_in(self):
        return self._user_logged_in

    def execute_with_retry(self, operation, max_retries=3):
        for attempt in range(max_retries):
            try:
                return operation()
            except ConnectionError:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)
                self.hs = self._create_session()  # Create new session

    def get_resource(self, resource_id):
        # this function is used to get the resource object from HydroShare using an active hydroshare client session
        # always use this function when there is a need to retrieve a resource object from hydroshare
        return self.execute_with_retry(lambda: self.hs.resource(resource_id))

    def update_resource_session(self, resource):
        # before we do any operation (api call) using the resource object, we need to make sure the hydroshare client
        # session for the resource is still active/valid - here we are using the my_user_info api call to check
        # if the session is still valid, otherwise we create a new session
        self.execute_with_retry(lambda: self.hs.my_user_info())
        resource._hs_session = self.hs._hs_session


@dataclass
class ResourceFilesCache:
    """A class to manage a file cache for files in a HydroShare resource."""

    _file_paths: list[str]
    _resource: Resource
    _refreshed_at: datetime = field(default_factory=datetime.now)

    def update_files_cache(self, file_path: str, update_type: FileCacheUpdateType) -> None:
        if update_type == FileCacheUpdateType.ADD:
            self._file_paths.append(file_path)
        elif update_type == FileCacheUpdateType.DELETE:
            self._file_paths.remove(file_path)

    def load_files_to_cache(self) -> None:
        # refresh resource hydroshare session only if 30 seconds have passed since last refresh
        if (datetime.now() - self._refreshed_at).total_seconds() > 30:
            HydroShareWrapper().update_resource_session(self._resource)
        self._resource.refresh()
        self._file_paths = self._resource.files(search_aggregations=True)
        self._refreshed_at = datetime.now()

    def get_files(self) -> list[str]:
        return self._file_paths

    def is_due_for_refresh(self) -> bool:
        refresh_interval = get_cache_refresh_interval()
        return (datetime.now() - self._refreshed_at).total_seconds() > refresh_interval

    @property
    def resource(self) -> Resource:
        return self._resource


class ResourceFileCacheManager:
    """A class to manage resource file caches for multiple HydroShare resources."""

    resource_file_caches: list[ResourceFilesCache] = []
    _instance: "ResourceFileCacheManager" = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance") or cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_hydroshare_resource_info(self, file_path: str) -> HydroShareResourceInfo:
        """Get HydroShare resource information for a given file path."""
        file_path = Path(file_path).as_posix()
        if not self.user_authorized():
            raise HydroShareAuthError("User is not authorized with HydroShare")
        resource = self.get_resource_from_file_path(file_path)

        resource_id = resource.resource_id
        hs_file_path = get_hs_file_path(file_path)

        # get all files in the resource to check if the file to be acted on already exists in the resource
        files, refresh = self.get_files(resource)
        hs_data_path = get_hs_resource_data_path(resource_id).as_posix() + "/"
        hs_file_relative_path = hs_file_path.split(hs_data_path, 1)[1]
        return HydroShareResourceInfo(
            resource=resource,
            resource_id=resource_id,
            hs_file_path=hs_file_path,
            files=files,
            refresh=refresh,
            hs_file_relative_path=hs_file_relative_path,
        )

    def user_authorized(self) -> bool:
        return HydroShareWrapper().user_logged_in()

    def create_resource_file_cache(self, resource: Resource) -> ResourceFilesCache:
        resource_file_cache = ResourceFilesCache(_file_paths=[], _resource=resource)
        self.resource_file_caches.append(resource_file_cache)
        resource_file_cache.load_files_to_cache()
        return resource_file_cache

    def get_resource_file_cache(self, resource: Resource) -> ResourceFilesCache:
        return next((rc for rc in self.resource_file_caches if rc.resource.resource_id == resource.resource_id), None)

    def get_files(self, resource: Resource, refresh=False) -> (list, bool):
        """Get a list of file paths in a HydroShare resource. If the cache is up to date, return the cached files."""

        resource_file_cache = self.get_resource_file_cache(resource)
        if resource_file_cache is None:
            rfc = self.create_resource_file_cache(resource)
            return rfc.get_files(), True

        if not refresh:
            refresh = resource_file_cache.is_due_for_refresh()
            if not refresh:
                # letting the caller know that the cache doesn't need to be refreshed - it's up to date
                return resource_file_cache.get_files(), True

        if refresh:
            resource_file_cache.load_files_to_cache()

        return resource_file_cache.get_files(), refresh

    def refresh_files_cache(self, resource: Resource) -> None:
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(self.get_files, resource, refresh=True)

    def get_resource(self, resource_id: str) -> Resource:
        resource = next(
            (rc.resource for rc in self.resource_file_caches if rc.resource.resource_id == resource_id), None
        )
        if resource is not None:
            return resource

        if not self.user_authorized():
            err_msg = "User is not authorized with HydroShare"
            raise HydroShareAuthError(err_msg)
        try:
            resource = HydroShareWrapper().get_resource(resource_id)
        except Exception as e:
            hs_err_msg = str(e)
            if "404" in hs_err_msg:
                err_msg = f"Resource with id {resource_id} was not found in Hydroshare"
            elif "403" in hs_err_msg:
                err_msg = f"You are not authorized to access this resource: {resource_id}"
            else:
                err_msg = f"Failed to get resource from Hydroshare with id {resource_id}"

            logger.error(f"{err_msg}. Error: {hs_err_msg}")
            raise ValueError(err_msg)
        self.create_resource_file_cache(resource)
        return resource

    def get_resource_from_file_path(self, file_path) -> Resource:
        file_path = Path(file_path).as_posix()
        resource_id = get_resource_id(file_path)
        resource = self.get_resource(resource_id)
        return resource

    def update_resource_files_cache(
        self, *, resource: Resource, file_path: str, update_type: FileCacheUpdateType
    ) -> None:
        resource_file_cache = self.get_resource_file_cache(resource)
        if resource_file_cache is not None:
            resource_file_cache.update_files_cache(file_path, update_type)
        else:
            # This should not happen
            err_msg = (
                f"Failed to update file list cache. Resource file cache was not found for "
                f"resource: {resource.resource_id}"
            )
            logger.error(err_msg)

    @classmethod
    def compute_checksum(cls, file_path: str):
        md5_hash = calculate_md5(file_path)
        return md5_hash


@lru_cache(maxsize=None)
def get_credentials() -> (str, str):
    """The Hydroshare user credentials files used here are created by nbfetch as part of resource
    open with Jupyter functionality, This extension depends on those files for user credentials."""

    username = os.getenv("HS_USER")
    password = os.getenv("HS_PASS")

    if username and password:
        return username, password

    home_dir = Path.home()
    user_file = home_dir / ".hs_user"
    pass_file = home_dir / ".hs_pass"

    for f in [user_file, pass_file]:
        if not os.path.exists(f):
            logger.error(f"User credentials file was not found: {f}")
            raise HydroShareAuthError("User credentials for HydroShare was not found")

    with open(user_file, "r") as uf:
        username = uf.read().strip()

    with open(pass_file, "r") as pf:
        password = pf.read().strip()

    return username, password


def get_resource_id(file_path: str) -> str:
    log_err_msg = f"Resource id was not found in selected file path: {file_path}"
    user_err_msg = "Invalid resource file path"
    if file_path.startswith("Downloads/"):
        res_id = file_path.split("/")[1]
        if len(res_id) != 32:
            logger.error(log_err_msg)
            raise ValueError(user_err_msg)
        return res_id

    logger.error(log_err_msg)
    raise ValueError(user_err_msg)


def get_hs_resource_data_path(resource_id: str) -> Path:
    hs_data_path = Path(resource_id) / "data" / "contents"
    return hs_data_path


@lru_cache(maxsize=None)
def get_notebook_dir() -> str:
    # Get the current server application instance
    server_app = ServerApp.instance()
    return server_app.root_dir


def get_local_absolute_file_path(file_path: str) -> str:
    notebook_root_dir = get_notebook_dir()
    return (Path(notebook_root_dir) / file_path).as_posix()


def get_hs_file_path(file_path: str) -> str:
    file_path = Path(file_path).as_posix()
    resource_id = get_resource_id(file_path)
    hs_file_path = file_path.split(resource_id, 1)[1]
    hs_file_path = hs_file_path.lstrip("/")
    # add resource id to the file path if it doesn't already start with it
    if not hs_file_path.startswith(resource_id):
        hs_file_path = (Path(resource_id) / hs_file_path).as_posix()
    return hs_file_path


@lru_cache(maxsize=None)
def get_cache_refresh_interval() -> int:
    return int(os.getenv("CACHE_REFRESH_INTERVAL", 180))


def calculate_md5(file_path):
    md5_hash = hashlib.md5()
    buffer_size = 8192  # Read in chunks of 8KB
    file_path = get_local_absolute_file_path(file_path)

    with open(file_path, "rb") as file:
        while chunk := file.read(buffer_size):
            md5_hash.update(chunk)

    return md5_hash.hexdigest()
