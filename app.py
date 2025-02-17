import os
import shutil
import gradio as gr
import argparse
from pathlib import Path
import google.generativeai as genai
from summarizer.summarizer import summarise_from_file
from summarizer.transcriber import convert_mp4_to_wav, split_audio, transcribe_audio_folder


def parse_args():
    parser = argparse.ArgumentParser(description='Speech Processing App with Authentication')
    parser.add_argument('--username', type=str, help='Username for authentication')
    parser.add_argument('--password', type=str, help='Password for authentication')
    return parser.parse_args()


def init_model():
    assert "GEMINI_API_KEY" in os.environ, "Please set the GEMINI_API_KEY environment variable"
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    return genai.GenerativeModel('models/gemini-1.5-flash')


def clear_segments(segment_folder="segments"):
    print(f"Clearing and creating {segment_folder} folder...")
    if os.path.exists(segment_folder):
        shutil.rmtree(segment_folder)
    os.makedirs(segment_folder, exist_ok=True)


def process_audio(audio_file, should_summarize):
    """Process audio file: convert, segment, transcribe and optionally summarize"""
    try:
        if audio_file is None:
            raise gr.Error("Please upload an audio file")

        # Create paths for processing
        input_path = audio_file.name  # Temporary uploaded file path
        output_wav_name = Path(audio_file.name).stem + '.wav'
        output_wav_path = str(Path(input_path).parent / output_wav_name)
        
        # Clear and recreate segments folder
        segment_folder = "segments"
        clear_segments(segment_folder)

        # Process audio
        print(f"Converting {input_path} to {output_wav_path}")
        convert_mp4_to_wav(input_path)  # This should output to output_wav_path

        print(f"Splitting audio from {output_wav_path}")
        split_audio(output_wav_path, segment_folder)
        
        # Transcribe
        print("Transcribing segments...")
        prompt = "Please transcribe the given recorded interview speech."
        transcription_file = f"{Path(audio_file.name).stem}_transcriptions.csv"
        df = transcribe_audio_folder(model, str(segment_folder), prompt=prompt)
        df.to_csv(transcription_file, index=False)
        
        if should_summarize:
            # Summarize if requested
            output_summary_file = f"{Path(audio_file.name).stem}_summary.docx"
            markdown_summary, summary_file = summarise_from_file(model, transcription_file, output_summary_file)
            return transcription_file, markdown_summary, summary_file
        
        return transcription_file, None, None
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # This will help debug the exact error
        raise gr.Error(f"Error processing audio: {str(e)}")


def summarize_transcript(transcript_file):
    """Summarize uploaded transcript file"""
    try:
        if transcript_file is None:
            raise gr.Error("Please upload a transcript file")
        output_summary_file = f"summary_{Path(transcript_file.name).stem}.docx"
        markdown_summary, summary_docx = summarise_from_file(model, transcript_file.name, output_summary_file)
        return markdown_summary, summary_docx
    except Exception as e:
        raise gr.Error(f"Error summarizing transcript: {str(e)}")


# Create Gradio interface
def create_app(auth=None):
    with gr.Blocks(title="Speech Processing and Summarization") as demo:
        gr.Image(value="assets/mahidol_logo.png", show_label=False, container=False, width=400)
        gr.Markdown("# Speech Processing and Summarization Tool")
        gr.Markdown("""
        แอปพลิเคชันนี้ช่วยในการถอดความและสรุปเนื้อหาจากไฟล์เสียงโดยเน้นการสรุปแบบราชการ โดยมีฟีเจอร์หลัก 2 ส่วน:

        ### 1. การประมวลผลไฟล์เสียง 🎙️
        - อัพโหลดไฟล์เสียง (รองรับไฟล์ MP3 และรูปแบบเสียงทั่วไป)
        - ระบบจะถอดความเสียงพูดให้โดยอัตโนมัติและสามารถเลือกให้สรุปเนื้อหาจากบทถอดความได้ (Generate Summary)
        - ดาวน์โหลดผลลัพธ์ได้ทั้งไฟล์ถอดความและรายงานสรุป

        ### 2. การสรุปจากบทถอดความ 📝
        - อัพโหลดไฟล์บทถอดความ (รองรับไฟล์ TXT และ CSV)
        - ระบบจะวิเคราะห์และสรุปเนื้อหาให้โดยอัตโนมัติ และสามารถดาวน์โหลดรายงานสรุปในรูปแบบ DOCX
        """)
        
        with gr.Tabs():
            # Audio Processing Tab
            with gr.Tab("Audio Processing"):
                gr.Markdown("Upload an audio file for transcription and optional summarization")
                
                with gr.Column():
                    # Changed to File component for audio upload
                    audio_input = gr.File(
                        label="Upload Audio File",
                        file_types=["audio"]
                    )
                    summarize_checkbox = gr.Checkbox(label="Generate Summary", value=False)
                    process_button = gr.Button("Process Audio")
                    
                    transcript_output = gr.File(label="Download Transcription")
                    summary_text = gr.Markdown(label="Summary", visible=False)
                    summary_file = gr.File(label="Download Summary", visible=False)


                def update_visibility(should_summarize):
                    return {
                        summary_text: gr.update(visible=should_summarize),
                        summary_file: gr.update(visible=should_summarize)
                    }
                
                summarize_checkbox.change(
                    update_visibility,
                    inputs=[summarize_checkbox],
                    outputs=[summary_text, summary_file]
                )
                
                process_button.click(
                    process_audio,
                    inputs=[audio_input, summarize_checkbox],
                    outputs=[transcript_output, summary_text, summary_file]
                )


            # Transcript Summarization Tab
            with gr.Tab("Transcript Summarization"):
                gr.Markdown("Upload a transcript file (TXT or CSV) for summarization")
                
                with gr.Column():
                    transcript_input = gr.File(
                        label="Upload Transcript",
                        file_types=[".txt", ".csv"]
                    )
                    summarize_button = gr.Button("Generate Summary")
                    
                    summary_output_text = gr.Markdown(label="Summary")
                    summary_output_file = gr.File(label="Download Summary Report")
                
                summarize_button.click(
                    summarize_transcript,
                    inputs=[transcript_input],
                    outputs=[summary_output_text, summary_output_file]
                )
    return demo

if __name__ == "__main__":
    args = parse_args()
    model = init_model()

    auth = None
    if args.username and args.password:
        auth = (args.username, args.password)
    
    demo = create_app(auth)
    demo.queue().launch(auth=auth)
