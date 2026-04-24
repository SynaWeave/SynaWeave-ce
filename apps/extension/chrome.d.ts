interface ChromeTab {
	id?: number;
	windowId?: number;
}

interface ChromeRuntimeMessageSender {
	tab?: ChromeTab;
}

interface ChromeContextMenuInfo {
	menuItemId: string;
}

interface ChromeStorageArea {
	get(keys: string[]): Promise<Record<string, unknown>>;
	remove(keys: string | string[]): Promise<void>;
	set(items: Record<string, unknown>): Promise<void>;
}

interface ChromeRuntimeApi {
	onInstalled: {
		addListener(listener: () => void): void;
	};
	onStartup: {
		addListener(listener: () => void): void;
	};
	onMessage: {
		addListener(
			listener: (
				message: { type?: string } | undefined,
				sender: ChromeRuntimeMessageSender,
				sendResponse: (response: unknown) => void,
			) => boolean,
		): void;
	};
}

interface ChromeSidePanelApi {
	setPanelBehavior(options: { openPanelOnActionClick: boolean }): Promise<void>;
	setOptions(options: {
		tabId: number;
		enabled: boolean;
		path?: string;
	}): Promise<void>;
	open(options: { windowId?: number }): Promise<void>;
}

interface ChromeContextMenusApi {
	create(options: {
		id: string;
		title: string;
		contexts: string[];
	}): void;
	onClicked: {
		addListener(
			listener: (info: ChromeContextMenuInfo, tab?: ChromeTab) => void,
		): void;
	};
}

interface ChromeActionApi {
	onClicked: {
		addListener(listener: (tab: ChromeTab) => void): void;
	};
}

interface ChromeCommandsApi {
	onCommand: {
		addListener(listener: (command: string) => void | Promise<void>): void;
	};
}

interface ChromeTabsApi {
	query(queryInfo: {
		active: boolean;
		currentWindow: boolean;
	}): Promise<ChromeTab[]>;
	sendMessage(tabId: number, message: { type: string }): Promise<unknown>;
}

interface ChromeApi {
	runtime: ChromeRuntimeApi;
	sidePanel: ChromeSidePanelApi;
	contextMenus: ChromeContextMenusApi;
	action: ChromeActionApi;
	commands: ChromeCommandsApi;
	tabs: ChromeTabsApi;
	storage: {
		local: ChromeStorageArea;
	};
}

declare const chrome: ChromeApi;
