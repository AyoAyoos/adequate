# LLM/engine.py
import os
import pandas as pd
import difflib
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
# FINAL IMPORT: This uses the new, dedicated HuggingFace package.
from langchain_huggingface import HuggingFaceEmbeddings

# This relative import is correct for our structure.
from .prompts import career_prompt_template_simple

def get_trait_based_suggestions(traits: list[str]) -> list[str]:
    trait_map = {
        "C+O": ("Strong decision-maker with responsibility", ["Manager", "Admin Head", "NGO Director"]),
        "C+R": ("Can handle pressure and multiple areas", ["Event Planner", "Product Manager"]),
        "C+E": ("Stays composed & resilient for long terms", ["Police", "Government Officer", "Army"]),
        "C+A": ("Positive leader who inspires others", ["HR Manager", "Motivational Coach"]),
        "O+R": ("Self-driven and adaptable across domains", ["Startup Founder", "Project Consultant"]),
        "O+E": ("Determined initiator with long-term vision", ["Researcher", "Business Owner", "Civil Services"]),
        "O+A": ("Responsible & optimistic individual", ["Educator", "Youth Counselor", "Team Lead"]),
        "R+E": ("Manages multitasking under long-term stress", ["Software Engineer", "Media Planner"]),
        "R+A": ("Juggles multiple tasks while spreading positivity", ["Social Media Manager", "Campaign Organizer"]),
        "E+A": ("Perseveres with positive attitude", ["Psychologist", "Teacher", "UPSC Aspirant"]),
        "C+O+A": ("Confident, responsible, and positive leader", ["Principal", "Entrepreneur", "NGO Leader"])
    }
    if not traits: return []
    traits_key = "+".join(sorted(set(traits))).upper()
    for key, value in trait_map.items():
        # Unpack the tuple to get the description (unused for now) and roles
        _description, roles = value
        key_set = set(key.split("+"))
        if key_set.issubset(set(traits_key.split("+"))):
            return roles
    return []


class GuidanceEngine:
    def __init__(self, config: dict):
        print("Initializing GuidanceEngine...")
        self.config = config
        self.student_df = self._load_student_data()
        self.all_skills_from_csv = self._extract_all_skills()
        self.qa_chain = self._initialize_rag_pipeline()
        print("GuidanceEngine ready.")

    def _load_student_data(self):
        path = self.config['student_data_path']
        print(f"Loading student records from {path}...")
        if not os.path.exists(path): raise FileNotFoundError(f"Student data file not found: {path}")
        return pd.read_csv(path)

    def _extract_all_skills(self):
        skills_set = set()
        for raw in self.student_df["Final Skills"].dropna():
            skills = [s.strip().capitalize() for s in str(raw).strip("[]'").split(",") if s.strip()]
            skills_set.update(skills)
        return sorted(list(skills_set))

    def _initialize_rag_pipeline(self):
        print("Initializing LangChain RAG pipeline...")
        llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))
        embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        index_path = self.config['faiss_index_path']
        paper_path = self.config['research_paper_path']

        if os.path.exists(index_path):
            print(f"Loading existing FAISS index from {index_path}...")
            db = FAISS.load_local(index_path, embedder, allow_dangerous_deserialization=True)
        else:
            print(f"Building FAISS index from {paper_path}...")
            if not os.path.exists(paper_path): raise FileNotFoundError(f"Research paper not found: {paper_path}")
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            loader = PyPDFLoader(paper_path)
            pages = loader.load_and_split()
            db = FAISS.from_documents(pages, embedder)
            db.save_local(index_path)
            print(f"FAISS index built and saved to {index_path}.")

        return RetrievalQA.from_chain_type(llm=llm, retriever=db.as_retriever(), chain_type="stuff")

    def _correct_skills(self, skills: list[str]) -> list[str]:
        corrected = [difflib.get_close_matches(s.lower(), [sk.lower() for sk in self.all_skills_from_csv], n=1, cutoff=0.7) for s in skills]
        return [match[0].capitalize() if match else skill.capitalize() for skill, match in zip(skills, corrected)]

    def _get_student_profile(self, enrollment: str, aq: int, skills: list[str]) -> dict:
        corrected_skills = self._correct_skills(skills)
        profile = {"enrollment": enrollment or "N/A", "aq": aq, "skills": corrected_skills, "suggested_role": None}
        if enrollment:
            match = self.student_df[self.student_df['Enrollment Number'] == enrollment]
            if not match.empty:
                profile["suggested_role"] = match.iloc[0].get("Suggested Role", "").strip()
        return profile

    def generate_recommendations(self, enrollment: str, aq_score: int, skills: list[str], traits: list[str]) -> list[str]:
        profile = self._get_student_profile(enrollment, aq_score, skills)

        # Step 1: Determine the AQ Category based on the score.
        if aq_score >= 180:
            aq_category = {"name": "Climber", "description": "You excel at navigating challenges and consistently seek growth. You are highly resilient and resourceful."}
        elif aq_score >= 140:
            aq_category = {"name": "Camper", "description": "You are steady and reliable, but may sometimes avoid difficult challenges to stay in a comfortable zone."}
        else:
            aq_category = {"name": "Quitter", "description": "You may feel overwhelmed by adversity and have an opportunity to develop stronger resilience strategies."}
        
        # Step 2: Format the full description to pass to the prompt.
        aq_profile_description = f"{aq_category['name']} - {aq_category['description']}"

        # Step 3: Format the prompt, now including the new variable. This is the fix.
        prompt_text = career_prompt_template_simple.format(
            aq_score=profile["aq"],
            skills=", ".join(sorted(profile["skills"], key=str.lower)),
            traits=" + ".join(sorted(traits)) if traits else "None",
            aq_profile_description=aq_profile_description # This line fixes the KeyError
        )
        
        # Step 4: Invoke the LLM and process the results.
        llm_output = self.qa_chain.invoke(prompt_text)
        llm_result_text = llm_output.get('result', '')

        llm_careers = [line.split(".", 1)[1].strip() for line in llm_result_text.strip().split("\n") if "." in line]
        trait_careers = get_trait_based_suggestions(traits)
        
        final_careers, seen = [], set()
        if profile["suggested_role"]:
            final_careers.append(profile["suggested_role"])
            seen.add(profile["suggested_role"].lower())
            
        for career in llm_careers + trait_careers:
            if career.lower() not in seen:
                final_careers.append(career)
                seen.add(career.lower())
        
        return final_careers[:3]