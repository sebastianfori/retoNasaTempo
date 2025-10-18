# Build
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm i
COPY . .
RUN npm run build

# Serve (vite preview)
FROM node:20-alpine
WORKDIR /app
COPY --from=build /app /app
ENV PORT=5173
EXPOSE 5173
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
