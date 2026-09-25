# ---- Étape 1 : génération du code ----
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY protos/ ./protos/
RUN mkdir -p generated \
 && python -m grpc_tools.protoc -Iprotos \
      --python_out=generated --pyi_out=generated --grpc_python_out=generated \
      chat.proto \
 && sed -i 's/^import chat_pb2/from generated import chat_pb2/' generated/chat_pb2_grpc.py \
 && python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. \
      protos/user.proto \
 && touch protos/__init__.py generated/__init__.py

# ---- Étape 2 : image finale ----
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && ARCH=$(uname -m) \
 && case "$ARCH" in x86_64) P=amd64;; aarch64) P=arm64;; *) P=amd64;; esac \
 && curl -fsSL -o /usr/local/bin/grpc_health_probe \
      "https://github.com/grpc-ecosystem/grpc-health-probe/releases/download/v0.4.37/grpc_health_probe-linux-${P}" \
 && chmod +x /usr/local/bin/grpc_health_probe \
 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app/generated ./generated
COPY --from=builder /app/protos ./protos
COPY auth/ ./auth/
COPY services/ ./services/
COPY interceptors/ ./interceptors/
COPY main.py .
ENV GRPC_TLS=1
ENV GRPC_PORT=50052
ENV CERTS_DIR=/app/certs
ENV JWT_SECRET=change-me-in-prod-please-use-32b+
EXPOSE 50052
# Healthcheck mTLS : sonde avec le certificat client (même CA)
HEALTHCHECK --interval=5s --timeout=2s --retries=3 \
  CMD grpc_health_probe -addr=localhost:50052 \
    -tls -tls-ca-cert=/app/certs/ca.crt \
    -tls-client-cert=/app/certs/client.crt \
    -tls-client-key=/app/certs/client.key || exit 1
CMD ["python", "main.py"]
