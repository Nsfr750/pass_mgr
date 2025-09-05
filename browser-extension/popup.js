// Popup script for the Password Manager extension

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const statusElement = document.getElementById('status');
  const statusText = document.getElementById('status-text');
  const loginForm = document.getElementById('login-form');
  const mainInterface = document.getElementById('main-interface');
  const masterPasswordInput = document.getElementById('master-password');
  const unlockButton = document.getElementById('unlock-button');
  const unlockSpinner = document.getElementById('unlock-spinner');
  const unlockText = document.getElementById('unlock-text');
  const fillButton = document.getElementById('fill-button');
  const fillSpinner = document.getElementById('fill-spinner');
  const fillText = document.getElementById('fill-text');
  const saveButton = document.getElementById('save-button');
  const settingsButton = document.getElementById('settings-button');

  // State
  let isConnected = false;
  let isUnlocked = false;
  let currentTab = null;

  // Initialize the popup
  async function init() {
    // Get the current active tab
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTab = tabs[0];

    // Check connection status
    checkConnection();

    // Set up event listeners
    unlockButton.addEventListener('click', handleUnlock);
    fillButton.addEventListener('click', handleFill);
    saveButton.addEventListener('click', handleSave);
    settingsButton.addEventListener('click', openSettings);
    masterPasswordInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        handleUnlock();
      }
    });

    // Check if already unlocked
    chrome.storage.local.get(['isUnlocked'], (result) => {
      if (result.isUnlocked) {
        isUnlocked = true;
        showMainInterface();
      } else {
        showLoginForm();
      }
    });
  }

  // Check connection to the native application
  function checkConnection() {
    chrome.runtime.sendMessage({ type: 'checkStatus' }, (response) => {
      if (chrome.runtime.lastError) {
        updateStatus(false, 'Not connected to Password Manager');
        return;
      }

      isConnected = response && response.isConnected;
      
      if (isConnected) {
        updateStatus(true, 'Connected to Password Manager');
      } else {
        updateStatus(false, 'Not connected to Password Manager');
      }
    });
  }

  // Update the status display
  function updateStatus(connected, message) {
    isConnected = connected;
    statusText.textContent = message;
    
    if (connected) {
      statusElement.classList.remove('disconnected');
      statusElement.classList.add('connected');
    } else {
      statusElement.classList.remove('connected');
      statusElement.classList.add('disconnected');
    }
  }

  // Show the login form
  function showLoginForm() {
    loginForm.classList.remove('hidden');
    mainInterface.classList.add('hidden');
    masterPasswordInput.focus();
  }

  // Show the main interface
  function showMainInterface() {
    loginForm.classList.add('hidden');
    mainInterface.classList.remove('hidden');
  }

  // Handle unlock button click
  async function handleUnlock() {
    const password = masterPasswordInput.value.trim();
    
    if (!password) {
      updateStatus(false, 'Please enter your master password');
      return;
    }

    // Show loading state
    unlockSpinner.classList.remove('hidden');
    unlockText.textContent = 'Unlocking...';
    unlockButton.disabled = true;

    try {
      // In a real implementation, this would verify the password with the native app
      const isValid = await verifyMasterPassword(password);
      
      if (isValid) {
        // Store the unlocked state
        await chrome.storage.local.set({ isUnlocked: true });
        isUnlocked = true;
        showMainInterface();
      } else {
        updateStatus(false, 'Incorrect password');
      }
    } catch (error) {
      console.error('Error during unlock:', error);
      updateStatus(false, 'Error connecting to Password Manager');
    } finally {
      // Reset the button state
      unlockSpinner.classList.add('hidden');
      unlockText.textContent = 'Unlock';
      unlockButton.disabled = false;
    }
  }

  // Simulate master password verification
  // In a real implementation, this would communicate with the native app
  function verifyMasterPassword(password) {
    return new Promise((resolve) => {
      // This is a placeholder. In a real implementation, you would:
      // 1. Send the password to the native application for verification
      // 2. Wait for the response
      // 3. Return true if the password is correct, false otherwise
      
      // For demo purposes, accept any non-empty password
      setTimeout(() => {
        resolve(password.length > 0);
      }, 500);
    });
  }

  // Handle fill button click
  function handleFill() {
    if (!isConnected) {
      updateStatus(false, 'Not connected to Password Manager');
      return;
    }

    // Show loading state
    fillSpinner.classList.remove('hidden');
    fillText.textContent = 'Filling...';
    fillButton.disabled = true;

    // Send message to content script to fill the form
    chrome.tabs.sendMessage(currentTab.id, { type: 'fillForm' }, (response) => {
      // Reset button state after a short delay
      setTimeout(() => {
        fillSpinner.classList.add('hidden');
        fillText.textContent = 'Fill Login';
        fillButton.disabled = false;
        
        // Close the popup after a short delay
        setTimeout(() => {
          window.close();
        }, 500);
      }, 500);
    });
  }

  // Handle save button click
  function handleSave() {
    if (!isConnected) {
      updateStatus(false, 'Not connected to Password Manager');
      return;
    }

    // Send message to content script to save the current form
    chrome.tabs.sendMessage(currentTab.id, { type: 'saveForm' }, (response) => {
      if (response && response.success) {
        updateStatus(true, 'Login saved successfully');
      } else {
        updateStatus(false, 'No login form found on this page');
      }
      
      // Close the popup after a short delay
      setTimeout(() => {
        window.close();
      }, 1000);
    });
  }

  // Open the extension's settings page
  function openSettings() {
    chrome.runtime.openOptionsPage();
    window.close();
  }

  // Initialize the popup
  init();
});
