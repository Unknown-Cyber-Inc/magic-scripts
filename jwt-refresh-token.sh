# NOTE: This file must be "sourced" and not run
#   because it sets an environment variable

# LOGIN TO USER AND GET THE ACCESS TOKEN

# USAGE:
#    source user-login.sh
#


JWT_REFRESH_FILE=".jwt-refresh-token.json"

curl -H 'Content-Type: multipart/form-data' \
    -F "refresh=$MAGIC_REFRESH_TOKEN" \
    -X 'POST' "$MAGIC_API/auth/tokens/jwt/refresh/" > $JWT_REFRESH_FILE

export MAGIC_ACCESS_TOKEN=`cat $JWT_REFRESH_FILE | python get-jwt.py access`

