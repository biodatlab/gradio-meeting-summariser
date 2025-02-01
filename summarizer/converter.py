from moviepy.editor import VideoFileClip

def convert_video_to_audio(input_path: str, output_path: str = None) -> None:
    """
    Convert video to audio using moviepy

    Args:
        input_path (str): Path to input video file
        output_path (str): Path to output audio file

    Example:
        convert_video_to_audio("video.mp4")
    """
    if output_path is None:
        output_path = input_path.rsplit('.', 1)[0] + '.mp3' # Default to mp3 format
    try:
        video = VideoFileClip(input_path)
        audio = video.audio
        audio.write_audiofile(output_path)
        video.close()
        audio.close()
        print(f"Converted {input_path} to {output_path}")
    except Exception as e:
        print(f"Error converting video: {str(e)}")