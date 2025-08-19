import {
    JupyterFrontEnd,
    JupyterFrontEndPlugin
} from '@jupyterlab/application';
import {FileBrowser, IFileBrowserFactory} from '@jupyterlab/filebrowser';
import {showDialog, Dialog, Spinner, MainAreaWidget} from '@jupyterlab/apputils';
import {ServerConnection} from '@jupyterlab/services';
import {URLExt} from '@jupyterlab/coreutils';
import {Widget} from '@lumino/widgets';
import { addIcon, downloadIcon, closeIcon, infoIcon } from '@jupyterlab/ui-components';

class SpinnerWidget extends Widget {
    constructor() {
        super();
        this.addClass('jp-SpinnerWidget');
        const spinner = new Spinner();
        this.node.appendChild(spinner.node);
    }
}

async function requestAPI<T>(url: string, init: RequestInit): Promise<T> {
    const settings = ServerConnection.makeSettings();
    const requestUrl = URLExt.join(settings.baseUrl, 'hydroshare', url);
    const response = await ServerConnection.makeRequest(requestUrl, init, settings);
    const data = await response.json();
    if (data.response.error) {
        throw new Error(data.response.error);
    }
    return data.response;
}

function disableFileBrowser(fileBrowser: FileBrowser) {
    fileBrowser.node.style.pointerEvents = 'none';
    fileBrowser.node.style.opacity = '0.5';
    console.log('File browser disabled');
}

function enableFileBrowser(fileBrowser: FileBrowser) {
    fileBrowser.node.style.pointerEvents = 'auto';
    fileBrowser.node.style.opacity = '1';
    console.log('File browser enabled');
}

async function handleCommand(
    app: JupyterFrontEnd,
    tracker: IFileBrowserFactory['tracker'],
    command: string,
    url: string,
    successTitle: string | ((response: any) => string),
    successMessage: (response: any) => string,
    extraData: any = {}
) {
    const widget = tracker.currentWidget;
    if (widget) {
        const selectedItem = widget.selectedItems().next();
        if (selectedItem && selectedItem.value) {
            const path = selectedItem.value.path;
            const fileBrowser = tracker.currentWidget;
            disableFileBrowser(fileBrowser);

            const content = new SpinnerWidget();
            const mainWidget = new MainAreaWidget({ content });
            mainWidget.id = `spinner-${command.replace(/\s+/g, '-')}`;
            mainWidget.title.label = 'Processing...';
            app.shell.add(mainWidget, 'main');
            app.shell.currentChanged;  // Wait for layout update
            content.node.style.display = 'block';

            try {
                const response = await requestAPI<any>(url, {
                    method: 'POST',
                    body: JSON.stringify({path, ...extraData}),
                });
                content.node.style.display = 'none';
                const title = typeof successTitle === 'function' ? successTitle(response) : successTitle;
                console.log(title, path);
                await showDialog({
                    title: title,
                    body: successMessage(response),
                    buttons: [Dialog.okButton({label: 'OK'})]
                });
            } catch (error) {
                const errMssg = `${command} Failed:`;
                if (error instanceof Error) {
                    console.error(errMssg, error.message);
                    await showDialog({
                        title: `${command} Failed`,
                        body: `Error: ${error.message}.`,
                        buttons: [Dialog.okButton({label: 'OK'})]
                    });
                } else {
                    console.error(errMssg, error);
                }
            } finally {
                if (content.isAttached) {
                    content.parent = null;
                }
                mainWidget.dispose();
                enableFileBrowser(fileBrowser);
            }
        }
    }
}

async function handleUploadCommand(
    app: JupyterFrontEnd,
    tracker: IFileBrowserFactory['tracker'],
    path: string,
    fileBrowser: FileBrowser,
    content: SpinnerWidget,
    mainWidget: MainAreaWidget<SpinnerWidget>
) {
    try {
        // First check if file exists
        const statusResponse = await requestAPI<any>('status', {
            method: 'POST',
            body: JSON.stringify({path}),
        });

        if (statusResponse.status === "Exists in HydroShare" ||
            statusResponse.status === "Exists in HydroShare but they are different" ||
            statusResponse.status === "Exists in HydroShare and they are identical") {

            const result = await showDialog({
                title: 'File Already Exists',
                body: 'This file already exists in HydroShare. Would you like to replace it?',
                buttons: [
                    Dialog.cancelButton({ label: 'Cancel' }),
                    Dialog.okButton({ label: 'Replace' })
                ],
                defaultButton: 0
            });

            if (result.button.label === 'Replace') {
                // Delete the existing file first
                await requestAPI<any>('delete', {
                    method: 'POST',
                    body: JSON.stringify({path}),
                });

                // Now upload the new file
                const uploadResponse = await requestAPI<any>('upload', {
                    method: 'POST',
                    body: JSON.stringify({path}),
                });

                await showDialog({
                    title: 'File upload to HydroShare was successful',
                    body: uploadResponse.success,
                    buttons: [Dialog.okButton({label: 'OK'})]
                });
            }
        } else {
            // File doesn't exist, proceed with normal upload
            const uploadResponse = await requestAPI<any>('upload', {
                method: 'POST',
                body: JSON.stringify({path}),
            });

            await showDialog({
                title: 'File upload to HydroShare was successful',
                body: uploadResponse.success,
                buttons: [Dialog.okButton({label: 'OK'})]
            });
        }
    } catch (error) {
        const errMssg = `Upload file to HydroShare Failed:`;
        if (error instanceof Error) {
            console.error(errMssg, error.message);
            await showDialog({
                title: `Upload Failed`,
                body: `Error: ${error.message}.`,
                buttons: [Dialog.okButton({label: 'OK'})]
            });
        } else {
            console.error(errMssg, error);
        }
    } finally {
        if (content.isAttached) {
            content.parent = null;
        }
        mainWidget.dispose();
        enableFileBrowser(fileBrowser);
    }
}

