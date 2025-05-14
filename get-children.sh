#! /bin/sh

# GET HASHES OF CHILDREN OF A FILE
# USED TO GET THE HASHES OF FILES INSIDE A ZIP FILE


# USAGE
#  get-children.sh $sha1-file-hash

#  OUTPUT: To standard output

sha1=$1
curl -H "Authorization: Bearer $MAGIC_ACCESS_TOKEN" -X GET "$MAGIC_API/v2/files/$sha1/children?no_links=true"

