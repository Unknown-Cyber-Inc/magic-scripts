#! /bin/sh

# TO GET INFORMATION ABOUT A FILE

# USAGE
#   get-file-genomics.sh $sha1-file-hash


sha1=$1


# CUSTOMIZABLE PARAMETERS
# COMMENT/UNCOMMENT FOLLOWING DEPENDING ON USE

f=""
    f="read_mask=_default"  # see documentation

read_mask=$f

x=""
#x="expand_mask=notes"  # traverse notes object and get the notes



no_links=true               # true: do not give links to related objects

expand_mask=$x

curl -H "Authorization: Bearer $MAGIC_ACCESS_TOKEN" -X GET "$MAGIC_API/v2/files/$sha1/genomics/?$read_mask&expand_mask=$x&no_links=$no_links"
