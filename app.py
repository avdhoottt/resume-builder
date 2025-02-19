# app.py
import streamlit as st
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import json
import requests
from resume_agent import ResumeAgent, ResumeProcessor
import asyncio

# Configure Streamlit page
st.set_page_config(
    page_title="AI Resume Reviewer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Global Styles */
    .main {
        padding: 2rem;
        font-family: 'Inter', sans-serif;
    }

    /* Header Styles */
    .stTitle {
        color: #1E293B;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 1.5rem !important;
    }

    /* Upload Section Styles */
    .upload-section {
        background-color: #F8FAFC;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Button Styles */
    .stButton>button {
        width: 100%;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        color: white;
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        border: none;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }

    /* Metric Card Styles */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
        transition: transform 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-5px);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #4F46E5;
        margin: 0.5rem 0;
    }

    .metric-label {
        color: #64748B;
        font-size: 1rem;
        font-weight: 500;
    }

    /* Skills Section Styles */
    .skills-section {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        margin-top: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .skill-item {
        background: #F1F5F9;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        transition: all 0.2s ease;
    }

    .skill-item:hover {
        background: #E2E8F0;
        transform: translateX(5px);
    }

    /* Suggestion Styles */
    .suggestion-item {
        background: #F8FAFC;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        border-left: 4px solid #4F46E5;
        transition: all 0.2s ease;
    }

    .suggestion-item:hover {
        background: #F1F5F9;
        transform: translateX(5px);
    }

    /* Progress Animation */
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .progress-bar {
        background: linear-gradient(-45deg, #4F46E5, #7C3AED, #4F46E5);
        background-size: 200% 200%;
        animation: gradient 2s ease infinite;
        height: 4px;
        width: 100%;
        border-radius: 2px;
    }

    /* File Upload Styles */
    .upload-box {
        border: 2px dashed #CBD5E1;
        padding: 2rem;
        text-align: center;
        border-radius: 12px;
        background: #F8FAFC;
        transition: all 0.3s ease;
    }

    .upload-box:hover {
        border-color: #4F46E5;
        background: #F1F5F9;
    }

    /* Text Area Styles */
    .stTextArea>div>div>textarea {
        border-radius: 12px;
        border: 2px solid #CBD5E1;
        padding: 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }

    .stTextArea>div>div>textarea:focus {
        border-color: #4F46E5;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Load Lottie animation
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# Initialize session state variables
if 'agent' not in st.session_state:
    st.session_state.agent = ResumeAgent()
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

def create_radar_chart(skills_data):
    categories = list(skills_data.keys())
    values = list(skills_data.values())

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Resume Score',
        line=dict(color='#4F46E5'),
        fillcolor='rgba(79, 70, 229, 0.2)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10),
                gridcolor='#E2E8F0'
            ),
            angularaxis=dict(
                tickfont=dict(size=12)
            ),
            bgcolor='white'
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=80, r=80, t=40, b=40)
    )
    return fig

def display_analysis_results(analysis):
    # Metrics Section
    st.markdown("### 📊 Analysis Overview")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Overall Match</div>
                <div class="metric-value">{analysis.score:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Format Quality</div>
                <div class="metric-value">{analysis.format.structure}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        total_skills = len(analysis.skills_match.matched) + len(analysis.skills_match.missing)
        matched_skills = len(analysis.skills_match.matched)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Skills Match</div>
                <div class="metric-value">{matched_skills}/{total_skills}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Skills Analysis Section
    st.markdown("### 🎯 Skills Analysis")
    skills_col1, skills_col2 = st.columns(2)

    with skills_col1:
        st.markdown('<div class="skills-section">', unsafe_allow_html=True)
        st.markdown("#### ✅ Matched Skills")
        for skill in analysis.skills_match.matched:
            st.markdown(
                f'<div class="skill-item">✨ {skill}</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with skills_col2:
        st.markdown('<div class="skills-section">', unsafe_allow_html=True)
        st.markdown("#### ❌ Missing Skills")
        for skill in analysis.skills_match.missing:
            st.markdown(
                f'<div class="skill-item">💡 {skill}</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # Radar Chart
    st.markdown("### 📈 Skills Breakdown")
    skills_data = {
        'Technical Skills': (len(analysis.skills_match.matched) / max(1, total_skills)) * 100,
        'Format': 95 if analysis.format.structure == "Excellent" else 80 if analysis.format.structure == "Good" else 60,
        'Overall Match': analysis.score
    }

    st.plotly_chart(create_radar_chart(skills_data), use_container_width=True)

    # Improvement Suggestions
    st.markdown("### 💡 Improvement Suggestions")
    for suggestion in analysis.suggestions:
        st.markdown(
            f'<div class="suggestion-item">✨ {suggestion}</div>',
            unsafe_allow_html=True
        )

async def analyze_resume(resume_file, job_description):
    try:
        resume_text = ResumeProcessor.extract_text_from_pdf(resume_file) if resume_file.type == "application/pdf" else ResumeProcessor.extract_text_from_docx(resume_file)
        analysis = await st.session_state.agent.analyze_resume(resume_text, job_description)
        return analysis
    except Exception as e:
        st.error(f"An error occurred during analysis: {str(e)}")
        return None

def main():
    # Header Section
    st.title("🤖 AI Resume Reviewer")
    st.markdown("### Transform your resume with AI-powered insights")

    # Load and display Lottie animation
    lottie_url = "https://assets4.lottiefiles.com/packages/lf20_xyadoh9h.json"
    lottie_json = load_lottieurl(lottie_url)
    if lottie_json:
        st_lottie(lottie_json, height=200, key="resume_animation")

    # Upload Section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📄 Upload Resume")
        resume_file = st.file_uploader(
            "Drop your resume here (PDF or DOCX)",
            type=["pdf", "docx"],
            key="resume_uploader"
        )

    with col2:
        st.markdown("### 💼 Job Description")
        job_description = st.text_area(
            "Paste the job description here",
            height=150,
            key="job_description"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Analysis Button
    if st.button("🔍 Analyze Resume", key="analyze_button"):
        if resume_file is None or not job_description:
            st.error("⚠️ Please upload both resume and job description!")
            return

        with st.spinner("🤖 AI is analyzing your resume..."):
            # Add progress bar
            st.markdown('<div class="progress-bar"></div>', unsafe_allow_html=True)

            analysis = asyncio.run(analyze_resume(resume_file, job_description))

            if analysis:
                st.success("✅ Analysis Complete!")
                st.session_state.analysis_results = analysis
                st.session_state.analysis_complete = True

    # Display results if analysis is complete
    if st.session_state.analysis_complete and st.session_state.analysis_results:
        display_analysis_results(st.session_state.analysis_results)

if __name__ == "__main__":
    main()
