import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const OAuthCallback = () => {
  const navigate = useNavigate();
  const { handleCallback } = useAuth();
  const [error, setError] = useState(null);
  const hasProcessed = useRef(false);

  useEffect(() => {
    const processCallback = async () => {
      // Prevent processing the callback multiple times
      if (hasProcessed.current) {
        return;
      }
      hasProcessed.current = true;
      try {
        // Get authorization code and state from URL query parameters
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const errorParam = urlParams.get('error');

        if (errorParam) {
          setError(`Authentication failed: ${errorParam}`);
          setTimeout(() => navigate('/'), 3000);
          return;
        }

        if (!code) {
          setError('No authorization code received');
          setTimeout(() => navigate('/'), 3000);
          return;
        }

        if (!state) {
          setError('No state parameter received - possible security issue');
          setTimeout(() => navigate('/'), 3000);
          return;
        }

        // Exchange code for token with state validation
        await handleCallback(code, state);

        // Redirect to home page
        navigate('/');
      } catch (err) {
        console.error('OAuth callback error:', err);
        setError(err?.message || 'Authentication failed. Please try again.');
        setTimeout(() => navigate('/'), 3000);
      }
    };

    processCallback();
  }, [handleCallback, navigate]);

  return (
    <div className="oauth-callback">
      <div className="oauth-callback-card">
        {error ? (
          <div className="oauth-callback-error">
            <svg
              className="error-icon"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              width="48"
              height="48"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h2>Authentication Failed</h2>
            <p>{error}</p>
            <p className="redirect-message">Redirecting to login page...</p>
          </div>
        ) : (
          <div className="oauth-callback-loading">
            <div className="spinner"></div>
            <h2>Completing sign in...</h2>
            <p>Please wait while we authenticate your account.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default OAuthCallback;
