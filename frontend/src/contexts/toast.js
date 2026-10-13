import { createContext, useContext } from 'react';
export const ToastContext=createContext(null);
export const SystemToastContext=createContext(null);
export const useAdminToast=()=>useContext(ToastContext);
export const useSystemToast=()=>useContext(SystemToastContext);

