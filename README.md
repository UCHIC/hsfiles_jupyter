# hsfiles_jupyter

A JupyterLab extension for managing HydroShare resource files in JupyterLab. This extension assumes that the user has loaded a HydroShare resource to a JupyterHub environment using the 'Open with' functionality in HydroShare.

## Features

1. **Upload Fileto HydroShare** - Upload local files from your JupyterLab workspace directly to a HydroShare resource. This allows you to add new files or update existing files in your HydroShare resource without leaving the JupyterLab environment.

2. **Refresh with File from HydroShare** - Download and synchronize files from your HydroShare resource to your local JupyterLab workspace. This ensures you have the latest version of files from HydroShare in your local environment.

3. **Delete File in HydroShare** - Remove files from your HydroShare resource directly from the JupyterLab file browser. This provides a convenient way to manage and clean up files in your HydroShare resource.

4. **Check Status of File in HydroShare** - Compare local files with their corresponding versions in HydroShare to see if there are differences. This helps you identify which files have been modified locally or remotely and need synchronization.

5. **Download from HydroShare** - Download specific files from your HydroShare resource to your local JupyterLab workspace. This is useful when you want to retrieve individual files without syncing the entire resource. This menu option is available when you are inside the resource id folder or any subfolder of the resource id folder in the JupyterLab file browser. When you select this option, you will be presented with a list of files available for download from HydroShare. Select the file you want to download and click on the 'Download' button. This file list consits of files that are available in HydroShare and not downloaded locally yet.

All these operations are accessible through right-click context menu options in the JupyterLab file browser, providing seamless integration between your local JupyterLab environment and HydroShare resources.

**NOTE:** The HydroShare specific file menu options are only available when you are inside a HydroShare resource folder in the JupyterLab file browser where the resource was downloaded using the 'Open with' functionality in HydroShare. This extension depends on env variable `JUPYTER_DOWNLOADS` to determine the download directory. If this env variable is not set, the default download directory is `Downloads`.

## Installation in JupyterHub/JupyterLab

```python
# Create and activate python environment, requires python >= 3.9

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip

# Install
python3 -m pip install hsfiles_jupyter

# Link extension to JupyterLab
python3 -m hsfiles_jupyter

# Launch JupyterLab and access the functionality of this extension from the JupyterLab file browser menu!
python3 -m jupyter lab
```

## Setup for Development

1. Clone the repository: `git clone https://github.com/UCHIC/hsfiles_jupyter.git`
2. Navigate to the project root directory: `cd hsfiles_jupyter`
3. Create a branch: `git checkout -b my-branch`
4. Create a virtual environment: `python3 -m venv .venv`
5. Activate the virtual environment: `source .venv/bin/activate`
6. Install dependencies using `pip install -e .[dev]`

### Frontend

1. Navigate to the `frontend` directory.
2. Run `npm install` to install dependencies.
3. Run `npm run build` to compile the TypeScript code.
4. Run `jupyter lab build` to build the frontend assets.
5. Run `jupyter labextension install .` to install the extension.

### Backend

1. Navigate to the `hsfiles_jupyter` directory (project root).
2. Run `python3 -m hsfiles_jupyter` to link extension to JupyterLab.

### Usage

1. Setup a notebook dir to be used as the root directory in JupyterLab. Example: ~/Documents/hsfiles_jupyter

   1.1. Create a directory called "Downloads"  under the notebook root directory. Example: ~/Documents/hsfiles_jupyter/Downloads

   1.2. Download a HydroShare resource that you own and extract the contents to the "Downloads" directory.

2. Export your HydroShare credentials as environment variables. This is needed for local development only:

```shell
export HS_USER=your_hydroshare_username
export HS_PASS=your_hydroshare_password
```

3. Start JupyterLab: `jupyter lab --debug --notebook-dir=~/Documents/hsfiles_jupyter`

4. This will open the JupyterLab in browser. Open the "Downloads" directory in the file browser and navigate to data/contents folder, and you should see the contents of the resource your downloaded. Right-click on any of the resource files, and you should see HydroShare specific file action menu options".

### Create distribution package to publish to PyPI

1. Clone the repository: `git clone https://github.com/hydroshare/hsfiles_jupyter.git`
2. Navigate to the project root directory: `cd hsfiles_jupyter`
3. Checkout the main branch: `git checkout -b main origin/main`
4. Create a virtual environment: `python3 -m venv .venv`
5. Activate the virtual environment: `source .venv/bin/activate`
6. Install dependencies using `pip install .[dev]`
7. Navigate to frontend directory: `cd frontend`
8. Run `npm install` to install dependencies.
9. Run `npm run build` to compile the TypeScript code.
10. Navigate to the project root directory: `cd ..`
11. Run `python3 -m build` to create the distribution package.
12. Run `twine upload dist/*` to publish the package to PyPI.
