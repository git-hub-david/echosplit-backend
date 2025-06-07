import os
import subprocess
import threading
import boto3
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load environment
bucket_name = os.getenv("S3_BUCKET")
region      = os.getenv("AWS_REGION")
s3 = boto3.client("s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=region
)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "separated/mdx_extra_q"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def do_separation(filename: str):
    """Runs in a background thread—downloads, runs Demucs, then uploads stems."""
    try:
        local_path = os.path.join(UPLOAD_FOLDER, filename)
        s3.download_file(bucket_name, filename, local_path)

        subprocess.run(
            ["demucs", local_path, "-n", "mdx_extra_q", "--mp3"],
            check=True
        )

        song_name = os.path.splitext(filename)[0]
        for stem in ["vocals","drums","bass","other"]:
            stem_path = f"{OUTPUT_FOLDER}/{song_name}/{stem}.mp3"
            s3_key    = f"{song_name}/{stem}.mp3"
            s3.upload_file(stem_path, bucket_name, s3_key)

        print(f"✅ Background separation complete for {filename}")

    except Exception as e:
        print(f"❌ Separation error for {filename}: {e}")

@app.route("/", methods=["POST"])
def process_file():
    data     = request.get_json(force=True)
    filename = data.get("filename")
    if not filename:
        return jsonify({"error":"No filename provided"}), 400

    # Immediately spawn a background thread and return 200
    threading.Thread(target=do_separation, args=(filename,), daemon=True).start()
    print(f"🔔 Job started for {filename}")
    return jsonify({"message":"Processing started"}), 200

@app.route("/status")
def status():
    filename = request.args.get("filename","")
    if not filename:
        return jsonify({"error":"No filename"}), 400

    key = f"{filename.rsplit('.',1)[0]}/vocals.mp3"
    try:
        s3.head_object(Bucket=bucket_name, Key=key)
        return jsonify({"done":True})
    except:
        return jsonify({"done":False})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)