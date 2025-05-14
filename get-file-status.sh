#! /bin/sh

# TO GET INFORMATION ABOUT A FILE

# USAGE
#   get-file-status.sh $sha1-file-hash

# NOTE: This is a specialized version of get-file-info.sh

sha1=$1

curl -H "Authorization: Bearer $MAGIC_ACCESS_TOKEN" -X GET "$MAGIC_API/v2/files/$sha1?read_mask=_default,pipeline&no_links=true"
