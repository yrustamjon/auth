# ADAuth frontend

React + Vite orqali ochiq mahsulot sayti va alohida admin/superadmin paneli. Django API, sessiya cookie va CSRF bilan ishlaydi.

## Ishga tushirish (Windows / PowerShell)

Yangi frontendni Django portidan, jumladan ngrok bilan ochish:

```powershell
# Bir terminalda:
ngrok http 8000
# Loyiha ildizidagi boshqa terminalda:
$env:PUBLIC_SITE_URL = 'https://sizning-manzilingiz.ngrok-free.dev'
cd frontend
npm.cmd run build
cd ..
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Ngrok havolasi va http://localhost:8000 yangi frontendni ochadi. Ngrok manzili o'zgarsa, PUBLIC_SITE_URL qiymatini yangilab Django'ni qayta ishga tushiring.
cd frontend
npm.cmd run build
cd ..
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 -PublicUrl https://sizning-manzilingiz.ngrok-free.dev`. Ngrok manzili o'zgarsa, serverni shu skript bilan qayta ishga tushiring. `8000` portidagi avvalgi serverni Ctrl+C bilan to'xtatib keyin skriptni oching.

Eski template fayllari saqlangan. Eski interfeysga qaytish uchun `$env:SERVE_FRONTEND='0'` bilan Django'ni oddiy ishga tushiring. `SERVE_FRONTEND=1` odatiy holat. API va `/admin/` Django'da qoladi. Quyidagi Vite usuli frontendni ishlab chiqish uchun hamon mavjud.

Loyiha ildizidan backend:

