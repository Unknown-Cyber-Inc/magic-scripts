#! /bin/sh

# ASSIGN USER DEFINED FAMILY OF A BINARY

# USAGE:
#  STEP 1:  EDIT THE FILE TO SET THE FOLLOWING VARIABLES

tag_name="$1"         # Family name

# STEP 2:
#     set-families.sh $tagname $sha1-file-hash

sha1="$2"

curl -H "Authorization: Bearer $MAGIC_ACCESS_TOKEN" -X POST "$MAGIC_API/v2/files/$sha1/tags?no_links=true" -F "name=$tag_name"


