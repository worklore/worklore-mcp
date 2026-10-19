# Cache headers in the deploy

Updated `scripts/deploy.sh` to upload HTML, JavaScript, and CSS with `Cache-Control: public, max-age=300`, and files in `assets/` with `Cache-Control: public, max-age=86400`. The deploy still removes deleted files and invalidates CloudFront after the uploads.

The script reuploads the local files after `s3 sync`, so existing objects receive the new headers even when their contents have not changed. HTML, JavaScript, and CSS uploads set their content types explicitly; asset uploads use the AWS CLI's MIME type detection from local files.

Verified with `bash -n`, `git diff --check`, and a local mock of the AWS CLI that checked the upload options and invalidation order. No deployment or external AWS call was made.
