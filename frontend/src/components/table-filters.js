export const activeFilter = key => ({
  key, label: 'Holat', getValue: row => row[key] !== false,
  options: [{ value: true, label: 'Faol' }, { value: false, label: 'Nofaol' }],
});

export const platformFilter = {
  key: 'platform', label: 'Tizim',
  options: [{ value: 'windows', label: 'Windows' }, { value: 'macos', label: 'macOS' }, { value: 'linux', label: 'Linux' }],
};

export const lockedFilter = {
  key: 'locked', label: 'Holat', getValue: row => Boolean(row.locked),
  options: [{ value: false, label: 'Ochiq' }, { value: true, label: 'Qulflangan' }],
};

export const severityFilter = {
  key: 'severity', label: 'Daraja',
  options: [{ value: 'info', label: 'Ma’lumot' }, { value: 'warning', label: 'Ogohlantirish' }],
};