const extension: JupyterFrontEndPlugin<void> = {
    id: 'hsfiles_jupyter:plugin',
    autoStart: true,
    requires: [IFileBrowserFactory],
    activate: (app: JupyterFrontEnd, factory: IFileBrowserFactory) => {
        const {commands} = app;
        const {tracker} = factory;
        console.log('JupyterLab extension hsfiles_jupyter is activated!');

        commands.addCommand('upload-to-hydroshare', {
            label: 'Upload File to HydroShare',
            icon: addIcon,
            execute: async () => {
                const widget = tracker.currentWidget;
                if (widget) {
                    const selectedItem = widget.selectedItems().next();
                    if (selectedItem && selectedItem.value) {
                        const path = selectedItem.value.path;
                        const fileBrowser = tracker.currentWidget;
                        disableFileBrowser(fileBrowser);

                        const content = new SpinnerWidget();
                        const mainWidget = new MainAreaWidget({ content });
                        mainWidget.id = 'spinner-upload-to-hydroshare';
                        mainWidget.title.label = 'Processing...';
                        app.shell.add(mainWidget, 'main');
                        app.shell.currentChanged;  // Wait for layout update
                        content.node.style.display = 'block';

                        await handleUploadCommand(app, tracker, path, fileBrowser, content, mainWidget);
                    }
                }
            }
        });

        commands.addCommand('refresh-from-hydroshare', {
            label: 'Replace with File from HydroShare',
            icon: downloadIcon,
            execute: async () => {
                const result = await showDialog({
                    title: 'Replace File',
                    body: 'Replace will overwrite the local copy of the file. Are you sure you want replace this file from HydroShare?',
                    buttons: [
                        Dialog.cancelButton({ label: 'Cancel' }),
                        Dialog.okButton({ label: 'OK' })
                    ],
                    defaultButton: 0
                });
                if (result.button.label === 'OK') {
                    await handleCommand(
                        app,
                        tracker,
                        'Replace with file from HydroShare',
                        'refresh',
                        'File replace from HydroShare was successful',
                        response => `${response.success}`
                    );
                }
            }
        });

        commands.addCommand('delete-file-from-hydroshare', {
            label: `Delete File` + ` in HydroShare`,
            icon: closeIcon,
            execute: async () => {
                const result = await showDialog({
                    title: 'Delete File',
                    body: 'Are you sure you want to permanently delete this file in HydroShare?',
                    buttons: [
                        Dialog.cancelButton({ label: 'Cancel' }),
                        Dialog.okButton({ label: 'OK' })
                    ],
                    defaultButton: 0
                });

                if (result.button.label === 'OK') {
                    await handleCommand(
                        app,
                        tracker,
                        `Delete file in` + ` HydroShare`,
                        'delete',
                        `File delete in` + ` HydroShare was successful`,
                        response => `${response.success}`
                    );
                }
            }
        });

        commands.addCommand('check-file-status-with-hydroshare', {
            label: 'Check Status of File in HydroShare',
            icon: infoIcon,
            execute: () => handleCommand(
                app,
                tracker,
                'Check status of file in HydroShare',
                'status',
                response => `File Status: ${response.status}`,
                response => `${response.success}`
            )
        });

        // Add separator before HydroShare items with a higher rank
        app.contextMenu.addItem({
            type: 'separator',
            selector: '.jp-DirListing-item[data-isdir="false"]',
            rank: 10.0
        });

        // Add HydroShare menu items with consecutive ranks
        app.contextMenu.addItem({
            command: 'upload-to-hydroshare',
            selector: '.jp-DirListing-item[data-isdir="false"]',
            rank: 10.1
        });

        app.contextMenu.addItem({
            command: 'refresh-from-hydroshare',
            selector: '.jp-DirListing-item[data-isdir="false"]',
            rank: 10.2
        });

        app.contextMenu.addItem({
            command: 'delete-file-from-hydroshare',
            selector: '.jp-DirListing-item[data-isdir="false"]',
            rank: 10.3
        });

        app.contextMenu.addItem({
            command: 'check-file-status-with-hydroshare',
            selector: '.jp-DirListing-item[data-isdir="false"]',
            rank: 10.4
        });

        // Add separator after HydroShare items
        app.contextMenu.addItem({
            type: 'separator',
            selector: '.jp-DirListing-item[data-isdir="false"]',
            rank: 10.5
        });
    }
};

export default extension;
