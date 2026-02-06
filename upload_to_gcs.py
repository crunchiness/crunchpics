#!/usr/bin/env python3
"""Manage files in a Google Cloud Storage bucket."""

import sys
import os
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME')
CREDENTIALS_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')


def get_client() -> storage.Client:
    if CREDENTIALS_PATH:
        return storage.Client.from_service_account_json(CREDENTIALS_PATH)
    return storage.Client()


def require_bucket_name():
    if not BUCKET_NAME:
        print('Error: GCS_BUCKET_NAME is not set in .env', file=sys.stderr)
        sys.exit(1)


def upload(file_path: str) -> str:
    """Upload a file to GCS and set it to publicly readable."""
    require_bucket_name()

    if not os.path.isfile(file_path):
        print(f'Error: "{file_path}" is not a valid file.', file=sys.stderr)
        sys.exit(1)

    client = get_client()
    object_name = os.path.basename(file_path)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(object_name)

    print(f'Uploading "{file_path}" to gs://{BUCKET_NAME}/{object_name} ...')
    blob.upload_from_filename(file_path)

    blob.make_public()

    print(f'Upload complete. Public URL:\n{blob.public_url}')
    return blob.public_url


def get_latest_blobs(count: int = 10) -> list:
    """Fetch the latest blobs from the bucket, sorted newest first."""
    require_bucket_name()

    client = get_client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = list(bucket.list_blobs())

    blobs.sort(key=lambda b: b.updated, reverse=True)
    return blobs[:count]


def is_public(blob) -> bool:
    """Check if a blob is publicly accessible."""
    blob.reload()
    for entry in blob.acl:
        if entry.get('entity') == 'allUsers' and entry.get('role') == 'READER':
            return True
    return False


def print_blob_list(blobs: list):
    """Print a numbered list of blobs with public/private status."""
    if not blobs:
        print('Bucket is empty.')
        return

    print(f'Latest {len(blobs)} file(s) in gs://{BUCKET_NAME}:\n')
    for i, b in enumerate(blobs, 1):
        size_kb = b.size / 1024
        access = 'public' if is_public(b) else 'private'
        print(f'  {i:>3}.  [{access:<7}]  {b.name:<40} {size_kb:>8.1f} KB  {b.updated:%Y-%m-%d %H:%M:%S}')


def list_files(count: int = 10):
    """List the most recently uploaded files in the bucket."""
    print_blob_list(get_latest_blobs(count))


def delete(object_name: str | None = None):
    """Delete a file from the bucket. If no name given, show interactive picker."""
    require_bucket_name()

    if object_name is None:
        blobs = get_latest_blobs()
        if not blobs:
            print('Bucket is empty.')
            return

        print_blob_list(blobs)
        print()
        choice = input('Enter file number to delete (or "q" to cancel): ').strip()

        if choice.lower() == 'q':
            print('Cancelled.')
            return

        try:
            index = int(choice) - 1
            if not 0 <= index < len(blobs):
                raise ValueError
        except ValueError:
            print('Invalid selection.', file=sys.stderr)
            sys.exit(1)

        blob = blobs[index]
        confirm = input(f'Delete "{blob.name}"? [y/N] ').strip().lower()
        if confirm != 'y':
            print('Cancelled.')
            return

        blob.delete()
        print(f'Deleted gs://{BUCKET_NAME}/{blob.name}')
    else:
        client = get_client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(object_name)

        if not blob.exists():
            print(f'Error: "{object_name}" not found in gs://{BUCKET_NAME}', file=sys.stderr)
            sys.exit(1)

        blob.delete()
        print(f'Deleted gs://{BUCKET_NAME}/{object_name}')


def make_private(object_name: str | None = None):
    """Revoke public access on a file. If no name given, show interactive picker."""
    require_bucket_name()

    if object_name is None:
        blobs = get_latest_blobs()
        if not blobs:
            print('Bucket is empty.')
            return

        print_blob_list(blobs)
        print()
        choice = input('Enter file number to make private (or "q" to cancel): ').strip()

        if choice.lower() == 'q':
            print('Cancelled.')
            return

        try:
            index = int(choice) - 1
            if not 0 <= index < len(blobs):
                raise ValueError
        except ValueError:
            print('Invalid selection.', file=sys.stderr)
            sys.exit(1)

        blob = blobs[index]
    else:
        client = get_client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(object_name)

        if not blob.exists():
            print(f'Error: "{object_name}" not found in gs://{BUCKET_NAME}', file=sys.stderr)
            sys.exit(1)

    blob.acl.all().revoke_read()
    blob.acl.save()
    print(f'Made private: gs://{BUCKET_NAME}/{blob.name}')


def usage():
    name = sys.argv[0]
    print(f'Usage:', file=sys.stderr)
    print(f'  {name} upload <file_path>    Upload a file and make it public', file=sys.stderr)
    print(f'  {name} list [count]           List latest files (default 10)', file=sys.stderr)
    print(f'  {name} delete [object_name]   Delete a file (interactive if no name given)', file=sys.stderr)
    print(f'  {name} private [object_name]  Make a file private (interactive if no name given)', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()

    command = sys.argv[1]

    if command == 'upload':
        if len(sys.argv) != 3:
            usage()
        upload(sys.argv[2])
    elif command == 'list':
        count = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
        list_files(count)
    elif command == 'delete':
        delete(sys.argv[2] if len(sys.argv) >= 3 else None)
    elif command == 'private':
        make_private(sys.argv[2] if len(sys.argv) >= 3 else None)
    else:
        usage()