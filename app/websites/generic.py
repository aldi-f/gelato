import ffmpeg
import requests
import tempfile

from websites.base import Base


class Generic(Base):
    _ffmpeg_codec = "libx264"
    

    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        content = requests.get(self.url).content
        with open(output_name, "wb") as file:
            file.write(content)

        # extra steps after downloading
        # self._convert_to_mp4()
        # self._compress()


    def _convert_to_mp4(self):
        input_file = self.output_path[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        (ffmpeg
        .input(input_file)
        .output(output_name, f='mp4', vcodec=self._ffmpeg_codec)
        .run())


    # def _compress(self):
    #     input_file = self.output_path[-1]
    #     with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
    #         output_name = temp_file.name
    #         self.output_path.append(output_name)

        # compress logic here
