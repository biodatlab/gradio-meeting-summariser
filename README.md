# MU Meeting Summary

Gradio application for automatic transcription and summarization of meeting recordings using Gemini API. The application generates summaries in a structured governmental report format.


## Usage

Clone the repository and install dependencies:

```sh
git clone https://github.com/titipata/gradio_mu_meeting_summary
pip install -r requirements.txt
```

Then set up Gemini API key

```sh
export GEMINI_API_KEY="..."
```

Run `gradio` application with a given `app.py` file

```py
python app.py
```

<p align="center">
  <img src="assets/example_interface.png" width="500"/>
</p>