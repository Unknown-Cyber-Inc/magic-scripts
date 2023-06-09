#! /bin/sh

# TO GET INFORMATION ABOUT A FILE

# USAGE
#   get-file-info.sh $sha1-file-hash


sha1=$1


# CUSTOMIZABLE PARAMETERS
# COMMENT/UNCOMMENT FOLLOWING DEPENDING ON USE

f=""
    f="read_mask=_default"  # see documentation
#    f="$f,pipeline"         # get processing status
#    f="$f,children"         # get children file hashes; such as those in a zip file
#    f="$f,similarities"     # get similar files, threshold >0.7
    f="$f,categories"       # get categories: ground truth, inferred, and user assigned
    f="$f,families"         # get families: ground truth, inferred, and user assigned
#    f="$f,tags"             # get tags/project
#    f="$f,notes"            # get note objects
    f="$f,match_count"
    f="$f,sha256"
    f="$f,family"
    f="$f,category"
    f="$f,detection_count"
    f="$f,scanner_count"
    f="$f,evasiveness"
    f="$f,scan_date"
    f="$f,reputation"
    f="$f,threat"
    f="$f,object_class"
    f="$f,filetype"
#    f="$f,matches"
    f="$f,create_time"
    f="$f,filenames"

read_mask=$f

x=""
x="expand_mask=notes"  # traverse notes object and get the notes



explain=false               # true: explain the query parameters
no_links=true               # true: do not give links to related objects

expand_mask=$x

curl -H "Authorization: Bearer $MAGIC_TOKEN" -X GET "$MAGIC_API/v2/files/$sha1?$read_mask&expand_mask=notes&explain=$explain&no_links=$no_links"
