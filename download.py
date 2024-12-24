import requests
import os

def upload_file_to_signed_url(file_path, signed_url):
    """
    Upload a file to a pre-signed Google Cloud Storage URL.

    Args:
        file_path (str): Path to the file you want to upload
        signed_url (str): The pre-signed URL generated for upload

    Returns:
        bool: True if upload was successful, False otherwise
    """
    try:
        # Validate file exists
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return False

        # Determine content type based on file extension
        file_extension = os.path.splitext(file_path)[1].lower()
        content_type_map = {
            '.zip': 'application/zip',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.pdf': 'application/pdf',
            '.json': 'application/json',
            '.xml': 'application/xml',
            # Add more mappings as needed
            '': 'application/octet-stream'  # default binary
        }
        content_type = content_type_map.get(file_extension, 'application/octet-stream')

        # Open the file in binary read mode
        with open(file_path, 'rb') as file:
            file_data = file.read()

        # Send PUT request to the signed URL
        headers = {
            'Content-Type': content_type,
        }
        response = requests.put(
            signed_url,
            data=file_data,
            headers=headers
        )

        # Check upload status
        if response.status_code in [200, 204]:
            print(f"Successfully uploaded {file_path}")
            return True
        else:
            print(f"Upload failed. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"Error during file upload: {e}")
        return False

def main():
    # Example usage
    # Replace these with your actual values
    signed_url = "https://storage.googleapis.com/data_collections/uploads/file_20241214_003318.zip?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=terraform-builder%40virtual-video-assessor-dev.iam.gserviceaccount.com%2F20241214%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20241214T003318Z&X-Goog-Expires=900&X-Goog-SignedHeaders=content-type%3Bhost&X-Goog-Signature=4403f283b7e2a396409b9d3d929ab185ca4ccd890e7608218a0461cae410d4679138002a3d9aad68b785f894d64a5af5d5fc2085ba6666b3bf7fc4ceb43f271fa853bfe43a47f2095c2b69ef751c79a8fec14538b21d1710bde5f26533984fc57a6d50067c09b863bd5b190511959d3321ae99e4cb4e69dd280b2283df42352c2276ff0d14a9d7d71320035135e798b394203b616166758d43d98bdfddd5c1b0006d0d89253e589f13b80ce0555dcaacc6cc69bc586ee683aa7c189e6f2f687970a8b4e629b8303187ece50abada89be2713ae39712ebb782d9f6786e8a03d9dc68eceaf96ae4ff67c8713f974abc7d8bbda91a6f3a586f53dc0a283f0c475c3"
    file_to_upload = "C://Users//babas//Downloads//Kendra_Indian.zip"

    # Perform the upload
    upload_success = upload_file_to_signed_url(file_to_upload, signed_url)
    if upload_success:
        print("File upload completed successfully!")
    else:
        print("File upload failed.")

if __name__ == "__main__":
    main()
