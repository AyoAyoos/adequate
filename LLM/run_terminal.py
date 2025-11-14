# LLM/run_terminal.py
import os
from dotenv import load_dotenv

# CORRECTED IMPORT: The '.' tells Python to look for engine.py in the same folder.
from .engine import GuidanceEngine

# This helper function makes file paths work correctly, no matter where you run the script from.
def get_absolute_path(relative_path):
    """
    Constructs an absolute path from a path relative to the current script's location.
    """
    # Gets the directory where THIS script (run_terminal.py) is located.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Joins the script's directory with the relative path to get the full, correct path.
    return os.path.join(script_dir, relative_path)

def run_cli():
    """
    Runs the Command-Line Interface to interact with the GuidanceEngine.
    """
    # Load the .env file from the same directory as this script.
    load_dotenv(dotenv_path=get_absolute_path('.env'))

    # Use our helper function to define robust paths to the data files.
    CONFIG = {
        "student_data_path": get_absolute_path("data\Final_Sheet - Sheet3.csv"),
        "research_paper_path": get_absolute_path("data/Research_Paper.pdf"),
        "faiss_index_path": get_absolute_path("embeddings/faiss_index")
    }

    try:
        print("--- INITIALIZING GUIDANCE ENGINE (this may take a moment on first run)... ---")
        career_engine = GuidanceEngine(config=CONFIG)
        print("--- ENGINE INITIALIZED SUCCESSFULLY. READY FOR INPUT. ---")
    except Exception as e:
        print(f"\nFATAL ERROR during initialization: {e}")
        print("Please ensure your 'data' folder and '.env' file are correctly placed inside the 'LLM' directory.")
        return

    # --- Main Interaction Loop ---
    while True:
        print("\n" + "="*50)
        print("AI Career Guidance System")
        print("Enter student details below (type 'exit' at any prompt to quit).")
        print("="*50)

        enrollment = input("▶ Enter Enrollment Number (or press Enter if none): ").strip()
        if enrollment.lower() == 'exit': break

        try:
            aq_score_str = input("▶ Enter AQ Score (1-100): ").strip()
            if aq_score_str.lower() == 'exit': break
            aq_score = int(aq_score_str)
        except ValueError:
            print("❗ Invalid AQ Score. Please enter a number. Restarting...")
            continue

        skills_str = input("▶ Enter Skills (comma-separated, e.g., Python, SQL, Leadership): ").strip()
        if skills_str.lower() == 'exit': break
        skills = [s.strip() for s in skills_str.split(',') if s.strip()]

        traits_str = input("▶ Enter Traits (optional, comma-separated, e.g., C, O, R): ").strip()
        if traits_str.lower() == 'exit': break
        traits = [t.strip().upper() for t in traits_str.split(',') if t.strip()]

        print("\n🔄 Analyzing profile and generating recommendations...")
        
        recommendations = career_engine.generate_recommendations(
            enrollment=enrollment,
            aq_score=aq_score,
            skills=skills,
            traits=traits
        )

        # --- Display the Formatted Report ---
        print("\n" + "-"*20 + " 🎓 CAREER GUIDANCE REPORT " + "-"*20)
        print(f"  🧑 Enrollment ID: {enrollment or 'N/A'}")
        print(f"  🧠 AQ Score:      {aq_score}")
        print(f"  🛠️ Skills:        {', '.join(skills)}")
        if traits:
            print(f"  🧬 Traits:        {', '.join(traits)}")
        print("-"*62)
        print("  🧭 Top 3 Career Recommendations:")
        if recommendations:
            for i, career in enumerate(recommendations, 1):
                print(f"     {i}. {career}")
        else:
            print("     Could not generate specific recommendations based on the input.")
        print("-"*62)

if __name__ == '__main__':
    run_cli()

