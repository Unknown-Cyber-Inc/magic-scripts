#! /bin/sh

# TO GET INFORMATION ABOUT A FILE

# USAGE
#   get-ai-analysis.sh $sha1-file-hash $llm


sha1=$1
llm="${2:-claude}"

page_size=100
# CUSTOMIZABLE PARAMETERS
# COMMENT/UNCOMMENT FOLLOWING DEPENDING ON USE

f=""
    f="read_mask=_default"  # see documentation
read_mask=$f
q=""
if [[ -n "$MAGIC_EXPLAIN" ]]; then
    q="$q&explain=true"
fi


q="$q&llm=$llm"

x=""
#x="expand_mask=notes"  # traverse notes object and get the notes



no_links=true               # true: do not give links to related objects

expand_mask=$x

echo "xxxxxxxxxxxxxxxxxx"


echo curl -H \"Authorization: Bearer \$MAGIC_ACCESS_TOKEN\" -X GET \"\$MAGIC_API/v2/ai/$sha1/?$read_mask\&expand_mask=$x\&no_links=$no_links\&llm=$llm\"
#curl -H "Authorization: Bearer $MAGIC_ACCESS_TOKEN" -X GET "$MAGIC_API/v2/ai/$sha1/?$read_mask&expand_mask=$x&no_links=$no_links$q"
