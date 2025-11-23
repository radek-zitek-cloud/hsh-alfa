/**
 * Utility functions for input validation and sanitization
 */

/**
 * Sanitizes input by removing HTML tags and script content
 * @param {string} input - The input string to sanitize
 * @returns {string} - Sanitized string
 */
export const sanitizeInput = (input) => {
  if (!input || typeof input !== 'string') return ''

  // Remove script tags and their content
  let sanitized = input.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')

  // Remove HTML tags
  sanitized = sanitized.replace(/<[^>]*>/g, '')

  // Remove potential XSS vectors
  sanitized = sanitized.replace(/javascript:/gi, '')
  sanitized = sanitized.replace(/on\w+\s*=/gi, '')

  return sanitized
}

/**
 * Validates a URL with improved error messaging
 * @param {string} url - The URL to validate
 * @returns {{ isValid: boolean, error?: string }} - Validation result
 */
export const validateUrl = (url) => {
  if (!url || !url.trim()) {
    return { isValid: false, error: 'URL is required' }
  }

  const trimmedUrl = url.trim()

  // Check for obvious malicious schemes
  const maliciousSchemes = ['javascript:', 'data:', 'vbscript:', 'file:']
  const lowerUrl = trimmedUrl.toLowerCase()

  for (const scheme of maliciousSchemes) {
    if (lowerUrl.startsWith(scheme)) {
      return { isValid: false, error: `Invalid URL scheme: ${scheme} is not allowed` }
    }
  }

  // Check if URL is relative (starts with /)
  if (trimmedUrl.startsWith('/')) {
    return {
      isValid: false,
      error: 'Relative URLs are not supported. Please provide an absolute URL (e.g., https://example.com/path)'
    }
  }

  // Check if URL has a protocol
  if (!trimmedUrl.match(/^[a-zA-Z][a-zA-Z\d+\-.]*:/)) {
    return {
      isValid: false,
      error: 'URL must include a protocol (e.g., https://example.com)'
    }
  }

  // Try to parse with URL constructor
  try {
    const urlObj = new URL(trimmedUrl)

    // Only allow http and https protocols
    if (!['http:', 'https:'].includes(urlObj.protocol)) {
      return {
        isValid: false,
        error: `Only HTTP and HTTPS protocols are allowed, got ${urlObj.protocol}`
      }
    }

    return { isValid: true }
  } catch (e) {
    return {
      isValid: false,
      error: 'Invalid URL format. Please check the URL and try again'
    }
  }
}

/**
 * Validates a favicon URL
 * @param {string} url - The favicon URL to validate
 * @returns {{ isValid: boolean, error?: string }} - Validation result
 */
export const validateFaviconUrl = (url) => {
  if (!url || !url.trim()) {
    return { isValid: true } // Favicon is optional
  }

  return validateUrl(url)
}

/**
 * Parses tags string into an array
 * @param {string} tagsString - Comma-separated tags string
 * @returns {string[] | null} - Array of trimmed tags or null if empty
 */
export const parseTags = (tagsString) => {
  if (!tagsString || !tagsString.trim()) {
    return null
  }

  const tags = tagsString
    .split(',')
    .map(tag => tag.trim())
    .filter(tag => tag.length > 0)

  return tags.length > 0 ? tags : null
}

/**
 * Debounces a function
 * @param {Function} func - The function to debounce
 * @param {number} wait - The delay in milliseconds
 * @returns {Function} - Debounced function
 */
export const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}
