# Agent’dan oldingi QR device registration

Bu flow Windows, macOS va Linux uchun bir xil. Agent hali o‘rnatilmagan PC’da `/device/scan` ochiladi. Foydalanuvchi **Scan this PC** bosadi, standalone registration helper ZIP’i yuklanadi va uni bir marta ishga tushiradi. Helper OS identifierlarini avtomatik o‘qib, qisqa muddatli sessiyaga yuboradi. Shundan **keyingina** target sahifada QR ko‘rinadi. Admin Devices → QR skaner orqali QR’ni ochib, PC ma’lumotlarini ko‘radi; faqat Approve bosilganda `Device` yaratiladi.

Helper Agent emas, Agent repository’siga bog‘lanmagan va hech qanday servis o‘rnatmaydi. Brauzer yuklangan executable’ni avtomatik yoki yashirincha ishga tushira olmaydi. Windows/macOS security prompt chiqishi mumkin. Installer/preflight va keyingi Agent public-key enrollment bu flow’da yo‘q.

## Ishga tushirish

1. `req.text` dependency’larini o‘rnating (`qrcode==8.2` talab qilinadi) va `python manage.py migrate` bajaring.
2. `registration-helper/` ichida `make build` bajaring. Natija `registration-helper/dist/`da olti OS/architecture binary; Django shu katalogdan ZIP yaratadi. Binary bo‘lmasa download `HELPER_NOT_BUILT` (503) qaytaradi.
3. `PUBLIC_SITE_URL`ni saytingizning HTTPS origin’iga o‘rnating, masalan `https://denny-halolike-tenisha.ngrok-free.dev`. Local development uchun `http://localhost:8000` mumkin. `ALLOWED_HOSTS` va `CSRF_TRUSTED_ORIGINS` ham hostname’ga mos bo‘lsin. `PUBLIC_SITE_URL` source code’da hardcode qilinmaydi.
4. `python manage.py cleanup_browser_enrollment_sessions`ni davriy bajaring. Pending sessiyalar 5 daqiqada tugaydi; resolved sessiyalar bir kundan keyin o‘chadi, audit saqlanadi.

Public tarqatishdan oldin Windows binary’larini code-sign, macOS binary’larini sign/notarize qilish kerak. Hozirgi build’lar lokal test uchun unsigned. QR token URL’i reverse-proxy/access loglarda redact qilinishi kerak; URL qisqa muddatli bearer secret hisoblanadi.

## API

Browser mutation so‘rovlari Django CSRF cookie/header talab qiladi. Helper identity endpoint’i CSRF’dan mustasno, lekin 32-byte random bir martalik `scan_token` talab qiladi; token ZIP ichidagi `scan.json`ga qo‘yiladi. Token hech qachon QR ichiga qo‘yilmaydi. Browser architecture hint yuborsa, ZIP faqat shu architecture binary’sini oladi; hint bo‘lmasa ikkala variant fallback sifatida qo‘shiladi. Download ZIP endi binary’ni ichiga olmaydi: `scan.json` va launcher binary endpoint URL’ini oladi, launcher esa binary’ni alohida stream qilib yuklaydi. `scan.json` binary SHA-256 manifestini olib yuradi va helper ishga tushganda o‘z executable checksumini tekshiradi. Binary endpoint query token ishlatgani uchun reverse-proxy/access loglarda `scan_token`ni redact qiling.

| Method/path | Kim chaqiradi | Request | Response |
| --- | --- | --- | --- |
| `GET /device/scan` | Target browser | — | Scan sahifasi va CSRF cookie |
| `POST /api/devices/browser-enrollment/session/` | Shu browser + CSRF | `{}` | 201: `session_id`, `scan_token`, `expires_at`, `display_code`, `qr_url`, `qr_svg`, `identity_ready=false` |
| `POST /api/devices/browser-enrollment/session/<id>/helper/<windows\|macos\|linux>/` | Shu browser + CSRF | `{"scan_token":"...","architecture":"amd64"}` | 200: kichik ZIP (`scan.json`, launcher) |
| `GET /api/devices/browser-enrollment/session/<id>/binary/<windows\|macos\|linux>/<amd64\|arm64>/?scan_token=...` | Download launcher | — | 200: selected binary stream |
| `POST /api/devices/browser-enrollment/session/<id>/identity/` | Standalone helper | `{"scan_token":"...","platform":"linux","device_id":"...","identifiers":{"machine_id":"...","product_uuid":"..."},"hostname":"..."}` | 200: `identity_ready=true`; repeated submit 409, wrong token 403, expired 410 |
| `GET /api/devices/browser-enrollment/session/<id>/` | Shu target browser | — | Holat va `identity_ready`; noto‘g‘ri browser 404 |
| `GET /device-enroll/<one-time-token>` | Admin phone | — | Login yoki approval page; helper ma’lumot yubormagan bo‘lsa 409 |
| `POST /api/devices/browser-enrollment/session/<id>/approve/` yoki `/reject/` | Shu phone sessiyasidagi authorized admin + CSRF | Empty | 200: `approved` yoki `rejected`; replay 409, expired 410 |
| `POST /api/devices/browser-enrollment/session/<id>/cancel/` | Target browser + CSRF | Empty | 200: `cancelled` |

Platform primary ID’lari: Windows `MachineGuid`, macOS `IOPlatformUUID`, Linux `/etc/machine-id`. Windows `ProductId`, macOS serial, Linux DMI product UUID qo‘shimcha metadata sifatida yuboriladi. Primary ID bo‘lmasa helper xato bilan to‘xtaydi. Backend `device_id` primary identifier bilan tengligini tekshiradi. Admin approval sahifasi platform, device ID, hostname, identifierlar, display code va joriy organization’ni ko‘rsatadi. Birinchi authorized admin QR’ni claim qilgan organization sessiyaga bog‘lanadi; boshqa organization qayta claim qila olmaydi.

Approval natijasida `Device` joriy organization’da `browser_approved`, `is_active=false`, `public_key=NULL`, `device_public_key=NULL`, `license=UNKNOWN` bo‘ladi. Admin approval sahifasida location kiritiladi va u `Device.location`ga yoziladi; browser session location berilmasa vaqtinchalik `Unknown` qiymati saqlanadi. Canonical `DeviceEnrollmentSession` modeli eski `BrowserEnrollmentSession` importi uchun compatibility aliasni saqlaydi. Same-organization `device_id` (`pc_id` compatibility ustuni) duplicate’lari reject qilinadi. Eski `/api/agent/activate/` va `/api/devices` Windows contract’lari o‘zgarmaydi; faqat yangi `browser_approved` statusi legacy activation’dan himoyalanadi. UUID/serial/MachineGuid **kriptografik security proof emas**: helperdan kelgan ma’lumotlar admin ko‘rishi uchun claim hisoblanadi. Agent’ni o‘rnatishga yakuniy ruxsat beruvchi, yangi public key va proof-of-possession’ni tekshiruvchi alohida bosqich hali implement qilinmagan. Shuning uchun bu flow company-owned/hardware-backed deb belgilanmaydi.
