# crunchpics

Share screenshots (or any files) with friends. No cookie banners, no login walls, no "who has access?" dialogs, no bloating your Signal chat history with full-res attachments. Just a direct image link you can paste into Signal (and retract if you messed up).

A tiny CLI that uploads files to a Google Cloud Storage bucket, makes them publicly accessible, and lets you flip them back to private whenever you want.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```
GCS_BUCKET_NAME=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

`GOOGLE_APPLICATION_CREDENTIALS` can be left blank to use [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials).

## Usage

```bash
# Upload a file (makes it publicly accessible)
python upload_to_gcs.py upload <file_path>

# List latest files (default 10, shows public/private status)
python upload_to_gcs.py list [count]

# Delete a file (interactive picker if no name given)
python upload_to_gcs.py delete [object_name]

# Revoke public access on a file (interactive picker if no name given)
python upload_to_gcs.py private [object_name]
```

### Shell alias

Add to `~/.bashrc` for quick access:

```bash
alias u2g='/path/to/crunchpics/venv/bin/python /path/to/crunchpics/upload_to_gcs.py'
```

Then: `u2g upload photo.jpg`, `u2g list`, etc.

## Requirements

- Python 3.10+
- GCS bucket with Fine-grained ACL mode (not Uniform bucket-level access)
- Service account with the **Storage Object Admin** role (or equivalent)
