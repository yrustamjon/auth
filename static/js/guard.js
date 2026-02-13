// /**
//  * Page protection guard (Django compatible)
//  */

// // Protected Django paths
// const PROTECTED_PATHS = [
//     '/dashboard/',
//     '/users/',
//     '/roles/',
//     '/devices/',
//     '/logs/'
// ];

// // const LOGIN_PATH = '/login/';

// async function checkSession() {
//     const path = window.location.pathname;

//     // 🔥 Login sahifani tekshirmaymiz
//     if (path === LOGIN_PATH) {
//         return;
//     }

//     // Faqat protected sahifalar
//     if (PROTECTED_PATHS.includes(path)) {
//         const isValid = await validateSession();

//         if (!isValid) {
//             window.location.href = `${LOGIN_PATH}?next=${path}`;
//             return;
//         }
//     }
// }



