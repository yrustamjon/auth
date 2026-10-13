export function isTerminalEnrollment(status) { return ['approved','rejected','cancelled','expired'].includes(status); }
export function readEnrollmentToken(value, origin) {
  const url = new URL(value, origin);
  if (url.origin !== new URL(origin).origin) throw new Error('QR havola boshqa saytga tegishli');
  const match = url.pathname.match(/^\/device-enroll\/([A-Za-z0-9_-]+)\/?$/);
  if (!match || match[1] === 'approval') throw new Error('Qurilma QR havolasi noto‘g‘ri');
  return match[1];
}

