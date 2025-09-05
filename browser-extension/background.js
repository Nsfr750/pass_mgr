// Background script for the Password Manager Auto-fill extension

// Native messaging port
let port = null;
let isConnected = false;

// Connect to the native host application
function connectToNativeApp() {
  const nativeHostName = "com.passmgr.extension";
  
  try {
    port = chrome.runtime.connectNative(nativeHostName);
    isConnected = true;
    
    port.onMessage.addListener((message) => {
      // Handle messages from the native application
      handleNativeMessage(message);
    });
    
    port.onDisconnect.addListener(() => {
      isConnected = false;
      console.log('Disconnected from native application');
      // Try to reconnect after a delay
      setTimeout(connectToNativeApp, 5000);
    });
    
    console.log('Connected to native application');
  } catch (error) {
    console.error('Failed to connect to native application:', error);
    isConnected = false;
    // Retry connection after a delay
    setTimeout(connectToNativeApp, 5000);
  }
}

// Handle messages from the native application
function handleNativeMessage(message) {
  if (!message || !message.type) return;
  
  switch (message.type) {
    case 'credentials':
      // Forward credentials to the content script
      chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        if (tabs[0] && tabs[0].id) {
          chrome.tabs.sendMessage(tabs[0].id, {
            type: 'fillCredentials',
            credentials: message.credentials
          });
        }
      });
      break;
      
    case 'status':
      // Update extension icon based on status
      updateExtensionIcon(message.status);
      break;
      
    default:
      console.log('Received unknown message type:', message.type);
  }
}

// Update the extension icon based on status
function updateExtensionIcon(status) {
  const iconPath = status === 'connected' ? 'icons/icon48.png' : 'icons/icon48-gray.png';
  chrome.action.setIcon({path: iconPath});
}

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (!request || !request.type) return;
  
  switch (request.type) {
    case 'getCredentials':
      // Forward the request to the native application
      if (isConnected && port) {
        port.postMessage({
          type: 'getCredentials',
          url: request.url,
          fields: request.fields
        });
      } else {
        console.error('Not connected to native application');
      }
      break;
      
    case 'saveCredentials':
      // Forward save request to the native application
      if (isConnected && port) {
        port.postMessage({
          type: 'saveCredentials',
          url: request.url,
          credentials: request.credentials
        });
      }
      break;
      
    case 'checkStatus':
      // Check connection status
      sendResponse({ isConnected });
      return true; // Required for async response
      
    default:
      console.log('Unknown message type:', request.type);
  }
});

// Initialize connection when extension loads
connectToNativeApp();

// Periodically check connection status
setInterval(() => {
  if (!isConnected) {
    connectToNativeApp();
  } else if (port) {
    // Send a ping to keep the connection alive
    try {
      port.postMessage({ type: 'ping' });
    } catch (error) {
      console.error('Ping failed, connection lost:', error);
      isConnected = false;
      connectToNativeApp();
    }
  }
}, 30000); // Check every 30 seconds
