import os
import subprocess
import boto3
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()
print("🚀 Handler starting up...")

app = Flask(__name__)

# Load environment variables
bucket_name = os.getenv("S3_BUCKET")
region = os.getenv("AWS_REGION")
aws_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")

# Log env check (safe to print region + bucket only)
print(f"🌍 AWS Region: {region}")
print(f"🪣 S3 Bucket: {bucket_name}")

# Setup S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_key,
    aws_secret_access_key=aws_secret,
    region_name=region
)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "separated/mdx_extra_q"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["POST"])
def process_file():
    print("🔥 Received POST request to /")

    try:
        data = request.get_json()
        print(f"📦 Request JSON: {data}")
        filename = data.get("filename")
        if not filename:
            return jsonify({"error": "No filename provided"}), 400

        # Download file from S3
        local_path = os.path.join(UPLOAD_FOLDER, filename)
        print(f"⬇️ Downloading {filename} from S3 to {local_path}")
        s3.download_file(bucket_name, filename, local_path)

        # Run Demucs
        print("🎶 Running Demucs...")
        subprocess.run(["demucs", local_path, "-n", "mdx_extra_q", "--mp3"], check=True)

        # Upload stems
        song_name = os.path.splitext(filename)[0]
        for stem in ["vocals", "drums", "bass", "other"]:
            stem_path = f"{OUTPUT_FOLDER}/{song_name}/{stem}.mp3"
            s3_key = f"{song_name}/{stem}.mp3"
            print(f"⬆️ Uploading {stem} to S3 at {s3_key}")
            s3.upload_file(stem_path, bucket_name, s3_key)

        print("✅ All stems uploaded.")
        return jsonify({"message": "Processing complete", "song": song_name})

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)