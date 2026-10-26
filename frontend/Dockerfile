# =====================================================================
# frontend/Dockerfile — React + Vite (Node 20)
# =====================================================================
FROM node:20-alpine AS base

# --- Métadonnées ---
LABEL maintainer="DHR" \
      description="Front-end React/Vite pour la DHR"

# --- Répertoire de travail ---
WORKDIR /app

# --- Installation des dépendances ---
# On copie d'abord package.json pour profiter du cache Docker
COPY package.json ./
# npm install (pas npm ci) car pas de package-lock.json initialement
RUN npm install

# --- Copie du code ---
COPY . .

# --- Port exposé (Vite dev server) ---
EXPOSE 5173

# --- Point d'entrée ---
# --host 0.0.0.0 : accessible depuis l'extérieur du container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]