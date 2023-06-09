
These scripts accompany the Phase 1 training.



SETTING UP YOUR ENVIRONMENT

    Pre-requisite: Requires "python" in $PATH

    Step 1: Modify "set-credentials.sh"
    Step 2: Initialize environment variables with the credentials

	    % source set-credentials.sh

	   Confirm that the environment variables are set

	   % printenv | grep MAGIC

	 Should have the following variable set:
	    MAGIC_USER
	    MAGIC_PASS

	    MAGIC_GROUP

	    MAGIC_API

    Step 3: Login to your user account

	   % source user-login.sh


	  Confirm that the following environment variables are set

	  % printenv | grep MAGIC_USER_TOKEN


    Step 4: (optional) Login to the your preferred group

	  % source group-login.sh

	  Confirm that the following environment variables are set

	  % printenv | grep MAGIC_GROUP_TOKEN
	  % printenv | grep MAGIC_TOKEN


PERFORMING OPERATIONS


   TASK: UPLOAD FILE

       STEP 1: Customize the upload parameters
            Edit "upload-file.sh"

       STEP 2: Upload the file
       
           % upload-file.sh path-to-file  | python -m json.tool > upload-response.json


      STEP 3: GET SHA1 OF THE FILE (NEEDED FOR ALL LATER OPERATIONS)
	  Option 1: use "sha1sum" on your system to compute the sha1 of the uploaded file.
	  Option 2: Get the sha1 from the upload-response.json

          % export filehash=<copy/paste>

   TASK: QUERY FILE STATUS

          % get-file-status.sh $filehash | python -m json.tool

   TASK: GET FILE HASH OF CHILDREN (OF ZIP FILE, FOR EXAMPLE)

         % get-children.sh $filehash | python -m json.tool

        Copy/paste hashes from the screen output

         % export childsha1=<copy/paste>

   TASK: GET FILE INFORMATION

      STEP 1: Customize the information you'd like
         Edit get-file-info.sh


      STEP 2: Get file info

         % get-file-info.sh $filehash

  TASK: GET FILE GENOMICS
        % get-file-genomics.sh > $filehash


  TASK: SET YOUR OWN FAMILY FOR A FILE (PRIVILEGED OPERATION)

      STEP 1: Choose the family name
          Edit set-families.sh


     STEP 2: Set the info
         % set-families $sha1-file-hash

   TASK: DOWNLOAD FILE: ZIP, BINARY, OR ANY OTHER (PRIVILEGED OPERATION)


       % download-file.sh $sha1-file-hash
      


