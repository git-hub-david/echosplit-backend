import os
import subprocess
import boto3
from dotenv import load_dotenv

load_dotenv()

# Pull bucket from event (if present) or fall back to env
DEFAULT_BUCKET = os.getenv("S3_BUCKET")

# S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

# Where Demucs will write its outputs
OUTPUT_BASE = "separated"
MODEL = "mdx_extra_q"

# Ensure our download/upload folders exist
os.makedirs("uploads", exist_ok=True)
os.makedirs(OUTPUT_BASE, exist_ok=True)

def handler(event):
    """
    event should be:
      { "filename": "<key in S3>",  "bucket": "<optional bucket override>" }
    """
    filename = event.get("filename")
    if not filename:
        return {"error": "No filename provided"}, 400

    bucket = event.get("bucket", DEFAULT_BUCKET)
    base, _ext = os.path.splitext(filename)
    local_in = os.path.join("uploads", filename)

    try:
        # 1) fetch from S3
        s3.download_file(bucket, filename, local_in)

        # 2) run Demucs
        #    writes into separated/<MODEL>/<base>/*.mp3
        subprocess.run([
            "demucs",
            local_in,
            "-n", MODEL,
            "--mp3",
            "--out", OUTPUT_BASE
        ], check=True)

        # 3) push each stem back
        out_dir = os.path.join(OUTPUT_BASE, MODEL, base)
        stems = ["vocals", "drums", "bass", "other"]
        for stem in stems:
            src = os.path.join(out_dir, f"{stem}.mp3")
            dest_key = f"{base}/{stem}.mp3"
            s3.upload_file(src, bucket, dest_key)

        return {"message": "Processing complete", "filename": filename}

    except subprocess.CalledProcessError as e:
        return {"error": f"Demucs failed: {e}"}, 500
    except Exception as e:
        return {"error": str(e)}, 500