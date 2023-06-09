#! /bin/sh

# ASSIGN USER DEFINED FAMILY OF A BINARY

# USAGE:
#  STEP 1:  EDIT THE FILE TO SET THE FOLLOWING VARIABLES

label="Raccoon"         # Family name
source="Demo"        # Source of the info about family name

# STEP 2:
#     set-families.sh $sha1-file-hash

sha1=$1

curl -H "Authorization: Bearer $MAGIC_USER_TOKEN" -X POST "$MAGIC_API/v2/files/$sha1/families?no_links=true" -F "label=$label" -F "source=$source"


