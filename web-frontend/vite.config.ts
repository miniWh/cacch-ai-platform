import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
    plugins: [vue()],
    server: {
        // Windows 上默认可能只绑 [::1]，导致 127.0.0.1 无法访问
        host: '0.0.0.0',
        port: 5173,
        strictPort: true,
    },
})
