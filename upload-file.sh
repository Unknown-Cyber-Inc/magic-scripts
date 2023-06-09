#! /bin/sh

# TO UPLOAD A FILE

# CUSTOMIZING UPLOAD PARAMETERS


# PARAMETERS: USER DEFINE DATA
TAGS="AL 2-17"    # A tag to assocated with the file
NOTES="This is a file used for demo about $TAGS"
PASSWORD=         # For password protected files; if not default

# PARAMETER: DISABLE UNPACKING OF BY MAGIC

skip_unpack=false       # Make it true to disable unpacking


# PARAMETERS TO DETERMINE HOW TO TREAT AN ARCHIVE

# An archive (with nested archives) forms a tree structure, with files
# at the leaves.
# The following parameters control whether files are extracted to be
# 'top level' as though they have been uploaded by themselves.


extract=true           # make it false to not extract a file to the top level
recursive=true         # make it false to extract only one level deep files
                       # else the extraction is done recursively
retain_wrapper=true    # make it false if you do not want to keep the wrapper
                       # in your collection (it is always kept in the system)


query_params="skip_unpack=$skip_unpack&extract=$extract&recursive=$recursive&retain_wrapper=$retain_wrapper&no_links=true"

curl -H "Authorization: Bearer $MAGIC_TOKEN" -F "filedata=@$1" -F "tags=$TAGS" -F "notes=$NOTES" -F "password=$PASSWORD" -X POST "$MAGIC_API/v2/files?$query_params"
