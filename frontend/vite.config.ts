import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    // src/generated est un paquet local ("generated": "file:src/generated").
    // En gardant le chemin node_modules/generated, Vite le traite comme une
    // dépendance et le pré-bundle en ESM : le chat_pb.js CommonJS produit par
    // protoc devient importable dans le navigateur (sinon "exports is not defined").
    preserveSymlinks: true,
  },
})
