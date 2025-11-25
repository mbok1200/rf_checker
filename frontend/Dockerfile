# Dockerfile for frontend (Next.js)
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install --legacy-peer-deps
ENV PATH="/app/node_modules/.bin:${PATH}"
RUN ls -la /app/node_modules/.bin
RUN which next || echo "next not found"
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
