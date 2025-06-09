import os
import subprocess
import boto3
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# S3 config
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

@app.route("/", methods=["POST"])
def process_file():
    data = request.get_json() or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    try:
        # download
        local_path = os.path.join(UPLOAD_FOLDER, filename)
        s3.download_file(bucket_name, filename, local_path)

        # demucs
        subprocess.run(["demucs", local_path, "-n", "mdx_extra_q", "--mp3"],
                       check=True)

        # upload stems
        base = os.path.splitext(filename)[0]
        for stem in ["vocals", "drums", "bass", "other"]:
            stem_path = f"{OUTPUT_FOLDER}/{base}/{stem}.mp3"
            s3_key    = f"{base}/{stem}.mp3"
            s3.upload_file(stem_path, bucket_name, s3_key)

        return jsonify({"message": "Processing complete"}), 200

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Demucs failed: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status", methods=["GET"])
def check_status_and_urls():
    filename = request.args.get("filename", "")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    base = filename.rsplit(".",1)[0]
    key  = f"{base}/vocals.mp3"
    try:
        s3.head_object(Bucket=bucket_name, Key=key)
    except s3.exceptions.NoSuchKey:
        return jsonify({"done": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # presign
    urls = {}
    for stem in ["vocals","drums","bass","other"]:
        urls[stem] = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket_name,
                    "Key": f"{base}/{stem}.mp3"},
            ExpiresIn=3600
        )
    return jsonify({"done": True, "urls": urls})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)