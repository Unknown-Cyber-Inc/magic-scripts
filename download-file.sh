#! /bin/sh

#  SCRIPT TO DOWNLOAD MALWARE FILE
#  THIS IS A PRIVILEGED CAPABILITY; IT MUST BE EXPLICITLY ENABLED FOR A USER
#  BY DEFAULT IT IS NOT TURNED ON

#  THE FILE DOWNLOADED IS ZIPPED AND PASSWORD PROTECTED.
#  ASK ADMIN FOR THE PASSWORD

# ENVIRONMENT VARIABLES REQUIRES
#     MAGIC_API
#     MAGIC_TOKEN

# USAGE:
#     download-file.sh sha1-file-hash
# OUTPUT
#     filenamed: $sha1-file-hash.zip
#


sha1=$1
filename="${sha1}.zip"
curl -H "Authorization: Bearer $MAGIC_ACCESS_TOKEN" -X GET "$MAGIC_API/v2/files/$sha1/download/?zipped=true&no_links=true" -o $filename
