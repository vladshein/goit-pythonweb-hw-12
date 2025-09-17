import cloudinary
import cloudinary.uploader


class UploadFileService:
    def __init__(self, cloud_name, api_key, api_secret):
        """
        Initialize the UploadFileService with the given cloud name, api key and api secret.

        :param cloud_name: The cloud name to use for the Cloudinary API.
        :param api_key: The API key to use for the Cloudinary API.
        :param api_secret: The API secret to use for the Cloudinary API.
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username) -> str:
        """
        Upload a file to Cloudinary and return the URL of the uploaded file.

        :param file: The file to upload.
        :param username: The username of the user who is uploading the file.
        :return: The URL of the uploaded file.
        :rtype: str
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
