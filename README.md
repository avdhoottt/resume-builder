# AI Resume Reviewer 🤖

An AI-powered application that analyzes resumes against job descriptions to provide actionable insights and improvement suggestions.

## Demo

Try it out here: [AI Resume Reviewer Demo](https://huggingface.co/spaces/Avdhoottt/resume-reviewer)

![Hero Section](/images/resume-builder-1.png)
![Input Features](/images/resume-builder-2.png)
![Analyze](/images/resume-builder-3.png)
![Improvements section](/images/resume-builder-4.png)

## Features

- 📄 Resume parsing (PDF & DOCX support)
- 🎯 Skills matching and analysis
- 📊 Interactive visualizations
- 💡 Smart suggestions for improvement
- 🔍 Detailed format analysis
- 📈 Match score calculation
- 🎨 Modern, responsive UI

## Tech Stack

- Streamlit
- LangChain
- Ollama (LLaMA2)
- Plotly
- spaCy
- PyPDF2
- python-docx
- Lottie animations

## Local Setup

1. Clone the repository:

```bash
git clone https://github.com/avdhoottt/resume-builder.git
cd resume-builder
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Download spaCy model:

```bash
python -m spacy download en_core_web_sm
```

5. Install and start Ollama:

```bash
# macOS/Linux
curl https://ollama.ai/install.sh | sh
ollama run llama2

# Windows
# Download from https://ollama.ai/download/windows
# Then run:
ollama run llama2
```

6. Run the application:

```bash
streamlit run app.py
```

7. Open your browser and navigate to:

```
http://localhost:8501
```

## Project Structure

```
ai-resume-reviewer/
├── app.py              # Main Streamlit application
├── resume_agent.py     # Resume analysis agent and tools
├── requirements.txt    # Project dependencies
└── README.md          # Project documentation
```

## Configuration

The application uses several key configurations:

- Streamlit page configuration in `app.py`
- LLM model configuration in `resume_agent.py`
- Custom styling in `app.py`
- Resume analysis tools in `resume_agent.py`

Made with ❤️ by avdhoottt
