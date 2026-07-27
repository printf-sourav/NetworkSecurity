import subprocess

class S3Sync:
    def sync_folder_to_s3(self, folder, aws_bucket_url):
        try:
            command = f'aws s3 sync "{folder}" "{aws_bucket_url}"'
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print("AWS sync failed:")
            print(e.stderr)
            raise