/**
 * AD BioGuard â€” Frontend Application
 * Navigation stack: select â†’ face-select / finger-select â†’ action screens
 */

const App = (() => {

  /* â”€â”€ State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  let config        = {};
  let cameraStream  = null;
  let currentScreen = 'init';
  let screenStack   = [];   // navigation history for ← Back
  let faceQualityTimer = null;
  let lastFaceQuality  = null;

  /* â”€â”€ Boot â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  async function init() {
    startClock();
    await waitForPywebview();

    try {
      const raw = await pywebview.api.get_config();
      config = JSON.parse(raw);
    } catch(e) {
      config = { username: 'demo.user', camera_ok: true,
                 dev_mode: true, demo_mode: true };
    }

    document.getElementById('header-user').textContent =
      config.username.toUpperCase();
    document.getElementById('select-username').textContent =
      `${config.username} — kirish uchun tasdiqlang`;

    if (config.demo_mode)
      document.getElementById('header-mode').style.display = 'inline';
    document.getElementById('dev-bar').style.display = 'flex';

    if (!config.camera_ok) {
      document.getElementById('face-badge-text').textContent = 'No Webcam';
      const badge = document.getElementById('face-badge');
      badge.style.color       = 'var(--amber)';
      badge.style.borderColor = 'var(--amber)';
      document.getElementById('webcam-badge-text').textContent = 'Not detected';
      const wb = document.getElementById('webcam-badge');
      wb.style.color       = 'var(--amber)';
      wb.style.borderColor = 'var(--amber)';
      const wc = document.getElementById('card-face-webcam');
      wc.style.opacity = '0.45';
      wc.style.pointerEvents = 'none';
    }

    // 1. Aktivatsiyadan o'tganmi?
    if (!config.activated) {
      sleep(400).then(() => showScreen('setup', false));
      return;
    }

    setInitStatus('Session starting...');

    // 2. Internet yo'q â€” offline rejim
    if (!config.online) {
      // Org bilan â†’ admin username + parol (adauth.tech)
      if (config.has_offline) {
        sleep(400).then(() => showScreen('offline-admin', false));
        return;
      }
      // Orgsiz â†’ faqat parol
      if (config.has_personal_offline) {
        sleep(400).then(() => showScreen('offline', false));
        return;
      }
      // Hech qanday offline yo'q
      setInitStatus('Internet yo\'q. IT administratorga murojaat qiling.');
      return;
    }

    // 4. Oddiy holatda â€” session boshlash
    await callApi('start_session');
  }

  async function waitForPywebview() {
    for (let i = 0; i < 50; i++) {
      if (typeof pywebview !== 'undefined' && pywebview.api) return;
      await sleep(100);
    }
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     SETUP â€” Aktivatsiya (doc 02)
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function showScreen(name, push = true) {
    if (push && currentScreen !== 'init') screenStack.push(currentScreen);
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const el = document.getElementById(`screen-${name}`);
    if (el) { el.classList.add('active'); currentScreen = name; }
  }

  function showSetupOrg()      { showScreen('setup-org'); }
  function showSetupPersonal() { showScreen('setup-personal'); } // kelgusida

  function onSetupStatus(msg) {
    const org = document.getElementById('setup-org-btn');
    if (org) org.innerHTML = `<div class="spinner" style="display:inline-block"></div> &nbsp; ${msg}`;
  }

  function onSetupError(msg) {
    const orgStatus  = document.getElementById('setup-org-status');
    const orgText    = document.getElementById('setup-org-status-text');
    const orgBtn     = document.getElementById('setup-org-btn');
    if (orgStatus) {
      orgStatus.style.display = 'block';
      if (orgText) orgText.textContent = msg;
      if (orgBtn)  { orgBtn.disabled = false; orgBtn.innerHTML = 'â†’ &nbsp; Aktivatsiya'; }
    }
  }

  function onActivated() {
    showScreen('setup-success', false);
    // 2s keyin ADMIN PAROL o'rnatish (majburiy, o'tkazib bo'lmaydi)
    sleep(2000).then(() => showScreen('setup-admin-pw', false));
  }

  async function submitOrgActivation() {
    const code = document.getElementById('setup-org-code')?.value?.trim();
    if (!code) { onSetupError('Activation Code kiritilishi shart'); return; }
    const btn = document.getElementById('setup-org-btn');
    if (btn) { btn.disabled = true; }
    const status = document.getElementById('setup-org-status');
    if (status) status.style.display = 'none';
    await callApi('activate_org', code);
  }

  async function submitPersonalActivation() {
    const email    = document.getElementById('setup-email')?.value?.trim();
    const password = document.getElementById('setup-password')?.value;
    if (!email || !password) { onSetupError('Email va parol kiritilishi shart'); return; }
    const btn = document.getElementById('setup-personal-btn');
    if (btn) { btn.disabled = true; }
    await callApi('activate_personal', email, password);
  }

  // â”€â”€ Admin parol o'rnatish (aktivatsiyadan keyin, MAJBURIY) â”€â”€â”€â”€â”€â”€
  async function submitAdminPasswordSetup() {
    const pw1    = document.getElementById('setup-admin-pw')?.value;
    const pw2    = document.getElementById('setup-admin-pw2')?.value;
    const errEl  = document.getElementById('setup-admin-status');
    const errTxt = document.getElementById('setup-admin-status-text');
    const btn    = document.getElementById('setup-admin-btn');

    if (!pw1 || pw1.length < 6) {
      if (errEl) errEl.style.display = 'flex';
      if (errTxt) errTxt.textContent = 'Parol kamida 6 ta belgi bo\'lishi kerak';
      return;
    }
    if (pw1 !== pw2) {
      if (errEl) errEl.style.display = 'flex';
      if (errTxt) errTxt.textContent = 'Parollar mos emas';
      return;
    }
    if (errEl) errEl.style.display = 'none';
    if (btn) { btn.disabled = true; btn.innerHTML = '<div class="spinner" style="display:inline-block"></div> &nbsp; Saqlanmoqda...'; }
    await callApi('set_admin_password', pw1);
  }

  function onAdminPasswordSet() {
    // Admin parol saqlandi â†’ session boshlash
    sleep(500).then(async () => {
      try {
        const raw = await pywebview.api.get_config();
        config = JSON.parse(raw);
      } catch(e) {}
      await callApi('start_session');
    });
  }

  function onAdminPasswordError(msg) {
    const errEl  = document.getElementById('setup-admin-status');
    const errTxt = document.getElementById('setup-admin-status-text');
    const btn    = document.getElementById('setup-admin-btn');
    if (errEl) errEl.style.display = 'flex';
    if (errTxt) errTxt.textContent = msg;
    if (btn) { btn.disabled = false; btn.innerHTML = 'â†’ &nbsp; Saqlash'; }
  }

  // â”€â”€ Offline parol o'rnatish (setup dan keyin) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  async function submitOfflineSetup() {
    const pw1 = document.getElementById('offline-setup-pw')?.value;
    const pw2 = document.getElementById('offline-setup-pw2')?.value;
    const statusEl = document.getElementById('offline-setup-status');
    const statusTx = document.getElementById('offline-setup-status-text');
    const btn      = document.getElementById('offline-setup-btn');

    if (!pw1 || pw1.length < 6) {
      if (statusEl) statusEl.style.display = 'flex';
      if (statusTx) statusTx.textContent = 'Parol kamida 6 ta belgi bo\'lishi kerak';
      return;
    }
    if (pw1 !== pw2) {
      if (statusEl) statusEl.style.display = 'flex';
      if (statusTx) statusTx.textContent = 'Parollar mos emas';
      return;
    }
    if (statusEl) statusEl.style.display = 'none';
    if (btn) { btn.disabled = true; btn.innerHTML = '<div class="spinner" style="display:inline-block"></div> &nbsp; Saqlanmoqda...'; }
    await callApi('set_personal_offline_password', pw1);
  }

  function onPersonalOfflineSet() {
    // Parol saqlandi â€” session boshlash
    sleep(600).then(async () => {
      try {
        const raw = await pywebview.api.get_config();
        config = JSON.parse(raw);
      } catch(e) {}
      await callApi('start_session');
    });
  }

  function onPersonalOfflineError(msg) {
    const statusEl = document.getElementById('offline-setup-status');
    const statusTx = document.getElementById('offline-setup-status-text');
    const btn      = document.getElementById('offline-setup-btn');
    if (statusEl) statusEl.style.display = 'flex';
    if (statusTx) statusTx.textContent = msg;
    if (btn)     { btn.disabled = false; btn.innerHTML = 'â†’ &nbsp; Saqlash'; }
  }

  function skipOfflineSetup() {
    // O'tkazib yuborsa â€” session boshlash
    sleep(200).then(async () => {
      try {
        const raw = await pywebview.api.get_config();
        config = JSON.parse(raw);
      } catch(e) {}
      await callApi('start_session');
    });
  }

  /* â”€â”€ Internet monitoring (doc 06) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  function onInternetLost() {
    stopCamera();
    callApi('stop_face_poll');
    callApi('stop_finger_poll');
    if (config.has_offline) {
      showScreen('offline-admin', false);
    } else if (config.has_personal_offline) {
      showScreen('offline', false);
    } else {
      setInitStatus('Internet uzildi. IT administratorga murojaat qiling.');
      showScreen('init', false);
    }
  }

  function onInternetRestored() {
    if (currentScreen === 'offline' || currentScreen === 'offline-admin' || currentScreen === 'init') {
      setInitStatus('Internet qaytdi. Session tiklanmoqda...');
      showScreen('init', false);
      callApi('start_session');
    }
  }

  /* â”€â”€ Screen navigation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  function goBack() {
    stopCamera();
    callApi('stop_face_poll');
    callApi('stop_finger_poll');
    const prev = screenStack.pop();
    if (prev) showScreen(prev, false);
    else      showScreen('select', false);
  }

  /* â”€â”€ Session â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€*/
  function onSessionReady(sessionId) {
    setInitStatus('Session established Â· ' + sessionId.slice(0, 8) + '...');
    sleep(400).then(() => showScreen('select', false));
  }

  /* â”€â”€ Main method select â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  function selectMethod(method) {
    if (method === 'face')   showScreen('face-select');
    else                     showScreen('finger-select');
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     FACE â€” WEBCAM
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function startFaceWebcam() {
    showScreen('face');
    setFaceStatus('idle', 'Opening camera...');

    if (!config.camera_ok) {
      setFaceStatus('error', 'No webcam detected on this device');
      const wrap = document.querySelector('.cam-wrap');
      if (wrap) wrap.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;
             justify-content:center;height:100%;gap:10px;
             font-family:var(--font-mono);color:var(--text-muted);">
          <div style="font-size:32px;opacity:0.3">â¬¡</div>
          <div style="font-size:11px;letter-spacing:0.1em;text-transform:uppercase">
            No camera device found</div>
          <div style="font-size:10px;color:var(--text-dim)">
            Connect a webcam or use Phone Camera</div>
        </div>`;
      const btn = document.getElementById('capture-btn');
      if (btn) btn.disabled = true;
      return;
    }

    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })
      .then(stream => {
        cameraStream = stream;
        const video = document.getElementById('camera-video');
        video.srcObject = stream;
        video.play();
        setFaceStatus('active', 'Camera active â€” look at the camera');
        const btn = document.getElementById('capture-btn');
        if (btn) btn.disabled = true;
        startFaceQualityMonitor();
      })
      .catch(err => {
        setFaceStatus('error', 'Camera denied: ' + err.message);
        const btn = document.getElementById('capture-btn');
        if (btn) btn.disabled = true;
      });
  }

  function stopCamera() {
    if (faceQualityTimer) {
      clearInterval(faceQualityTimer);
      faceQualityTimer = null;
    }
    lastFaceQuality = null;
    if (cameraStream) {
      cameraStream.getTracks().forEach(t => t.stop());
      cameraStream = null;
    }
    const video = document.getElementById('camera-video');
    if (video) video.srcObject = null;
  }

  function startFaceQualityMonitor() {
    if (faceQualityTimer) clearInterval(faceQualityTimer);
    faceQualityTimer = setInterval(() => {
      const video = document.getElementById('camera-video');
      if (!video || !video.srcObject || video.readyState < 2) return;
      const quality = analyzeFaceFrame(video);
      lastFaceQuality = quality;
      updateFaceQualityUI(quality);
    }, 900);
  }

  function analyzeFaceFrame(video) {
    const sample = document.createElement('canvas');
    sample.width = 160;
    sample.height = 120;
    const ctx = sample.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(video, 0, 0, sample.width, sample.height);
    const { data } = ctx.getImageData(0, 0, sample.width, sample.height);

    let sum = 0;
    let sumSq = 0;
    let edgeSum = 0;
    let prevGray = 0;
    let pixels = 0;

    for (let i = 0; i < data.length; i += 4) {
      const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
      sum += gray;
      sumSq += gray * gray;
      if (pixels > 0) edgeSum += Math.abs(gray - prevGray);
      prevGray = gray;
      pixels += 1;
    }

    const brightness = sum / pixels;
    const variance = Math.max(0, sumSq / pixels - brightness * brightness);
    const contrast = Math.sqrt(variance);
    const sharpness = edgeSum / Math.max(1, pixels - 1);

    const issues = [];
    if (brightness < 70) issues.push('too_dark');
    if (brightness > 185) issues.push('too_bright');
    if (contrast < 38) issues.push('low_contrast');
    if (sharpness < 12) issues.push('blurry');

    return {
      brightness,
      contrast,
      sharpness,
      ok: issues.length === 0,
      issues,
    };
  }

  function updateFaceQualityUI(quality) {
    const btn = document.getElementById('capture-btn');
    if (!btn) return;
    if (quality.ok) {
      btn.disabled = false;
      btn.innerHTML = '??? &nbsp; Capture &amp; Verify';
      setFaceStatus('active', 'Lighting good - look straight at the camera');
      return;
    }

    btn.disabled = true;
    btn.innerHTML = '??? &nbsp; Improve Lighting';

    if (quality.issues.includes('too_dark')) {
      setFaceStatus('warning', 'Too dark - face the light or raise screen brightness');
      return;
    }
    if (quality.issues.includes('too_bright')) {
      setFaceStatus('warning', 'Too bright - reduce direct light on your face');
      return;
    }
    if (quality.issues.includes('blurry')) {
      setFaceStatus('warning', 'Image is soft - hold still and move closer');
      return;
    }
    setFaceStatus('warning', 'Low contrast - move to more even lighting');
  }

  function enhanceFrame(canvas, ctx) {
    const img = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = img.data;
    let sum = 0;
    for (let i = 0; i < data.length; i += 4) {
      sum += 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
    }
    const brightness = sum / (data.length / 4);
    const gain = Math.min(1.28, Math.max(0.82, 132 / Math.max(1, brightness)));

    for (let i = 0; i < data.length; i += 4) {
      data[i] = Math.min(255, data[i] * gain);
      data[i + 1] = Math.min(255, data[i + 1] * gain);
      data[i + 2] = Math.min(255, data[i + 2] * gain);
    }

    ctx.putImageData(img, 0, 0);
  }

  function captureFrame() {
    const video = document.getElementById('camera-video');
    if (!video || !video.srcObject) {
      setFaceStatus('error', 'Camera not ready');
      return;
    }
    const quality = lastFaceQuality || analyzeFaceFrame(video);
    if (!quality.ok) {
      updateFaceQualityUI(quality);
      return;
    }

    const canvas = document.getElementById('camera-canvas');
    canvas.width  = video.videoWidth  || 640;
    canvas.height = video.videoHeight || 480;
    if (!canvas.width || !canvas.height) {
      setFaceStatus('error', 'Frame not ready, try again');
      return;
    }
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    enhanceFrame(canvas, ctx);
    const b64 = canvas.toDataURL('image/jpeg', 0.88).split(',')[1];

    const btn = document.getElementById('capture-btn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner"></div> &nbsp; Verifying...';
    setFaceStatus('verifying', 'Analyzing face...');
    stopCamera();
    callApi('capture_face', b64);
  }

  function onFaceRetry(reason) {
    const btn = document.getElementById('capture-btn');
    if (btn) { btn.disabled = false; btn.innerHTML = 'âŠ™ &nbsp; Capture &amp; Verify'; }
    setFaceStatus('error', reason + ' â€” try again');
    startFaceWebcam();
  }

  function setFaceStatus(state, text) {
    const ind = document.getElementById('face-indicator');
    const txt = document.getElementById('face-status-text');
    if (ind) ind.className = `status-indicator ${state}`;
    if (txt) txt.textContent = text;
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     FACE â€” PHONE QR
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function startFaceQR() {
    showScreen('face-qr');
    const blink  = document.getElementById('face-qr-blink');
    const status = document.getElementById('face-qr-status');
    if (blink)  blink.style.background  = 'var(--amber)';
    if (status) status.textContent = 'Generating QR code...';
    callApi('start_face_qr_poll');
  }

  function renderFaceQR(url) {
    const loading = document.getElementById('face-qr-loading');
    const codeEl  = document.getElementById('face-qr-code');
    if (loading) loading.style.display = 'none';
    if (codeEl) {
      codeEl.style.display = 'block';
      codeEl.innerHTML = '';
      try {
        new QRCode(codeEl, {
          text: url, width: 180, height: 180,
          colorDark: '#0a0f1e', colorLight: '#ffffff',
          correctLevel: QRCode.CorrectLevel.M,
        });
      } catch(e) {
        codeEl.innerHTML = `<div style="font-size:9px;padding:8px;word-break:break-all">${url}</div>`;
      }
    }
    const status = document.getElementById('face-qr-status');
    const blink  = document.getElementById('face-qr-blink');
    if (status) status.textContent = 'Scan with your phone';
    if (blink)  blink.style.background = 'var(--accent)';
    setFaceTimerBar(120);
  }

  function setFaceTimerBar(seconds) {
    const bar   = document.getElementById('face-timer-bar');
    const label = document.getElementById('face-qr-timer');
    if (!bar) return;
    bar.style.transition = 'none';
    bar.style.width = '100%';
    updateFaceTimer(seconds);
  }

  function updateFaceTimer(remaining) {
    const bar   = document.getElementById('face-timer-bar');
    const label = document.getElementById('face-qr-timer');
    if (!bar || !label) return;
    bar.style.transition = 'width 2s linear';
    bar.style.width = Math.max(0, (remaining / 120) * 100) + '%';
    const m = Math.floor(remaining / 60);
    const s = remaining % 60;
    label.textContent = `${m}:${String(s).padStart(2,'0')}`;
    if (remaining < 30) bar.style.background = 'var(--amber)';
    if (remaining < 10) bar.style.background = 'var(--red)';
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     FINGERPRINT â€” QR
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function startFingerQR() {
    showScreen('finger');
    const blink  = document.getElementById('qr-blink');
    const status = document.getElementById('qr-status-text');
    if (blink)  blink.style.background  = 'var(--amber)';
    if (status) status.textContent = 'Generating QR code...';
    callApi('start_finger_poll');
  }

  function renderQR(url) {
    const loading = document.getElementById('qr-loading');
    const codeEl  = document.getElementById('qr-code');
    if (loading) loading.style.display = 'none';
    if (codeEl) {
      codeEl.style.display = 'block';
      codeEl.innerHTML = '';
      try {
        new QRCode(codeEl, {
          text: url, width: 180, height: 180,
          colorDark: '#0a0f1e', colorLight: '#ffffff',
          correctLevel: QRCode.CorrectLevel.M,
        });
      } catch(e) {
        codeEl.innerHTML = `<div style="font-size:9px;padding:8px;word-break:break-all">${url}</div>`;
      }
    }
    const status = document.getElementById('qr-status-text');
    const blink  = document.getElementById('qr-blink');
    if (status) status.textContent = 'Scan with your phone to authenticate';
    if (blink)  blink.style.background = 'var(--accent)';
    setTimerBar(120);
  }

  function setTimerBar(seconds) {
    const bar = document.getElementById('timer-bar');
    if (!bar) return;
    bar.style.background = 'linear-gradient(90deg, var(--accent), var(--cyan))';
    bar.style.transition = 'none';
    bar.style.width = '100%';
    updateTimer(seconds);
  }

  function updateTimer(remaining) {
    const bar   = document.getElementById('timer-bar');
    const label = document.getElementById('qr-timer');
    if (!bar || !label) return;
    bar.style.transition = 'width 2s linear';
    bar.style.width = Math.max(0, (remaining / 120) * 100) + '%';
    const m = Math.floor(remaining / 60);
    const s = remaining % 60;
    label.textContent = `${m}:${String(s).padStart(2,'0')}`;
    if (remaining < 30) bar.style.background = 'var(--amber)';
    if (remaining < 10) bar.style.background = 'var(--red)';
  }

  function onQRExpired() {
    const status = document.getElementById('qr-status-text');
    const blink  = document.getElementById('qr-blink');
    const bar    = document.getElementById('timer-bar');
    if (status) status.textContent = 'QR expired â€” go back and try again';
    if (blink)  blink.style.background = 'var(--red)';
    if (bar)    { bar.style.width = '0%'; bar.style.background = 'var(--red)'; }
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     VERIFIED â€” any method leads here
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function onVerified() {
    stopCamera();
    callApi('stop_face_poll');
    callApi('stop_finger_poll');

    const methodMap = {
      'face':       'Face Â· Webcam',
      'face-qr':    'Face Â· Phone Camera',
      'finger':     'Fingerprint Â· Phone',
    };
    const label = methodMap[currentScreen] || 'Biometric';
    document.getElementById('success-method').textContent =
      'Authenticated via ' + label.toUpperCase();

    // BUG FIX: animatsiyani force-restart
    const bar  = document.querySelector('#screen-success .success-bar');
    const ring = document.querySelector('#screen-success .success-ring');
    if (bar)  { bar.style.animation  = 'none'; bar.offsetHeight;  bar.style.animation  = ''; }
    if (ring) { ring.style.animation = 'none'; ring.offsetHeight; ring.style.animation = ''; }

    showScreen('success', false);

    // BUG FIX: setTimeout + fallback
    let _done = false;
    const _hide = () => { if (_done) return; _done = true; callApi('hide_lock'); };
    setTimeout(_hide, 2500);
    setTimeout(_hide, 4500); // fallback
  }

  /* â”€â”€ Error â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  function onOfflineMode() {
    if (config.has_offline) {
      showScreen('offline-admin', false);
      return;
    }
    if (config.has_personal_offline) {
      showScreen('offline', false);
      return;
    }
    setInitStatus("Internet yo'q. IT administratorga murojaat qiling.");
    showScreen('init', false);
  }

  function onSessionError(msg) {
    setInitStatus('Session error: ' + msg);
    showScreen('init', false);
  }

  function onEnrollmentRequired() {
    config.activated = false;
    stopCamera();
    callApi('stop_face_poll');
    callApi('stop_finger_poll');
    screenStack = [];
    showScreen('setup', false);
  }

  function onError(msg) { setInitStatus('Error: ' + msg); }

  /* â”€â”€ Blocked (doc 05) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  function onBlocked(message) {
    stopCamera();
    callApi('stop_face_poll');
    callApi('stop_finger_poll');
    const el = document.getElementById('blocked-message');
    if (el) el.textContent = message;
    showScreen('blocked', false);
  }

  /* â”€â”€ Auto-lock warning (doc 04) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  function onAutolockWarning(secondsLeft) {
    const overlay = document.getElementById('autolock-overlay');
    const countdown = document.getElementById('autolock-countdown');
    if (!overlay) return;
    overlay.style.display = 'flex';
    if (countdown) countdown.textContent = secondsLeft;
    // countdown ticker
    let remaining = secondsLeft;
    const tick = setInterval(() => {
      remaining--;
      if (countdown) countdown.textContent = Math.max(0, remaining);
      if (remaining <= 0) clearInterval(tick);
    }, 1000);
    overlay._tick = tick;
  }

  async function extendSession() {
    const overlay = document.getElementById('autolock-overlay');
    if (overlay) {
      if (overlay._tick) clearInterval(overlay._tick);
      overlay.style.display = 'none';
    }
    await callApi('extend_session');
  }

  /* â”€â”€ Offline login (doc 06) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  function onOfflineRetry(message) {
    // Shaxsiy offline ekrani
    const row = document.getElementById('offline-status-row');
    const txt = document.getElementById('offline-status-text');
    const btn = document.getElementById('offline-submit-btn');
    if (row) row.style.display = 'flex';
    if (txt) txt.textContent = message;
    if (btn) { btn.disabled = false; btn.innerHTML = 'â†’ &nbsp; Kirish'; }
    // Admin offline ekrani
    const arow = document.getElementById('offline-admin-status-row');
    const atxt = document.getElementById('offline-admin-status-text');
    const abtn = document.getElementById('offline-admin-btn');
    if (arow) arow.style.display = 'flex';
    if (atxt) atxt.textContent = message;
    if (abtn) { abtn.disabled = false; abtn.innerHTML = 'â†’ &nbsp; Kirish'; }
  }

  // Org admin â€” adauth.tech login/parol
  async function submitAdminOfflineLogin() {
    const username = document.getElementById('offline-admin-username')?.value?.trim();
    const password = document.getElementById('offline-admin-password')?.value;
    if (!username || !password) {
      onOfflineRetry('Login va parol kiritilishi shart');
      return;
    }
    const btn = document.getElementById('offline-admin-btn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<div class="spinner" style="display:inline-block"></div> &nbsp; Tekshirilmoqda...'; }
    const row = document.getElementById('offline-admin-status-row');
    if (row) row.style.display = 'none';
    await callApi('offline_login', username, password);
  }

  // Shaxsiy â€” foydalanuvchi o'zi o'rnatgan parol
  async function submitOfflineLogin() {
    const password = document.getElementById('offline-password')?.value;
    if (!password) {
      onOfflineRetry('Parol kiritilishi shart');
      return;
    }
    const btn = document.getElementById('offline-submit-btn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<div class="spinner" style="display:inline-block"></div> &nbsp; Tekshirilmoqda...'; }
    const row = document.getElementById('offline-status-row');
    if (row) row.style.display = 'none';
    await callApi('personal_offline_login', password);
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     ADMIN PANEL
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  let _adminToken = '';
  let _refreshInterval = null;

  function showAdminLogin() {
    showScreen('admin-login', false);
    // parol inputni tozalaymiz
    const pw = document.getElementById('admin-panel-pw');
    if (pw) pw.value = '';
    const err = document.getElementById('admin-panel-error');
    if (err) err.style.display = 'none';
    const btn = document.getElementById('admin-panel-btn');
    if (btn) { btn.disabled = false; btn.innerHTML = 'â†’ &nbsp; Kirish'; }
  }

  async function submitAdminPanelLogin() {
    const pw  = document.getElementById('admin-panel-pw')?.value;
    const btn = document.getElementById('admin-panel-btn');
    const err = document.getElementById('admin-panel-error');
    if (!pw) {
      if (err) { err.style.display = 'flex'; err.querySelector('.status-text').textContent = 'Parol kiritilishi shart'; }
      return;
    }
    if (btn) { btn.disabled = true; btn.innerHTML = '<div class="spinner" style="display:inline-block"></div> &nbsp; Tekshirilmoqda...'; }
    if (err) err.style.display = 'none';
    await callApi('admin_login', pw);
  }

  function onAdminLoginOk(token) {
    _adminToken = token;
    showScreen('admin-panel', false);
    _loadAndRenderPeers();
    // Har 15 sek yangilash
    if (_refreshInterval) clearInterval(_refreshInterval);
    _refreshInterval = setInterval(_refreshAllPeers, 15000);
  }

  function onAdminLoginFail(msg) {
    const btn = document.getElementById('admin-panel-btn');
    const err = document.getElementById('admin-panel-error');
    if (btn) { btn.disabled = false; btn.innerHTML = 'â†’ &nbsp; Kirish'; }
    if (err) { err.style.display = 'flex'; err.querySelector('.status-text').textContent = msg; }
  }

  async function _loadAndRenderPeers() {
    const raw     = await callApi('get_lan_peers');
    const peers   = JSON.parse(raw || '[]');
    _renderPeers(peers);
    // Har bir peer holatin yangilash
    _refreshAllPeers();
  }

  function _refreshAllPeers() {
    const rows = document.querySelectorAll('[data-peer-ip]');
    rows.forEach(row => {
      const ip = row.getAttribute('data-peer-ip');
      if (ip) callApi('refresh_lan_peer', ip);
    });
  }

  function onPeerUpdated(raw) {
    try {
      const peer = JSON.parse(raw);
      _updatePeerRow(peer);
    } catch(e) {}
  }

  function onPeerOffline(ip) {
    const row = document.querySelector(`[data-peer-ip="${ip}"]`);
    if (row) {
      const stateEl = row.querySelector('.admin-peer-state');
      if (stateEl) stateEl.innerHTML = 'âš« OFFLINE';
      stateEl.style.color = 'var(--text-muted)';
    }
  }

  function onLanResult(ip, cmd, ok) {
    // Holat yangilansin
    setTimeout(() => callApi('refresh_lan_peer', ip), 1500);
  }

  function onLanAllDone() {
    setTimeout(_refreshAllPeers, 1500);
  }

  function _stateInfo(state) {
    if (state === 'locked')   return { dot: 'ðŸ”´', text: 'LOCKED',   color: 'var(--red)'       };
    if (state === 'unlocked') return { dot: 'ðŸŸ¢', text: 'ACTIVE',   color: 'var(--green)'     };
    if (state === 'disabled') return { dot: 'ðŸŸ¡', text: 'DISABLED', color: 'var(--amber)'     };
    return                           { dot: 'âš«', text: 'OFFLINE',  color: 'var(--text-muted)' };
  }

  function _renderPeers(peers) {
    const list = document.getElementById('admin-peer-list');
    const cnt  = document.getElementById('admin-peer-count');
    if (!list) return;
    if (cnt) cnt.textContent = peers.length ? `${peers.length} ta qurilma` : '';

    if (peers.length === 0) {
      list.innerHTML = `<div class="admin-empty font-mono">
        <div class="spinner" style="margin:0 auto 12px"></div>
        LAN qurilmalar qidirilmoqda...
      </div>`;
      return;
    }

    list.innerHTML = peers.map(p => _peerRowHTML(p)).join('');
  }

  function _peerRowHTML(p) {
    const s   = _stateInfo(p.state || 'offline');
    const ip  = p.ip || '';
    const id  = ip.replace(/\./g, '-');
    const dis = p.state === 'disabled';
    const off = p.state === 'offline';
    return `
    <div class="admin-peer-row" data-peer-ip="${ip}" id="peer-${id}">
      <div class="admin-peer-info">
        <div class="admin-peer-name">${p.pc_name || ip}</div>
        <div class="admin-peer-meta font-mono">${ip}&nbsp;Â·&nbsp;${p.username || ''}</div>
      </div>
      <div class="admin-peer-state" style="color:${s.color}">${s.dot} ${s.text}</div>
      <div class="admin-peer-actions">
        ${off ? '' : dis
          ? `<button class="btn btn-sm btn-ghost" onclick="App.peerEnable('${ip}')">â–¶ Enable</button>`
          : `<button class="btn btn-sm btn-ghost" onclick="App.peerDisable('${ip}')">â¸ Disable</button>`
        }
      </div>
    </div>`;
  }

  function _updatePeerRow(peer) {
    const ip  = peer.ip || '';
    const id  = ip.replace(/\./g, '-');
    const row = document.getElementById(`peer-${id}`);
    if (row) {
      row.outerHTML = _peerRowHTML(peer);
    } else {
      // Yangi peer â€” ro'yxatga qo'shamiz
      const list = document.getElementById('admin-peer-list');
      const empty = list?.querySelector('.admin-empty');
      if (empty) empty.remove();
      if (list) list.insertAdjacentHTML('beforeend', _peerRowHTML(peer));
      // Count yangilash
      const cnt = document.getElementById('admin-peer-count');
      if (cnt) {
        const rows = document.querySelectorAll('[data-peer-ip]').length;
        cnt.textContent = `${rows} ta qurilma`;
      }
    }
  }

  async function peerDisable(ip) {
    await callApi('lan_command', ip, 'disable');
  }

  async function peerEnable(ip) {
    await callApi('lan_command', ip, 'enable');
  }

  async function disableAll() {
    const cnt = document.querySelectorAll('[data-peer-ip]').length;
    if (!cnt) return;
    _showConfirm(
      `Barcha ${cnt} ta qurilmani vaqtincha o'chirishni tasdiqlaysizmi?`,
      async () => { await callApi('lan_command_all', 'disable'); }
    );
  }

  function closeAdminPanel() {
    if (_refreshInterval) { clearInterval(_refreshInterval); _refreshInterval = null; }
    showScreen('select', false);
  }

  // â”€â”€ Confirm modal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  let _confirmCallback = null;

  function _showConfirm(msg, onYes) {
    _confirmCallback = onYes;
    const modal = document.getElementById('admin-confirm-modal');
    const txt   = document.getElementById('admin-confirm-msg');
    if (txt)   txt.textContent = msg;
    if (modal) modal.style.display = 'flex';
  }

  async function confirmYes() {
    document.getElementById('admin-confirm-modal').style.display = 'none';
    if (_confirmCallback) { await _confirmCallback(); _confirmCallback = null; }
  }

  function confirmNo() {
    document.getElementById('admin-confirm-modal').style.display = 'none';
    _confirmCallback = null;
  }

  /* â”€â”€ Dev â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  async function devUnlock() {
    try { await pywebview.api.dev_unlock(); }
    catch(e) { onVerified(); }
  }
  async function devExit() {
    try { await pywebview.api.dev_exit(); }
    catch(e) { window.close(); }
  }

  /* â”€â”€ Clock â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  function startClock() {
    const el = document.getElementById('header-clock');
    const tick = () => {
      el.textContent = new Date().toLocaleTimeString('en-GB',
        { hour:'2-digit', minute:'2-digit', second:'2-digit' });
    };
    tick(); setInterval(tick, 1000);
  }

  /* â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  function setInitStatus(text) {
    const el = document.getElementById('init-status');
    if (el) el.textContent = text;
  }

  function setStatus(state, text) { setFaceStatus(state, text); }

  async function callApi(method, ...args) {
    try {
      if (typeof pywebview !== 'undefined' && pywebview.api)
        return await pywebview.api[method](...args);
    } catch(e) { console.warn('API:', method, e); }
  }

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  /* â”€â”€ Boot â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  window.addEventListener('DOMContentLoaded', init);

  /* â”€â”€ Public â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  return {
    // Python chaqiradi
    onSessionReady, onFaceRetry, onVerified, onError,
    renderQR, renderFaceQR,
    updateTimer, updateFaceTimer,
    onQRExpired, setStatus,
    onBlocked, onAutolockWarning, onOfflineRetry,
    onActivated, onSetupStatus, onSetupError,
    onInternetLost, onInternetRestored, onOfflineMode, onSessionError, onEnrollmentRequired,
    onPersonalOfflineSet, onPersonalOfflineError,
    onAdminPasswordSet, onAdminPasswordError,
    onAdminLoginOk, onAdminLoginFail,
    onPeerUpdated, onPeerOffline,
    onLanResult, onLanAllDone,
    // HTML chaqiradi
    showScreen,
    selectMethod,
    showSetupOrg, showSetupPersonal,
    submitOrgActivation, submitPersonalActivation,
    submitAdminPasswordSetup,
    submitOfflineSetup, skipOfflineSetup,
    startFaceWebcam, startFaceQR,
    startFingerQR,
    captureFrame, goBack,
    extendSession,
    submitOfflineLogin,
    submitAdminOfflineLogin,
    showAdminLogin,
    submitAdminPanelLogin,
    peerDisable, peerEnable, disableAll,
    closeAdminPanel,
    confirmYes, confirmNo,
    devUnlock, devExit,
  };

})();


