import os
from pathlib import Path

from jupyter_core.paths import ENV_JUPYTER_PATH
from jupyter_server.extension.serverextension import EnableServerExtensionApp

_ERROR_MESSAGE_PREFIX = "Fatal, cannot link labextension."

MODULE_DIR = Path(__file__).parent.resolve()
EXTENSION_NAME = "hsfiles_jupyter"
LABEXTENSION_PATH = MODULE_DIR / "labextension"


def enable_server_extension(extension_name: str):
    o = EnableServerExtensionApp()
    o.toggle_server_extension(extension_name)


def get_env_jupyter_path() -> Path:
    """Absolute path to Jupyter's ENV_JUPYTER_PATH.
    If multiple ENV_JUPYTER_PATH's are specified, the first is returned.
    """
    try:
        return Path(ENV_JUPYTER_PATH[0]).resolve()
    except IndexError as e:
        error_message = f"{_ERROR_MESSAGE_PREFIX} ENV_CONFIG_PATH not set."
        raise ValueError(error_message) from e


def link_prebuilt_labextension(labextension_name: str, labextension_prebuilt_files_dir: str):
    labextension_prebuilt_files_dir = Path(labextension_prebuilt_files_dir).resolve()

    # naively verify that labextension exists (does not verify contents of directory. i.e. package.json exists)
    if not labextension_prebuilt_files_dir.exists() or not labextension_prebuilt_files_dir.is_dir():
        error_message = (
            f"{_ERROR_MESSAGE_PREFIX} labextension_prebuilt_files_dir: "
            f"{labextension_prebuilt_files_dir} does not exist."
        )
        raise FileNotFoundError(error_message)

    labextensions_path = get_env_jupyter_path() / "labextensions"

    # create `labextensions` directory if it does not already exist. Create intermediate dirs if necessary
    labextensions_path.mkdir(exist_ok=True, parents=True)

    link_dir = labextensions_path / labextension_name

    # choose not to fail raise exception if link_dir exists.
    if link_dir.exists():
        if link_dir.is_symlink() and os.readlink(str(link_dir)) == str(labextension_prebuilt_files_dir):
            print(f"{labextension_prebuilt_files_dir} already linked to {link_dir}")
        else:
            print(
                (
                    f"Could not link {labextension_prebuilt_files_dir} to {link_dir}. "
                    f"{link_dir} already exists. Remove {link_dir} and reinstall."
                )
            )
    else:
        # note: target_is_directory True, required for windows support
        link_dir.symlink_to(labextension_prebuilt_files_dir, target_is_directory=True)

        print(f"{labextension_prebuilt_files_dir} linked to {link_dir}")


def configure_jupyter() -> None:
    # link lab extension to correct location and enable server extension
    link_prebuilt_labextension(EXTENSION_NAME, LABEXTENSION_PATH)
    enable_server_extension(EXTENSION_NAME)


if __name__ == "__main__":
    configure_jupyter()
