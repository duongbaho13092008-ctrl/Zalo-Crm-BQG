import 'vuetify/styles';
import '@mdi/font/css/materialdesignicons.css';
import { createVuetify } from 'vuetify';

/**
 * Vuetify theme — palette từ design tokens Smax (mockup chat-smax-v3.html).
 * `smax-light` (default) khớp mockup. `legacy-dark` giữ lại để fallback nếu
 * có view nào còn phụ thuộc bảng màu cũ; sẽ rút khi mọi view đã migrate.
 *
 * Perf 2026-06-19: KHÔNG đăng ký `* as components/directives` toàn cục nữa —
 * vite-plugin-vuetify({ autoImport: true }) (vite.config.ts) chỉ bundle component
 * thực sự dùng trong template. Import wildcard trước đây kéo TOÀN BỘ Vuetify vào
 * entry chunk, vô hiệu hoá tree-shaking → bundle phình + chậm first paint.
 */
export const vuetify = createVuetify({
  theme: {
    defaultTheme: localStorage.getItem('theme') || 'smax-light',
    themes: {
      // Nhận diện Bình Quân Group (BQG): navy chủ đạo, xanh dương nhấn, vàng lúa.
      'smax-light': {
        dark: false,
        colors: {
          background: '#f5f7fa',
          surface: '#ffffff',
          'surface-variant': '#fafbfc',
          primary: '#1E6CA8',
          secondary: '#0F2E4D',
          accent: '#C9A227',
          error: '#D14332',
          warning: '#D9961A',
          success: '#4E9A51',
          info: '#2F6FA3',
          'on-background': '#16202b',
          'on-surface': '#16202b',
          'on-primary': '#ffffff',
          'on-secondary': '#ffffff',
        },
      },
      'legacy-dark': {
        dark: true,
        colors: {
          background: '#0A192F',
          surface: '#112240',
          'surface-variant': '#1D2D50',
          primary: '#00F2FF',
          secondary: '#E6F1FF',
          accent: '#00F2FF',
          error: '#FF5252',
          warning: '#FFB74D',
          success: '#4CAF50',
          info: '#00F2FF',
          'on-background': '#E6F1FF',
          'on-surface': '#E6F1FF',
          'on-primary': '#0A192F',
        },
      },
    },
  },
  defaults: {
    VBtn: { variant: 'flat' },
    VTextField: { variant: 'outlined', density: 'compact' },
    VSelect: { variant: 'outlined', density: 'compact' },
    VAutocomplete: { variant: 'outlined', density: 'compact' },
    VTextarea: { variant: 'outlined', density: 'compact' },
    VCard: { rounded: 'md', variant: 'flat' },
    VChip: { rounded: 'lg', size: 'small' },
    VDialog: { maxWidth: 600 },
  },
});
