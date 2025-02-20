import requests
import tempfile

from websites.base import Base


class Generic(Base):
    
    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        content = requests.get(self.url).content
        with open(output_name, "wb") as file:
            file.write(content)
