from jupyter_server.serverapp import ServerApp

try:
    from ._version import __version__
except ImportError:
    # Fallback when using the package in dev mode without installing
    # in editable mode with pip. It is highly recommended to install
    # the package from a stable release or in
    # editable mode: https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs
    import warnings

    warnings.warn("Importing 'hsfiles_jupyter' outside a proper installation.")
    __version__ = "dev"


_EXTENSION_NAME = "hsfiles_jupyter"


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": _EXTENSION_NAME}]


def _jupyter_server_extension_points():
    return [{"module": _EXTENSION_NAME}]


def _load_jupyter_server_extension(server_app: ServerApp):
    """Registers the API handler to receive HTTP requests from the frontend extension.

    Parameters
    ----------
    server_app: jupyterlab.labapp.LabApp
        JupyterLab application instance
    """
    from .handlers import setup_handlers

    setup_handlers(server_app.web_app)
    server_app.log.info(f"Registered {_EXTENSION_NAME} server extension")


load_jupyter_server_extension = _load_jupyter_server_extension
