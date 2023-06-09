# NOTE: This file must be "sourced" and not run
#   because it sets an environment variable

# LOGIN TO GROUP AND GET THE ACCESS TOKEN

# USAGE:
#    source group-login.sh
#




JWT_GROUP_FILE="jwt-group-token.json"
curl -H "Authorization: Bearer $MAGIC_USER_TOKEN" -H 'Content-Type: multipart/form-data' -F "id=$MAGIC_GROUP" -X 'POST' "$MAGIC_API/auth/groups/login/" > $JWT_GROUP_FILE
export  MAGIC_GROUP_TOKEN=`cat $JWT_GROUP_FILE | python get-jwt.py`
export MAGIC_TOKEN=$MAGIC_GROUP_TOKEN

