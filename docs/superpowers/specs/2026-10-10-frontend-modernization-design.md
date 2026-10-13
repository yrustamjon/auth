# React frontend: zamonaviy dizayn va yakunlash

## Maqsad

Foydalanuvchi Django template frontendidan alohida React frontendiga o'tmoqchi. Mavjud React dizayni yoqmagan; yangi zamonaviy ko'rinishni tanlashni menga topshirdi. Natija: kundalik boshqarishga qulay, mobilga mos, Django API bilan ishlaydigan admin va superadmin paneli.

## Tanlangan dizayn

- Och kulrang sahifa foni (#f5f7fb), oq panellar, to'q ko'k asosiy matn (#152238), ko'k aksent (#2563eb).
- 240px yon menyu, yuqorida sahifa nomi va hisob menyusi; mobil ekranda tugma bilan ochiladigan navigatsiya.
- Aniq tipografiya, 8px asosidagi masofalar, 12–16px yumaloq burchaklar, yengil chegaralar va soyalar.
- Dashboard: haqiqiy API ma'lumotlaridan hisoblangan ko'rsatkichlar, oxirgi kirishlar, qurilma holatlari. API bermagan foiz va xizmat holatlari ko'rsatilmaydi.
- Jadvallar: qidiruv, natija soni, holat belgilari, tushunarli amallar; tor ekranda jadval ichida gorizontal aylantirish.
- Formalar: o'qilishi qulay yorliqlar, maydon xatolari, saqlash holati; o'chirish uchun tasdiqlash oynasi.
- Login: sodda brend bloki va kirish formasi, mobil ekranda bitta ustun.
- Interfeys matnlari o'zbekcha; klaviatura fokusi, tugma nomlari, Escape bilan modal yopish va harakatni kamaytirish sozlamasi.

## Tuzilish va ma'lumotlar oqimi

React + Vite, React Router, Axios va mavjud Lucide ikonkalari saqlanadi. Dizayn CSS o'zgaruvchilari va umumiy komponentlar orqali boshqariladi. Mavjud sahifalardagi to'q rangli inline stillar yangilanadi; faqat ustidan CSS qo'shish bilan cheklanilmaydi.

Admin va superadmin umumiy sahifa karkasi, navigatsiya, jadval, modal, badge va bildirishnoma komponentlaridan foydalanadi. Ularning menyulari va vakolatlari alohida qoladi. Backend ruxsatlari asosiy himoya bo'lib qoladi; frontend sessiya tekshiruvini backenddagi mavjud autentifikatsiya mexanizmiga moslaydi.

API chaqiruvlari mavjud Django route, metod va javob shakllari bilan solishtiriladi. Backendda yo'q amal uchun ishlamaydigan tugma ko'rsatilmaydi. Sessiya cookie va CSRF oqimi tekshiriladi; ruxsatsiz javoblar tegishli login sahifasiga olib boradi, login xatolari esa forma ichida ko'rsatiladi.

## Sahifalar va ko'chirish

Loginlar, dashboardlar, foydalanuvchilar, rollar, qurilmalar, kirish loglari, tashkilotlar va administratorlar yangilanadi. Foydalanuvchi biometrik amallari mavjud API asosida saqlanadi.

QR orqali qurilma ro'yxatdan o'tkazish va tasdiqlash, shuningdek telefon biometrik sahifalari template va API bilan solishtirilib React route'lariga ko'chiriladi. Agent dasturi va uning protokoli o'zgartirilmaydi. Migratsiya davomida mavjud Django sahifalari ishlashda davom etadi; yakuniy ishga tushirish hujjati React va Django'ni alohida ishga tushirishni tushuntiradi.

## Xatolar va tekshirish

Yuklanish, bo'sh natija va API xatosi alohida holatlar bo'ladi. Xato sababli dashboardda muvaffaqiyatli yoki nol qiymat soxta ko'rsatilmaydi. Takroriy yuborish saqlash vaqtida cheklanadi.

Build va lint bajariladi. Autentifikatsiya, API javoblarini talqin qilish va o'zgartirilgan kritik amallar uchun maqsadli tekshiruvlar o'tkaziladi. Brauzerda login, ikkala panel, jadval, modal va mobil navigatsiya 390px hamda desktop kengliklarida ko'riladi. Backend zarur bo'lsa tegishli Django testlari bajariladi. Jonli backend bilan tekshirib bo'lmagan holatlar yakuniy hisobotda aniq aytiladi.

## Ish tartibi

1. Umumiy dizayn komponentlari, karkas va loginlar.
2. Admin va superadmin sahifalarining bir xil dizaynga o'tishi.
3. API mosligi, sessiya va yetishmayotgan template funksiyalarini ko'chirish.
4. Build, lint, funksional va vizual tekshiruvlar, ishga tushirish hujjati.

Foydalanuvchining joriy o'zgarishlari saqlanadi. Bu dizayn ish uchun yozilgan taklif; tasdiqdan so'ng fayllar va tekshiruvlarni ko'rsatadigan amalga oshirish rejasi tayyorlanadi.
