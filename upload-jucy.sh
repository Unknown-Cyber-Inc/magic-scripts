#! /bin/bash

# TO UPLOAD A FILE

# CUSTOMIZING UPLOAD PARAMETERS


# PARAMETERS: USER DEFINE DATA
TAGS="AL-05072025-Jucy2"    # A tag to assocated with the file
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

# file:                # (binary itself)
# priority: 1 (can be 1, 2, or 3)
# machine: win10 (can be win7, win10, or win11)
# route: internet
# tlp: white
# timeout: 120

query_params=""
# query_params="$query_params&filename=$1"

curl -H "Authorization: Bearer $MAGIC_ACCESS_TOKEN" \
    -F "file=@$1" \
    -F "tags_tasks=$TAGS" \
    -F "password=$PASSWORD" \
    -F "priority=1" \
    -F "tlp=white" \
    -F "timeout=120 " \
    -F "route=internet" \
    -F "machine=win10" \
    -X POST "$JUCY_API/apiv2/tasks/create/file/"
