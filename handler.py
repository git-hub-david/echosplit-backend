import os
import subprocess
import boto3
from dotenv import load_dotenv

load_dotenv()

# S3 configuration
bucket_name = os.getenv("S3_BUCKET")
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "separated/mdx_extra_q"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def handler(event):
    # Get the filename from event
    filename = event.get("input", {}).get("filename")
    if not filename:
        return {"error": "No filename provided"}

    try:
        # Step 1: Download the file from S3
        local_path = os.path.join(UPLOAD_FOLDER, filename)
        s3.download_file(bucket_name, filename, local_path)

        # Step 2: Run Demucs to separate stems
        subprocess.run([
            "demucs", local_path,
            "-n", "mdx_extra_q",
            "--mp3"
        ], check=True)

        # Step 3: Upload stems back to S3
        base = os.path.splitext(filename)[0]
        for stem in ["vocals", "drums", "bass", "other"]:
            stem_path = f"{OUTPUT_FOLDER}/{base}/{stem}.mp3"
            s3_key = f"{base}/{stem}.mp3"
            s3.upload_file(stem_path, bucket_name, s3_key)

        return {"message": "Processing complete", "filename": filename}

    except subprocess.CalledProcessError as e:
        return {"error": f"Demucs failed: {e}"}
    except Exception as e:
        return {"error": str(e)}