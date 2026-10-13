export function mobileFingerprintUrl(origin, sessionId) {
  return new URL('/mobile/fingerprint/' + encodeURIComponent(sessionId) + '/', origin).href;
}

