import os

from setuptools import find_packages, setup

HERE = os.path.abspath(os.path.dirname(__file__))

PKG_NAME = "hsfiles_jupyter"

# path to pre-built lab-extension - used during development only
LABEXTENSION_PATH = os.path.join(HERE, PKG_NAME, "labextension")

setup(
    name=PKG_NAME,
    version="0.2.1",
    author="Pabitra Dash",
    author_email="pabitra.dash@usu.edu",
    description="A JupyterLab extension to manage HydroShare resource files in JupyterLab",
    long_description=open(os.path.join(HERE, "README.md")).read(),
    long_description_content_type="text/markdown",
    url="https://github.com/hydroshare/hsfiles_jupyter",
    license="BSD-3-Clause",
    packages=find_packages(
        include=["hsfiles_jupyter", "hsfiles_jupyter.*"],
        exclude=["hsfiles_jupyter.labextension", "hsfiles_jupyter.labextension.*"]
    ),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.9",
    install_requires=[
        "hsclient>=1.1.6",
        "jupyterlab==4.3.*",
        "jupyter_server>=2.13,<3",
    ],
    extras_require={
        "dev": [
            "build",
            "setuptools",
            "wheel",
            "twine",
            "pytest",
            "pytest-asyncio",
            "asynctest",
            "tornado"
        ]
    },
    include_package_data=True,
    package_data={"hsfiles_jupyter": ["_version.py", "labextension/*", "labextension/static/*"]},
    data_files=[
        (
            "etc/jupyter/jupyter_server_config.d",
            ["jupyter-config/jupyter_server_config.d/hsfiles_jupyter.json"],
        ),
    ],
    zip_safe=False,
)
