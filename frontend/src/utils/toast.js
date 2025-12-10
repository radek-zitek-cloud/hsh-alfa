import { toast } from 'react-toastify';

/**
 * Toast notification utility for displaying messages to users.
 *
 * This utility provides a consistent interface for showing notifications
 * throughout the application. It replaces modal dialogs and alert() calls.
 *
 * Configuration:
 * - Success messages: Auto-dismiss after 5 seconds
 * - Info messages: Auto-dismiss after 5 seconds
 * - Warning messages: Auto-dismiss after 5 seconds
 * - Error messages: Require user dismissal (autoClose: false)
 *
 * Usage:
 *   import { showSuccess, showError, showWarning, showInfo } from '@/utils/toast';
 *
 *   showSuccess('Note saved successfully!');
 *   showError('Failed to save note');
 *   showWarning('This action cannot be undone');
 *   showInfo('Processing your request...');
 */

/**
 * Show a success notification (auto-dismisses after 5 seconds)
 * @param {string} message - The message to display
 */
export const showSuccess = (message) => {
  toast.success(message, {
    position: 'top-right',
    autoClose: 5000,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  });
};

/**
 * Show an error notification (requires user dismissal)
 * @param {string} message - The error message to display
 */
export const showError = (message) => {
  toast.error(message, {
    position: 'top-right',
    autoClose: false, // Errors require user dismissal
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  });
};

/**
 * Show a warning notification (auto-dismisses after 5 seconds)
 * @param {string} message - The warning message to display
 */
export const showWarning = (message) => {
  toast.warning(message, {
    position: 'top-right',
    autoClose: 5000,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  });
};

/**
 * Show an info notification (auto-dismisses after 5 seconds)
 * @param {string} message - The info message to display
 */
export const showInfo = (message) => {
  toast.info(message, {
    position: 'top-right',
    autoClose: 5000,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  });
};

/**
 * Show a loading notification that can be updated
 * Useful for operations that take time and have multiple stages
 * @param {string} message - The loading message to display
 * @returns {number} toastId - The ID of the toast to update later
 */
export const showLoading = (message) => {
  return toast.loading(message, {
    position: 'top-right',
  });
};

/**
 * Update an existing toast notification
 * @param {number} toastId - The ID of the toast to update
 * @param {string} message - The new message
 * @param {string} type - The type of toast ('success', 'error', 'warning', 'info')
 */
export const updateToast = (toastId, message, type = 'success') => {
  const options = {
    render: message,
    type,
    isLoading: false,
    autoClose: type === 'error' ? false : 5000,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  };

  toast.update(toastId, options);
};

/**
 * Dismiss a specific toast
 * @param {number} toastId - The ID of the toast to dismiss
 */
export const dismissToast = (toastId) => {
  toast.dismiss(toastId);
};

/**
 * Dismiss all toasts
 */
export const dismissAllToasts = () => {
  toast.dismiss();
};
