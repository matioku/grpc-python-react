# Build depuis la racine du repo (docker compose).
# Installe protoc + plugins DANS l'image — pas besoin sur l'hôte.

FROM node:22-bookworm AS build
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      protobuf-compiler curl ca-certificates unzip \
 && ARCH=$(dpkg --print-architecture) \
 && case "$ARCH" in amd64) GW=x86_64; JS=x86_64;; arm64) GW=aarch64; JS=aarch_64;; *) GW=x86_64; JS=x86_64;; esac \
 && curl -fsSL -o /usr/local/bin/protoc-gen-grpc-web \
      "https://github.com/grpc/grpc-web/releases/download/1.5.0/protoc-gen-grpc-web-1.5.0-linux-${GW}" \
 && chmod +x /usr/local/bin/protoc-gen-grpc-web \
 && curl -fsSL -o /tmp/pbjs.tar.gz \
      "https://github.com/protocolbuffers/protobuf-javascript/releases/download/v3.21.4/protobuf-javascript-3.21.4-linux-${JS}.tar.gz" \
 && tar -xzf /tmp/pbjs.tar.gz -C /tmp \
 && cp /tmp/bin/protoc-gen-js /usr/local/bin/ \
 && chmod +x /usr/local/bin/protoc-gen-js \
 && rm -rf /var/lib/apt/lists/* /tmp/pbjs.tar.gz /tmp/bin /tmp/include /tmp/README* /tmp/LICENSE*

COPY frontend/package.json frontend/package-lock.json ./
# Le paquet local "generated" doit exister avant l'install (file:src/generated)
COPY frontend/src/generated/package.json ./src/generated/package.json
RUN npm install --omit=dev=false

COPY frontend/ ./
COPY protos/ /protos/

# Génère les stubs grpc-web puis build Vite
RUN mkdir -p src/generated \
 && protoc -I /protos \
      --js_out=import_style=commonjs,binary:src/generated \
      --grpc-web_out=import_style=typescript,mode=grpcwebtext:src/generated \
      /protos/chat.proto \
 && test -f src/generated/ChatServiceClientPb.ts \
 && grep -q login src/generated/ChatServiceClientPb.ts \
 && npm install --no-save ./src/generated

ARG VITE_GRPC_URL=/api
ENV VITE_GRPC_URL=$VITE_GRPC_URL
RUN npx tsc -b && npx vite build

FROM nginx:1.27-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
RUN mkdir -p /etc/nginx/certs
EXPOSE 443
CMD ["nginx", "-g", "daemon off;"]
