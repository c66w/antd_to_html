FROM node:20-alpine AS base

WORKDIR /app

COPY package.json package-lock.json* ./

RUN if [ -f package-lock.json ]; then npm ci --only=production; else npm install --only=production; fi

COPY . .

ENV NODE_ENV=production
ENV PORT=6422

EXPOSE 6422

CMD ["npm", "start"]
