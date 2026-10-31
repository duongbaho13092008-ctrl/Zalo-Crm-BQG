#!/usr/bin/env bash
# =============================================================================
#  BQG · Deploy ZL-CRM 1-lệnh trên VPS
#  Dùng:  bash deploy/bqg-deploy.sh <domain-hoac-IP>
#  Ví dụ: bash deploy/bqg-deploy.sh 201.18.209.218
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."   # về thư mục gốc repo

PUBLIC_HOST="${1:-}"
if [ -z "$PUBLIC_HOST" ]; then
  read -rp "Nhập domain hoặc IP công khai của VPS: " PUBLIC_HOST
fi
[ -z "$PUBLIC_HOST" ] && { echo "❌ Chưa nhập host."; exit 1; }
command -v openssl >/dev/null || { echo "❌ Thiếu openssl"; exit 1; }
command -v docker  >/dev/null || { echo "❌ Thiếu docker"; exit 1; }

if [ -f .env ]; then
  echo "ℹ️  Đã có .env — giữ nguyên, không ghi đè."
else
  JWT=$(openssl rand -hex 32); ENC=$(openssl rand -hex 32)
  DBPW=$(openssl rand -hex 16); MINIO_PW=$(openssl rand -hex 16)
  FB_VERIFY=$(openssl rand -hex 16); FB_ENC=$(openssl rand -hex 32)
  ADMIN_PW=$(openssl rand -base64 12 | tr -d '/+=' | cut -c1-12)
  cat > .env <<EOF
PORT=3000
NODE_ENV=production
APP_URL=http://${PUBLIC_HOST}:3080
JWT_SECRET=${JWT}
ENCRYPTION_KEY=${ENC}
DB_USER=crmuser
DB_PASSWORD=${DBPW}
DB_NAME=zalocrm
DATABASE_URL=postgresql://crmuser:${DBPW}@db:5432/zalocrm
UPLOAD_DIR=/var/lib/zalo-crm/files
REDIS_URL=redis://redis:6379
S3_ENDPOINT=http://minio:9000
S3_PUBLIC_URL=http://${PUBLIC_HOST}:9000
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
FB_OAUTH_REDIRECT_URI=http://${PUBLIC_HOST}:3080/api/v1/integrations/facebook/oauth/callback
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
  echo "✅ Đã tạo .env — Admin SĐT 0989000000 · Mật khẩu: ${ADMIN_PW}  (ĐỔI sau khi đăng nhập)"
fi

echo "🐳 Build & khởi chạy (lần đầu ~5–10 phút)..."
docker compose up -d --build

echo ""
echo "────────────────────────────────────────────"
echo "  ✅ Xong. Mở:  http://${PUBLIC_HOST}:3080"
echo "  Mở tường lửa: ufw allow 3080/tcp && ufw allow 9000/tcp"
echo "────────────────────────────────────────────"
