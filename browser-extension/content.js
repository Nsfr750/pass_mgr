// Content script for auto-filling login forms

// Configuration
const OBSERVER_CONFIG = { 
  childList: true, 
  subtree: true,
  attributes: true,
  attributeFilter: ['style', 'class', 'type']
};

// State
let isProcessing = false;
let currentUrl = window.location.href;
let loginForms = new Set();
let observer = null;

// Initialize the content script
function init() {
  // Check if we're on a login page
  if (isLoginPage()) {
    setupFormDetection();
    setupMutationObserver();
    setupMessageListener();
  }
}

// Check if the current page is a login page
function isLoginPage() {
  // Check common login page indicators
  const loginIndicators = [
    'login', 'signin', 'sign-in', 'log-in', 'sign_in', 'log_in',
    'auth', 'authentication', 'account', 'user'
  ];
  
  const url = window.location.href.toLowerCase();
  const path = window.location.pathname.toLowerCase();
  
  // Check URL path
  if (loginIndicators.some(indicator => path.includes(indicator))) {
    return true;
  }
  
  // Check for login forms on the page
  const loginForms = document.querySelectorAll('form[action*="login"], form[action*="signin"], form[action*="auth"]');
  if (loginForms.length > 0) {
    return true;
  }
  
  // Check for username/password fields
  const usernameFields = document.querySelectorAll('input[type="text"][name*="user"], input[type="email"], input[name*="email"]');
  const passwordFields = document.querySelectorAll('input[type="password"]');
  
  return usernameFields.length > 0 && passwordFields.length > 0;
}

// Set up form detection
function setupFormDetection() {
  // Find all forms on the page
  const forms = document.getElementsByTagName('form');
  
  for (const form of forms) {
    if (isLoginForm(form)) {
      addFormToWatch(form);
    }
  }
  
  // Also watch for dynamically added forms
  setupMutationObserver();
}

// Check if an element is a login form
function isLoginForm(form) {
  // Check for common login form indicators
  const loginIndicators = ['login', 'signin', 'sign-in', 'log-in', 'sign_in', 'log_in', 'auth'];
  
  // Check form attributes
  const formId = (form.id || '').toLowerCase();
  const formClass = (form.className || '').toLowerCase();
  const formAction = (form.action || '').toLowerCase();
  
  if (loginIndicators.some(indicator => 
    formId.includes(indicator) || 
    formClass.includes(indicator) || 
    formAction.includes(indicator)
  )) {
    return true;
  }
  
  // Check for username/email and password fields
  const hasUsernameField = Array.from(form.elements).some(el => 
    (el.type === 'text' && /(user|login|email)/i.test(el.name || '')) ||
    el.type === 'email'
  );
  
  const hasPasswordField = Array.from(form.elements).some(el => 
    el.type === 'password'
  );
  
  return hasUsernameField && hasPasswordField;
}

// Add a form to the watch list
function addFormToWatch(form) {
  if (loginForms.has(form)) return;
  
  loginForms.add(form);
  
  // Add submit handler to detect successful logins
  form.addEventListener('submit', handleFormSubmit);
  
  // Check if we should auto-fill this form
  if (shouldAutoFillForm(form)) {
    requestCredentials(form);
  }
}

// Handle form submission
function handleFormSubmit(event) {
  const form = event.target;
  const formData = extractFormData(form);
  
  // Check if this is a login form
  if (isLoginForm(form) && formData.username && formData.password) {
    // Save the credentials if this is a successful login
    chrome.runtime.sendMessage({
      type: 'saveCredentials',
      url: window.location.hostname,
      credentials: formData
    });
  }
}

// Extract form data
function extractFormData(form) {
  const formData = {
    username: '',
    password: '',
    fields: {}
  };
  
  for (const element of form.elements) {
    if (!element.name) continue;
    
    const name = element.name.toLowerCase();
    const value = element.value.trim();
    
    if (name.includes('user') || name.includes('login') || name.includes('email')) {
      formData.username = value;
      formData.fields[name] = { type: 'username', value };
    } else if (name.includes('pass')) {
      formData.password = value;
      formData.fields[name] = { type: 'password', value };
    } else if (element.type === 'hidden' || element.type === 'text' || element.type === 'email') {
      formData.fields[name] = { type: 'text', value };
    }
  }
  
  return formData;
}