```powershell
$env:PUBLIC_SITE_URL = 'http://localhost:5173'
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Bu kompyuterda venv Python manzili eskirgan bo'lsa, mavjud pgAdmin Python bilan:

```powershell
& 'C:\Program Files\PostgreSQL\18\pgAdmin 4\python\python.exe' frontend/tools/run_django.py runserver 127.0.0.1:8000
```

Boshqa terminalda:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Frontend: http://localhost:5173. `/` ochiq bosh sahifa; `/product`, `/downloads`, `/guide` va `/device/scan` loginsiz ochiladi. Login `/` ustida modal: `/?login=admin` yoki `/?login=superadmin`. Eski `/login` va `/system/login` havolalari shu modalga yo'naltiriladi; panel va QR tasdiqlash davomiyligi saqlanadi. Vite /api so'rovlarini http://127.0.0.1:8000 ga uzatadi. Backend manzilini VITE_BACKEND_TARGET bilan o'zgartirish mumkin.

PUBLIC_SITE_URL frontendning tashqi manzili bo'lishi kerak: QR, helper va WebAuthn shu origin asosida ishlaydi. localhost va 127.0.0.1 ni aralashtirmang. Haqiqiy telefonda localhost kompyuterni anglatmaydi: frontend va /api uchun bitta ommaviy HTTPS manzilini ishlating, Django PUBLIC_SITE_URL, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS va CORS sozlamalarini shu manzilga moslang.

## Imkoniyatlar

- O'zbekcha, och rangli, mobil menyu va umumiy dizayn.
- `/` ustida `/?register=personal` yoki `/?register=company` orqali ro'yxatdan o'tish oynasi.
- Shaxsiy hisob: native yordamchi bilan PC aniqlanadi, hisob va alohida ish maydoni birgalikda yaratiladi. Qurilma Agent aktivatsiyasigacha nofaol qoladi.
- Shaxsiy UI: hisob ma'lumotlari → PC aniqlash → hisob yaratish → `/personal/biometrics` → `/personal/computer` orqali haqiqiy Agent va aktivatsiya tokeni. `/personal/history` faqat o'z profilining so'nggi 100 kirishini ko'rsatadi. Kompaniya rollari/foydalanuvchilari shaxsiy menyuda ko'rsatilmaydi. Token faqat tugma bosilganda olinadi va brauzer storage'iga yozilmaydi.
- Kompaniya: ariza pending holatda, `/registration/status` orqali holat tekshiriladi. Superadmin `/system/applications` sahifasidan tasdiqlaydi yoki rad etadi. Mavjud kompaniya PC QR oqimi o'sha kompaniya administratorining tasdig'ini talab qiladi.
- `/downloads`: haqiqiy mahsulot o'rnatuvchisi. Backend `AGENT_RELEASE_DIR` orqali katalogni o'qiydi; default `../agent/releases`. Windows 1.0.3 mavjud; Linux/macOS 0.0.0 placeholderlar yuklanadigan paket deb ko'rsatilmaydi. `VERSION` va mos versiya papkasidagi `manifest.json` hamda paket talab qilinadi. Sinov versiyasi belgisi saqlanadi.
- Sessiya tekshiruvi, panelga mos login/logout, tashkilot almashtirish.
- Foydalanuvchi, rol, qurilma, log, tashkilot va administrator sahifalari.
- Yuz yuklash/o'chirish, saqlangan biometrik yozuvlar, telefon orqali tasdiqlash.
- /device/scan: native yordamchini yuklash, identity holati, QR va tasdiqlash kodi.
- /devices/scan-qr/: kamera skaneri (BarcodeDetector mavjud bo'lsa) yoki havolani kiritish.
- /device-enroll/:token va /device-enroll/approval/: sessiya, tashkilot, kod, joylashuv, approve/reject.
- /mobile/fingerprint/:sessionId/: yuz tekshiruvi va server challenge asosidagi WebAuthn.

QR tasdiqlangan qurilma Agent ulanishigacha faol bo'lmaydi. Yordamchi binarylar backenddagi DEVICE_REGISTRATION_HELPER_DIR orqali avvalgi kabi ta'minlanadi. Telefon kamerasidan ham QR havolani ochish mumkin. USB skaner yoki tashqi tizimdan yangi biometrik yozuv kiritish uchun mavjud backend API yo'q; saqlangan yozuvlar ko'rinadi.

## Tekshiruvlar

Eski template route shartlarini ham tekshiradigan Django to'plami uchun `$env:SERVE_FRONTEND='0'` belgilang. `apps.common.test_frontend_serving` yangi frontendni alohida `SERVE_FRONTEND=True` bilan tekshiradi. Ishlayotgan yangi serverda `cd frontend; node tools/check-served-site.mjs` brauzer tekshiruvini bajaradi.

```powershell
npm.cmd run lint
npm.cmd run build
npm.cmd test
npm.cmd run test:e2e
```

E2E testlar mahalliy Chrome'ni headless rejimda ishlatadi; ishlab turgan Django bazasiga yozmaydi. UI testlar API fixturelarini ishlatadi. Backend integration testlar vaqtinchalik Django test bazasida sessiya/CSRF, QR vakolat/expiry/duplicate va WebAuthn optionsni tekshiradi.

```powershell
& 'C:\Program Files\PostgreSQL\18\pgAdmin 4\python\python.exe' frontend/tools/run_django.py test apps.common.test_frontend_session apps.device.test_frontend_enrollment apps.biometrik.test_frontend_options --noinput
```

## Production

Backendni yangilaganda `manage.py migrate` orqali yangi organization kind/review maydonlarini qo'llang. Mavjud tashkilotlar company/approved bo'lib qoladi. `AGENT_RELEASE_DIR` productionda haqiqiy release katalogiga yo'naltiriladi; katalog read-only bo'lishi mumkin. Yangi paket e'lon qilishda SHA-256 manifest bilan tekshirilsin.

npm run build natijasi dist papkasiga yoziladi. Web server statik dist fayllarini bersin; React route'lari (jumladan /device-enroll/ va /mobile/fingerprint/) uchun index.html fallback ishlasin. /api/ Django'ga proxy qilinadi, /admin/ esa Django adminiga yo'naltiriladi. Backend /device-enroll/ HTML route'lari mavjud bo'lib qoladi, ammo yangi frontendni beradigan serverda SPA route ustuvor bo'lishi kerak.

Kamera/WebAuthn HTTPS talab qiladi (loopback dev istisno). PUBLIC_SITE_URL aynan foydalanuvchi ochadigan HTTPS origin bilan bir xil bo'lishi kerak. Mavjud DB schema o'zgarmaydi.
