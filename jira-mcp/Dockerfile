FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
RUN npm run build
COPY . .
EXPOSE 5001
CMD ["npm run start"]