// Check if we should auto-fill a form
function shouldAutoFillForm(form) {
  // Check user preferences
  // TODO: Implement user preferences
  
  // For now, auto-fill all login forms
  return true;
}

// Request credentials from the background script
function requestCredentials(form) {
  if (isProcessing) return;
  isProcessing = true;
  
  // Get form fields
  const fields = {};
  
  for (const element of form.elements) {
    if (element.name) {
      const name = element.name.toLowerCase();
      let type = 'text';
      
      if (name.includes('user') || name.includes('login') || name.includes('email')) {
        type = 'username';
      } else if (name.includes('pass')) {
        type = 'password';
      } else if (element.type === 'email') {
        type = 'email';
      } else if (element.type === 'tel') {
        type = 'tel';
      } else if (element.type === 'number') {
        type = 'number';
      }
      
      fields[name] = {
        type,
        value: element.value || '',
        id: element.id || '',
        className: element.className || ''
      };
    }
  }
  
  // Send message to background script
  chrome.runtime.sendMessage({
    type: 'getCredentials',
    url: window.location.hostname,
    fields: fields
  }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('Error getting credentials:', chrome.runtime.lastError);
      isProcessing = false;
      return;
    }
    
    if (response && response.credentials) {
      fillForm(form, response.credentials);
    }
    
    isProcessing = false;
  });
}

// Fill a form with credentials
function fillForm(form, credentials) {
  if (!form || !credentials) return;
  
  // Fill in the form fields
  for (const [name, field] of Object.entries(credentials.fields || {})) {
    const elements = form.querySelectorAll(`[name="${name}"]`);
    
    for (const element of elements) {
      if (field.type === 'password' && element.type === 'password') {
        element.value = field.value || '';
      } else if ((field.type === 'username' || field.type === 'email') && 
                 (element.type === 'text' || element.type === 'email')) {
        element.value = field.value || '';
      }
    }
  }
  
  // Dispatch input events to trigger any form validation
  for (const element of form.elements) {
    if (element.value) {
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }
  
  // Auto-submit the form if it has a password field and only one button
  const buttons = form.querySelectorAll('button, input[type="submit"]');
  if (credentials.autoSubmit !== false && buttons.length === 1) {
    // Small delay to allow any validation to complete
    setTimeout(() => {
      form.submit();
    }, 100);
  }
}

// Set up mutation observer to detect dynamically added forms
function setupMutationObserver() {
  if (observer) {
    observer.disconnect();
  }
  
  observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      // Check added nodes
      for (const node of mutation.addedNodes) {
        if (node.nodeType === Node.ELEMENT_NODE) {
          // Check if this is a form
          if (node.tagName.toLowerCase() === 'form' && isLoginForm(node)) {
            addFormToWatch(node);
          }
          
          // Check for forms in the added nodes
          const forms = node.getElementsByTagName ? 
            node.getElementsByTagName('form') : [];
            
          for (const form of forms) {
            if (isLoginForm(form)) {
              addFormToWatch(form);
            }
          }
        }
      }
    }
  });
  
  // Start observing the document with the configured parameters
  observer.observe(document.documentElement, OBSERVER_CONFIG);
}

// Set up message listener
function setupMessageListener() {
  // Listen for messages from the background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message || !message.type) return;
    
    switch (message.type) {
      case 'fillCredentials':
        // Find the most likely form to fill
        const form = findBestFormToFill();
        if (form && message.credentials) {
          fillForm(form, message.credentials);
        }
        break;
        
      case 'checkStatus':
        // Just acknowledge the message
        sendResponse({ status: 'ready' });
        break;
    }
  });
}

// Find the best form to fill on the page
function findBestFormToFill() {
  // If we've already found forms, use the first one
  if (loginForms.size > 0) {
    return loginForms.values().next().value;
  }
  
  // Otherwise, look for forms with password fields
  const passwordFields = document.querySelectorAll('input[type="password"]');
  
  for (const field of passwordFields) {
    let form = field;
    
    // Find the parent form
    while (form && form.tagName !== 'FORM' && form !== document.body) {
      form = form.parentElement;
    }
    
    if (form && form.tagName === 'FORM') {
      return form;
    }
  }
  
  return null;
}

// Initialize the content script when the DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
