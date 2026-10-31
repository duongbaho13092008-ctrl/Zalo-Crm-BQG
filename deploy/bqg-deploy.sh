#!/usr/bin/env bash
# =============================================================================
#  BQG · Deploy ZL-CRM trên VPS
#  HTTP:   bash deploy/bqg-deploy.sh <domain-hoac-IP>
#  HTTPS:  bash deploy/bqg-deploy.sh <app-domain> <files-domain>
#  VD:     bash deploy/bqg-deploy.sh crmzalo.binhquangroup.tech files.crmzalo.binhquangroup.tech
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

APP_DOMAIN="${1:-}"
FILES_DOMAIN="${2:-}"
[ -z "$APP_DOMAIN" ] && read -rp "Nhập app domain (hoặc IP): " APP_DOMAIN
[ -z "$APP_DOMAIN" ] && { echo "❌ Chưa nhập domain."; exit 1; }
command -v openssl >/dev/null || { echo "❌ Thiếu openssl"; exit 1; }
command -v docker  >/dev/null || { echo "❌ Thiếu docker"; exit 1; }

if [ -n "$FILES_DOMAIN" ]; then
  APP_URL="https://${APP_DOMAIN}"
  S3_PUBLIC="https://${FILES_DOMAIN}"
  FB_CB="https://${APP_DOMAIN}/api/v1/integrations/facebook/oauth/callback"
  MODE="HTTPS"
else
  APP_URL="http://${APP_DOMAIN}:3080"
  S3_PUBLIC="http://${APP_DOMAIN}:9000"
  FB_CB="http://${APP_DOMAIN}:3080/api/v1/integrations/facebook/oauth/callback"
  MODE="HTTP"
fi

if [ -f .env ]; then
  echo "ℹ️  Đã có .env — giữ nguyên. (Xoá .env rồi chạy lại nếu muốn tạo mới)"
else
  JWT=$(openssl rand -hex 32); ENC=$(openssl rand -hex 32)
  DBPW=$(openssl rand -hex 16); MINIO_PW=$(openssl rand -hex 16)
  FB_VERIFY=$(openssl rand -hex 16); FB_ENC=$(openssl rand -hex 32)
  ADMIN_PW=$(openssl rand -base64 12 | tr -d '/+=' | cut -c1-12)
  cat > .env <<EOF
PORT=3000
NODE_ENV=production
APP_URL=${APP_URL}
JWT_SECRET=${JWT}
ENCRYPTION_KEY=${ENC}
DB_USER=crmuser
DB_PASSWORD=${DBPW}
DB_NAME=zalocrm
DATABASE_URL=postgresql://crmuser:${DBPW}@db:5432/zalocrm
UPLOAD_DIR=/var/lib/zalo-crm/files
REDIS_URL=redis://redis:6379
S3_ENDPOINT=http://minio:9000
S3_PUBLIC_URL=${S3_PUBLIC}
S3_BUCKET=zalocrm-attachments
S3_REGION=us-east-1
S3_ACCESS_KEY=bqgminio
S3_SECRET_KEY=${MINIO_PW}
MINIO_ROOT_USER=bqgminio
MINIO_ROOT_PASSWORD=${MINIO_PW}
AI_DEFAULT_PROVIDER=anthropic
AI_DEFAULT_MODEL=claude-sonnet-4.6
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_AUTH_TOKEN=
FB_GRAPH_API_VERSION=v21.0
FB_APP_ID=
FB_APP_SECRET=
FB_WEBHOOK_VERIFY_TOKEN=${FB_VERIFY}
FB_TOKEN_ENC_KEY=${FB_ENC}
FB_OAUTH_REDIRECT_URI=${FB_CB}
ZALO_MSG_DAILY_LIMIT=200
ZALO_MSG_BURST=5
BROADCAST_GROUP_DELAY_MS=15000
BOOTSTRAP_ADMIN_PHONE=0989000000
BOOTSTRAP_ADMIN_PASSWORD=${ADMIN_PW}
BOOTSTRAP_ADMIN_NAME=Phạm Văn Mạnh
BOOTSTRAP_ADMIN_EMAIL=
BOOTSTRAP_ORG_NAME=Bình Quân Group
BOOTSTRAP_ADMIN_RESET_PASSWORD=false
EOF
  chmod 600 .env
  echo "✅ .env đã tạo — Admin: SĐT 0989000000 · Mật khẩu: ${ADMIN_PW}  (ĐỔI sau khi đăng nhập)"
fi

echo "🐳 Build & khởi chạy ứng dụng (lần đầu ~5–10 phút)..."
docker compose up -d --build

if [ "$MODE" = "HTTPS" ]; then
  echo "🔐 Dựng Caddy (SSL tự động Let's Encrypt)..."
  cat > Caddyfile <<EOF
${APP_DOMAIN} {
    reverse_proxy localhost:3080
}
${FILES_DOMAIN} {
    reverse_proxy localhost:9000
}
EOF
  docker rm -f bqg-caddy >/dev/null 2>&1 || true
  docker run -d --name bqg-caddy --restart unless-stopped --network host \
    -v "$PWD/Caddyfile:/etc/caddy/Caddyfile" \
    -v bqg_caddy_data:/data -v bqg_caddy_config:/config caddy:2
  echo ""
  echo "────────────────────────────────────────────"
  echo "  ✅ Xong (HTTPS). Mở:  ${APP_URL}"
  echo "  (SSL cấp lần đầu ~30–60s. Cần mở cổng 80 & 443)"
  echo "  ufw allow 80/tcp && ufw allow 443/tcp"
  echo "────────────────────────────────────────────"
else
  echo ""
  echo "────────────────────────────────────────────"
  echo "  ✅ Xong (HTTP). Mở:  ${APP_URL}"
  echo "  ufw allow 3080/tcp && ufw allow 9000/tcp"
  echo "────────────────────────────────────────────"
fi
