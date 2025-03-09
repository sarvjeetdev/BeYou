# nginx/Dockerfile
FROM nginx:alpine

# Create an SSL directory inside the container
RUN mkdir -p /etc/nginx/ssl

# Copy your Nginx config file
COPY default.conf /etc/nginx/conf.d/default.conf

# Copy your SSL certificate and key (relative to the nginx/ folder)
COPY ssl/beyou.crt /etc/nginx/ssl/beyou.crt
COPY ssl/beyou.key /etc/nginx/ssl/beyou.key

# Expose ports (for clarity; Compose handles published ports)
EXPOSE 80
EXPOSE 443
