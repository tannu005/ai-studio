FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Set default env values for the build process (Next.js embeds these during build time)
ENV NEXT_PUBLIC_API_URL=http://localhost:5000
ENV NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

RUN npm run build

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["npm", "start"]
