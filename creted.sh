# # 1) Login to obtain origin cert (opens a URL to approve)
# cloudflared tunnel login
# # After approval, cert stored at ~/.cloudflared/cert.pem

# # 2) Create named tunnel
# cloudflared tunnel create "rf_checker"

# # 3) Get Tunnel ID and credentials JSON path
# NEW_ID=$(cloudflared tunnel list | awk '$1=="rf_checker"{print $2}')
# # echo "Tunnel ID: $NEW_ID"
# CRED_JSON="$HOME/.cloudflared/c813cbe6-0797-41eb-a001-69015f2caab3.json"
# # test -f "$CRED_JSON" || echo "Credentials JSON not found; check login/create steps"
# # cloudflared tunnel route dns "rf_checker" ai_app.workerinua.fun
# # cloudflared tunnel route dns "rf_checker" ai_api.workerinua.fun
# # Copy credentials into repo for Docker mount
# mkdir -p /home/mikola/projects/rf_checker/cloudflared
# cp "$CRED_JSON" "/home/mikola/projects/rf_checker/cloudflared/$NEW_ID.json"

# # Write cloudflared/config.yml
# cat >/home/mikola/projects/rf_checker/cloudflared/config.yml <<EOF
# tunnel: $NEW_ID
# credentials-file: /etc/cloudflared/$NEW_ID.json
# ingress:
#   - hostname: ai_app.workerinua.fun
#     service: http://rf_checker_frontend_1:3000
#   - hostname: ai_api.workerinua.fun
#     service: http://rf_checker_backend_1:8000
#   - service: http_status:404
# EOF

# # Export env for compose (used in credentials mount)
# export CLOUDFLARE_TUNNEL_ID="$NEW_ID"

cd /home/mikola/projects/rf_checker
docker-compose -f docker-compose.prod.yml down --remove-orphans
docker-compose -f docker-compose.prod.yml up -d