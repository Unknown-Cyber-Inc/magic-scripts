# NOTE: This file must be "sourced" and not run
#   because it sets an environment variable

# LOGIN TO USER AND GET THE ACCESS TOKEN

# USAGE:
#    source user-login.sh
#


JWT_USER_FILE="jwt-user-token.json"
curl -X POST $MAGIC_API/auth/tokens/jwt/issue -d username=$MAGIC_USER -d password=$MAGIC_PASS > $JWT_USER_FILE

export MAGIC_USER_TOKEN=`cat $JWT_USER_FILE | python get-jwt.py`


# To interact with the user account, and not the group account, uncomment the line below.

export MAGIC_TOKEN=$MAGIC_USER_TOKEN
