# Frontend Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Zamonaviy, o'zbekcha va mobilga mos React admin hamda superadmin panelini Django API bilan yakunlash.

**Architecture:** Mavjud React ilovasi umumiy dizayn tokenlari, sahifa karkasi va boshqaruv komponentlariga o'tadi. Sessiya va CSRF Django orqali boshqariladi; API adapterlari backendning haqiqiy javoblariga mos keladi. QR va telefon biometrik oqimlari mavjud backend protokolini ishlatadi.

**Tech Stack:** React, Vite, React Router, Axios, Lucide, mavjud Tailwind va Django REST Framework. Funksional tekshiruvlar uchun Node test runner va Django testlari; brauzerda vizual tekshiruv.

**Spec:** `docs/superpowers/specs/2026-10-10-frontend-modernization-design.md`

## Global Constraints

- Och kulrang sahifa foni (#f5f7fb), oq panellar, to'q ko'k asosiy matn (#152238), ko'k aksent (#2563eb).
- 240px yon menyu, yuqorida sahifa nomi va hisob menyusi; mobil ekranda tugma bilan ochiladigan navigatsiya.
- Interfeys matnlari o'zbekcha; klaviatura fokusi, tugma nomlari, Escape bilan modal yopish va harakatni kamaytirish sozlamasi.
- API bermagan foiz va xizmat holatlari ko'rsatilmaydi.
- Agent dasturi va uning protokoli o'zgartirilmaydi.
- Foydalanuvchining joriy o'zgarishlari saqlanadi.

## Review Focus

1. Sessiya muddati tugashi, login xatosi va panel vakolatlari: login xatosi ko'rinadi, admin superadmin paneliga o'tmaydi (Task 2).
2. Qisman API xatosi: mavjud statistika saqlanadi, muvaffaqiyatsiz statistika nol bo'lib ko'rinmaydi (Task 3).
3. 390px ekran va klaviatura: menyu/modal boshqariladi, sahifa tashqarisiga kontent chiqmaydi (Task 1).
4. QR muddati tugashi yoki ikki marta tasdiqlash: frontend backendning yakuniy holatini ko'rsatadi, polling to'xtaydi (Task 5).
5. Telefon localhostdan tashqarida ochilishi va komponent yopilishi: havola public frontend manzilidan tuziladi, polling tozalanadi (Task 6).

## Fayllar mas'uliyati

`src/index.css` va `tailwind.config.js`: tokenlar va moslashuvchan stillar. `components/AppShell.jsx`: admin/superadmin umumiy karkasi. `components/LoginForm.jsx`: umumiy login. `components/ProtectedRoute.jsx`: sessiya va panel tekshiruvi. `api/contracts.js`: API javoblarini talqin qilish. `api/enrollment.js`: QR API. `pages/DeviceScan.jsx`, `pages/DeviceApproval.jsx`, `pages/MobileFingerprint.jsx`: tashqi qurilma/telefon oqimlari. Backendda faqat frontend talab qilgan sessiya/CSRF va ma'lumot API'lari qo'shiladi; mavjud agent endpointlari saqlanadi.

### Task 1: Dizayn tizimi va ikkala panel karkasi

**Files:** Modify `frontend/src/index.css`, `frontend/tailwind.config.js`, `frontend/src/layouts/AdminLayout.jsx`, `frontend/src/layouts/SystemLayout.jsx`, `frontend/src/components/{Sidebar,Header,Table,Modal,Badge,StatCard,Toast}.jsx`; create `frontend/src/components/AppShell.jsx`.

**Interfaces:** `AppShell({ panel: 'admin'|'superadmin', children })` navigatsiya va hisob menyusini beradi. Mavjud Table/Modal/Toast prop interfeyslari saqlanadi.

- [ ] Tokenlar, och panellar, forma/jadval stillari, 12–16px radius va o'zbekcha holat matnlarini yozish; ortiqcha CSS fallbacklarini tozalash.
- [ ] AppShell yozish: 240px desktop sidebar, mobil drawer, sahifa sarlavhasi, logout; ishlamaydigan qidiruv/bildirishnoma dekorlarini olib tashlash.
- [ ] Ikkala layoutni AppShellga ulash; to'q inline stillarni komponentlardan chiqarish.
- [ ] Modalga dialog semantikasi, fokusni ichida saqlash, Escape va fokusni qaytarishni qo'shish; nested modalda scroll holatini saqlash.
- [ ] `npm.cmd run build` muvaffaqiyatini tekshirish. Brauzerda 390px/1440px karkas, menyu, modal, uzun sarlavha, Tab/Escape, reduced motionni tekshirish.
- [ ] Faqat shu task fayllarini commit qilish.

### Task 2: Login, sessiya va CSRF

**Files:** Modify `apps/common/urls.py`, `apps/common/views.py`, `frontend/src/api/{client,auth}.js`, `frontend/src/pages/Login.jsx`, `frontend/src/pages/system/SystemLogin.jsx`, `frontend/src/App.jsx`; create `frontend/src/components/{LoginForm,ProtectedRoute}.jsx`, `apps/common/test_frontend_session.py`.

**Interfaces:** `GET /api/session/` CSRF cookie o'rnatadi; JSON `{authenticated: boolean, panel: 'admin'|'superadmin'|null, user: {id, username}|null, organization_id: number|null, organizations: [{id,name}]}`. `getSession()` shu javobni oladi. `ProtectedRoute({panel,children})` yuklanish paytida kontentni ochmaydi. `LoginForm({panel})` mavjud login endpointlarini ishlatadi.

- [ ] Django testlarida anonim sessiya 200 va csrf cookie, authenticated panel/org, logoutdan keyin anonymous; yuborilgan noto'g'ri parol xatosini tekshirish.
- [ ] Testlar fail bo'lishini `venv/Scripts/python.exe manage.py test apps.common.test_frontend_session --noinput` bilan tasdiqlash; mavjud Python muhitidan foydalanish.
- [ ] Sessiya endpointini qo'shish; login oldidan CSRF olish; global interceptor login so'rovini qayta yo'naltirmasligi, sessiya xatosini login xatosidan ajratishi.
- [ ] Umumiy och rangli login, yuborish bloki, parol ko'rish, backend xato matni va sessiyaga mos route himoyasini yozish. Panel mezoni request.session.panel asosida tekshiriladi.
- [ ] Testlar pass, build pass; brauzerda noto'g'ri login, refresh, logout, to'g'ridan-to'g'ri URL va noto'g'ri panelni tekshirish.
- [ ] Faqat task fayllarini commit qilish.

### Task 3: Dashboardlar va API javoblari

**Files:** Create `frontend/src/api/contracts.js`, `frontend/test/contracts.test.mjs`; modify `frontend/src/pages/Dashboard.jsx`, `frontend/src/pages/system/SystemDashboard.jsx`, `frontend/src/api/{admin,superadmin}.js`.

**Interfaces:** `readCollection(payload, key?) -> Array` bare array yoki ko'rsatilgan kalitdagi arrayni oladi, noto'g'ri shaklda Error chiqaradi. `readMetric(settledResult, key?) -> {value: number|null, error: string|null}`. Organization UI backendning `active` maydonini ishlatadi.

- [ ] `node:test` bilan array, `{users:[]}`, empty array, noto'g'ri payload va rejected request uchun assertions yozish: rejected qiymat `null`, empty muvaffaqiyat qiymati `0`.
- [ ] `node --test frontend/test/contracts.test.mjs` fail ekanini tekshirish.
- [ ] Adapterlar va dashboardlarni yozish; haqiqiy sonlar, muvaffaqiyatsiz kartada xato, oxirgi loglar va tashkilotlar. Faol tashkilotlar sonini barcha tashkilotlardan hisoblash, faqat oxirgi 6 tadan emas.
- [ ] Soxta trendlar, xizmat Online holatlari va backend bermagan ko'rsatkichlarni olib tashlash.
- [ ] Node testlar va build pass; brauzerda qisman API failure va empty holatni ko'rish.
- [ ] Task fayllarini commit qilish.

### Task 4: CRUD sahifalari va biometrik modal dizayni

**Files:** Modify `frontend/src/pages/{Users,Roles,Devices,Logs}.jsx`, `frontend/src/pages/system/{Organizations,Admins}.jsx`, `frontend/src/api/{admin,superadmin}.js`; create `frontend/test/api-contracts.test.mjs`.

**Interfaces:** Mavjud exported API funksiya nomlari saqlanadi; URL, metod va payload backend route/viewga mos keladi. Reset attempts kabi backendda yo'q endpoint ishlatilmaydi; backenddagi mavjud unlock/reset amali bilan moslash yoki UI amalini olib tashlash.

- [ ] Har bir amaldagi viewning get/post/put/patch/delete payloadini frontend bilan jadval sifatida solishtirish; Users va Admins maydonlarini, organization.active, device enrollment holatini tekshirish.
- [ ] HTTP chaqiruvlari uchun request adapter orqali kutilgan URL/metod/payloadni assertions bilan tekshiradigan Node test yozish; topilgan nomuvofiqliklarda avval fail olish.
- [ ] API mosligini tuzatish, CRUD sahifalarini tokenlarga o'tkazish, o'zbekcha qidiruv/natija soni/empty/xato/saqlash holatlari, accessibility yorliqlari va delete tasdig'ini yangilash.
- [ ] Biometrics modalining tab, upload va natija stillarini yangilash; qo'llab-quvvatlanmaydigan skaner amallarini ishlaydigan amal sifatida ko'rsatmaslik.
- [ ] Node testlar, lint, build pass; browserda jadval, create/edit/delete tasdiqlari va API validation xatosini tekshirish. Testlar foydalanuvchining haqiqiy ma'lumotini o'zgartirmasligi kerak.
- [ ] Task fayllarini commit qilish.

### Task 5: QR qurilma oqimini Reactga ko'chirish

**Files:** Create `frontend/src/api/enrollment.js`, `frontend/src/pages/{DeviceScan,DeviceApproval,DeviceScanner}.jsx`, `frontend/src/api/enrollment-state.js`, `frontend/test/enrollment-state.test.mjs`, `apps/device/test_frontend_enrollment.py`; modify `frontend/src/App.jsx`, `frontend/src/pages/Devices.jsx`, `apps/device/browser_views.py`, `apps/device/urls.py`, `frontend/vite.config.js`.

**Interfaces:** Existing `/api/devices/browser-enrollment/session/` va uning status/identity/helper/approve/reject/cancel route'lari saqlanadi. React `/device/scan`, `/devices/scan-qr/`, `/device-enroll/:token`, `/device-enroll/approval/` route'larini beradi. `isTerminalEnrollment(status) -> boolean` backend modeldagi yakuniy holatlardan olinadi. Template context olishga bog'langan claim/approval uchun JSON API backenddagi mavjud `claim`, `permitted_admin`, `resolve` xizmatlariga delegatsiya qiladi.

- [ ] `templates/device_scan.html`, `device_qr_scanner.html`, `device_enroll_approval.html` va browser_views/service holat mashinasini o'qish; kamera HTTPS cheklovi va helper download oqimini saqlash.
- [ ] Django testlarida anonymous claim/login continuation, boshqa admin/org, expired token, duplicate approve, CSRF; Node testda terminal holat pollingni to'xtatishini tekshirish. Yangi JSON viewlar yo'qligida fail olish.
- [ ] Kerakli JSON context/claim endpointlarini minimal qo'shish; Reactda QR ko'rsatish, helper yuklash, identity kutish, kamera skanerlash yoki qo'lda URL kiritish, kod solishtirish va approve/reject/cancel UI.
- [ ] Public QR URL frontend originidan tuzilishi va token login paytida saqlanishini ta'minlash; mavjud qr_url tokenini o'zgartirmaslik. Helper endpointlarining cookie/CSRF talablari saqlanadi.
- [ ] Django va Node testlar pass; browserda yaratilish, expiry, tasdiqlash, rad etish, logout/login davom ettirish va polling cleanupni tekshirish.
- [ ] Task fayllarini commit qilish; foydalanuvchining devices backend/test o'zgarishlarini alohida saqlash.

### Task 6: Telefon biometrik sahifasi va yakuniy tekshiruv

**Files:** Create `frontend/src/pages/MobileFingerprint.jsx`, `frontend/src/api/public-links.js`, `frontend/test/public-links.test.mjs`; modify `frontend/src/pages/Users.jsx`, `frontend/src/App.jsx`, `frontend/src/api/admin.js`, `frontend/README.md`, `frontend/vite.config.js`, `frontend/index.html`.

**Interfaces:** React `/mobile/fingerprint/:sessionId/`; mavjud `/api/fingerprint/phone/submit/`, `/api/fingerprint/phone/status/:sessionId/`, `/api/face/phone/check/` payload/protokoli saqlanadi. `mobileFingerprintUrl(origin, sessionId) -> string` origin va UUIDdan URL yasaydi, localhostni hardcode qilmaydi.

- [ ] `templates/mobile_fingerprint.html`, `apps/biometrik/views.py`dan WebAuthn, face check va status oqimini o'qish; submit payload va capability holatlarini aniq saqlash.
- [ ] Node testda `https://auth.example` origin uchun shu hostdagi mobil URL va sessionIdni tekshirish; avval fail olish.
- [ ] React telefon sahifasi, unsupported browser/HTTPS xabari, holat va submit bloki; Users polling cleanup va haqiqiy session URLni yozish.
- [ ] READMEga Django 8000, Vite 5173, bir hostdan foydalanish, proxy, build va production SPA fallback/API routingni hujjatlashtirish. Brend title/faviconni yangilash.
- [ ] `npm.cmd run lint`, `npm.cmd run build`, `node --test frontend/test/*.test.mjs` va tegishli Django testlar pass; aniqlangan lint muammolarini o'zgartirilgan fayllarda tuzatish.
- [ ] Brauzerda ikkala panel, loginlar, har bir jadval/modal hamda QR/telefon sahifalarini 390px/1440px tekshirish; console xatolarini tekshirish. Server/hardware bo'lmasa tekshirilmagan jarayonlarni yakuniy hisobotda qayd etish.
- [ ] Diffni ko'rib faqat task fayllarini commit qilish; talablar va test dalillari bo'yicha yakuniy review, aniqlangan kamchiliklarni tuzatish.

## Reja self-review

Specning dizayn, til, responsive va accessibility talablari Task 1/2/4da; autentifikatsiya va API Task 2/3/4da; QR/telefon Task 5/6da; ishga tushirish va tekshiruv Task 6da qamralgan. Interfeyslar mavjud backend protokoliga moslanadi. Foydalanuvchining joriy o'zgarishlari commitga aralashtirilmaydi. Native bajarish tavsiya: bir xil dizayn va umumiy komponentlarga bog'liq tasklar ketma-ket shu sessiyada bajariladi.
