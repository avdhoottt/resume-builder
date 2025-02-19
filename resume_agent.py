from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate

from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain.memory import ConversationBufferMemory
from typing import List, Dict
import spacy
import re
import PyPDF2
import docx
import asyncio
from pydantic import BaseModel, Field

class SkillsMatch(BaseModel):
    matched: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)

class FormatAnalysis(BaseModel):
    structure: str = Field(default="Needs Improvement")
    clarity: str = Field(default="Good")
    length: str = Field(default="Appropriate")

class ResumeAnalysis(BaseModel):
    score: float = Field(default=0.0)
    skills_match: SkillsMatch = Field(default_factory=SkillsMatch)
    suggestions: List[str] = Field(default_factory=list)
    format: FormatAnalysis = Field(default_factory=FormatAnalysis)

class ResumeTools:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using NLP"""
        doc = self.nlp(text.lower())
        skills = set()

        skill_patterns = [
            r'\b(python|java|javascript|react|angular|vue|node\.js|aws|azure|git)\b',
            r'\b(machine learning|artificial intelligence|data science|blockchain)\b',
            r'\b(sql|mongodb|postgresql|mysql|oracle)\b',
            r'\b(docker|kubernetes|jenkins|ci/cd)\b',
            r'\b(agile|scrum|kanban|waterfall)\b'
        ]

        for pattern in skill_patterns:
            matches = re.finditer(pattern, text.lower())
            skills.update(match.group() for match in matches)

        return sorted(list(skills))

    def analyze_format(self, text: str) -> Dict:
        """Analyze resume format and structure"""
        sections = self._identify_sections(text)
        return {
            "structure": self._evaluate_structure(sections),
            "clarity": self._evaluate_clarity(text),
            "length": self._evaluate_length(text)
        }

    async def calculate_match_score(self, resume_text: str, job_description: str) -> float:
        """Calculate match score between resume and job description"""
        resume_skills = set(self.extract_skills(resume_text))
        job_skills = set(self.extract_skills(job_description))

        if not job_skills:
            return 0.0

        matched_skills = resume_skills.intersection(job_skills)
        score = len(matched_skills) / len(job_skills) * 100
        return min(round(score, 2), 100)

    def _identify_sections(self, text: str) -> List[str]:
        common_sections = ["education", "experience", "skills", "projects", "certifications", "achievements", "summary"]
        return [section for section in common_sections if re.search(rf"\b{section}\b", text.lower())]

    def _evaluate_structure(self, sections: List[str]) -> str:
        essential_sections = {"education", "experience", "skills"}
        found_essential = essential_sections.intersection(set(sections))

        if len(found_essential) == len(essential_sections):
            return "Excellent"
        elif len(found_essential) >= 2:
            return "Good"
        return "Needs Improvement"

    def _evaluate_clarity(self, text: str) -> str:
        sentences = [sent.text.strip() for sent in self.nlp(text).sents]
        avg_length = sum(len(sent.split()) for sent in sentences) / len(sentences) if sentences else 0

        if avg_length < 8:
            return "Too Concise"
        elif avg_length > 20:
            return "Too Verbose"
        return "Good"

    def _evaluate_length(self, text: str) -> str:
        word_count = len(text.split())

        if word_count < 200:
            return "Too Short"
        elif word_count > 1000:
            return "Too Long"
        return "Appropriate"

class ResumeAgent:
    def __init__(self):
        self.llm = Ollama(model="llama2")
        self.tools = ResumeTools()
        self.memory = ConversationBufferMemory()

        # Define available tools
        self.tool_list = [
            Tool(name="extract_skills", func=self.tools.extract_skills, description="Extracts skills from a resume."),
            Tool(name="analyze_format", func=self.tools.analyze_format, description="Analyzes the resume format."),
            Tool(name="calculate_match_score", func=self.tools.calculate_match_score, description="Calculates resume-job match score."),
        ]

        # Ensure tools and tool_names are correctly formatted
        tool_names = [tool.name for tool in self.tool_list]
        tools_str = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tool_list])

        # Define the prompt template with correctly formatted variables
        template = '''You are an expert resume analyzer. Analyze the resume against the job description.

Available tools:
{tools}

Tool Names: {tool_names}

Step 1: Extract skills from both documents
Step 2: Calculate the match score
Step 3: Analyze the resume format
Step 4: Generate specific suggestions for improvement

Question: {input}
{agent_scratchpad}'''

        self.prompt_template = PromptTemplate.from_template(template)


        # Ensure that the tools list is properly registered before passing it to the agent
        if not self.tool_list:
            raise ValueError("No tools are defined for the agent.")

        # Create the agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tool_list,
            prompt=self.prompt_template
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tool_list,
            memory=self.memory,
            verbose=True
        )

    async def analyze_resume(self, resume_text: str, job_description: str) -> ResumeAnalysis:
        """Analyze a resume against a job description"""
        try:
            resume_skills = self.tools.extract_skills(resume_text)
            job_skills = self.tools.extract_skills(job_description)
            score = await self.tools.calculate_match_score(resume_text, job_description)
            format_analysis = self.tools.analyze_format(resume_text)

            suggestions = self._generate_suggestions(resume_skills, job_skills, format_analysis)

            return ResumeAnalysis(
                score=score,
                skills_match=SkillsMatch(matched=list(set(resume_skills) & set(job_skills)), missing=list(set(job_skills) - set(resume_skills))),
                suggestions=suggestions,
                format=FormatAnalysis(**format_analysis)
            )
        except Exception as e:
            print(f"Error analyzing resume: {str(e)}")
            raise

    def _generate_suggestions(self, resume_skills: List[str], job_skills: List[str], format_analysis: Dict) -> List[str]:
        suggestions = []

        missing_skills = set(job_skills) - set(resume_skills)
        if missing_skills:
            suggestions.append(f"Add missing skills: {', '.join(missing_skills)}")

        if format_analysis['structure'] != 'Excellent':
            suggestions.append("Improve resume structure by including all essential sections (Education, Experience, Skills)")

        if format_analysis['clarity'] in ['Too Concise', 'Too Verbose']:
            suggestions.append("Optimize sentence length for better readability")

        if format_analysis['length'] in ['Too Short', 'Too Long']:
            suggestions.append("Adjust resume length to be between 200-1000 words")

        suggestions.extend([
            "Quantify achievements with specific metrics and results",
            "Use action verbs to describe experiences",
            "Ensure consistent formatting throughout the document"
        ])

        return suggestions
class ResumeProcessor:
    @staticmethod
    def extract_text_from_pdf(pdf_file) -> str:
        """Extract text from a PDF file."""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = []
            for page in pdf_reader.pages:
                text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    @staticmethod
    def extract_text_from_docx(docx_file) -> str:
        """Extract text from a DOCX file."""
        try:
            doc = docx.Document(docx_file)
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            return "\n".join(text)
        except Exception as e:
            raise Exception(f"Error extracting text from DOCX: {str(e)}")
