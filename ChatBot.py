"""
Install dependencies:
    pip install google-generativeai textblob
    python -m textblob.download_corpora
"""

import json
import re
from string import Template
from datetime import datetime, timedelta, timezone
from textblob import TextBlob  # For sentiment analysis

import google.generativeai as genai

# ----------------------------
# CONFIGURE GEMINI
# ----------------------------
genai.configure(api_key="AIzaSyDWyYmlvq0xZImhrL43JAIkqKeiwOpv30Y")

generation_config = {
    "temperature": 0.3,  # Lower temperature for more factual medical responses
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

# ----------------------------
# MEDICINE AI ASSISTANT PROMPT TEMPLATE
# ----------------------------
MEDICINE_PROMPT_TMPL = Template(r"""
You are a Medicine AI Assistant, a professional healthcare chatbot that provides accurate, reliable information about medications.
Your role is to answer questions about medicines with factual, evidence-based information while emphasizing that users should always consult healthcare professionals.

For each medicine query, provide a STRICT JSON object with:

1) medicine_name (the exact name of the medication)
2) generic_name (generic/chemical name if available)
3) uses (primary medical uses and indications)
4) dosage (typical dosage information - emphasize this may vary)
5) side_effects (common and serious side effects)
6) precautions (warnings, contraindications, special precautions)
7) interactions (drug-drug and drug-food interactions)
8) storage (storage conditions and requirements)
9) pregnancy_category (if applicable - FDA pregnancy categories)
10) availability (prescription status: OTC, Rx-only, etc.)
11) manufacturer (common manufacturers if known)
12) safety_warning (important safety alerts and disclaimers)

IMPORTANT: Always include a clear disclaimer that this is informational only and not medical advice.

Example Output:
{
  "medicine_name": "Ibuprofen",
  "generic_name": "Ibuprofen",
  "uses": ["Pain relief", "Fever reduction", "Anti-inflammatory"],
  "dosage": "Adults: 200-400mg every 4-6 hours as needed (max 1200mg/day). Always follow doctor's instructions.",
  "side_effects": ["Upset stomach", "Heartburn", "Nausea", "Dizziness", "Rare: Gastrointestinal bleeding"],
  "precautions": ["Do not use if allergic to NSAIDs", "Avoid with kidney disease", "Use caution with heart conditions"],
  "interactions": ["Blood thinners (warfarin)", "Other NSAIDs", "ACE inhibitors", "Diuretics"],
  "storage": "Store at room temperature, away from moisture and heat",
  "pregnancy_category": "Category C (consult doctor before use during pregnancy)",
  "availability": "OTC and prescription strengths available",
  "manufacturer": ["Advil", "Motrin", "Generic brands"],
  "safety_warning": "WARNING: This information is for educational purposes only. Always consult a healthcare professional before taking any medication. Do not self-medicate."
}

Now answer this medicine question:

Question: ${question}
User Context: ${context}

Rules:
- RETURN VALID JSON ONLY (no markdown, no extra text)
- Use double quotes for all strings
- Include ALL fields (set to "Not specified" if unknown)
- Be factual and evidence-based
- Always include safety warnings and disclaimers
- Do not provide dosage recommendations for specific individuals
""")


# ----------------------------
# MEDICINE-SPECIFIC HELPER FUNCTIONS
# ----------------------------
def now_ist_str():
    """Return current IST time formatted as 'YYYY-MM-DD HH:MM'."""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M")

def analyze_sentiment(text: str) -> str:
    """Perform basic sentiment analysis using TextBlob"""
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0.1:
        return "positive"
    elif analysis.sentiment.polarity < -0.1:
        return "negative"
    return "neutral"

def extract_keywords(text: str) -> list:
    """Extract important medical keywords"""
    medical_terms = ['mg', 'dose', 'tablet', 'capsule', 'injection', 'syrup', 'cream', 'ointment']
    blob = TextBlob(text)
    nouns = [word.lower() for word, tag in blob.tags if tag.startswith('NN')]
    # Prioritize medical terms
    keywords = list(set([word for word in nouns if word in medical_terms] + nouns))[:8]
    return keywords

def build_medicine_prompt(question: str, context: str) -> str:
    return MEDICINE_PROMPT_TMPL.substitute(
        question=question.strip(),
        context=context.strip(),
        now_ist=now_ist_str(),
    )

def extract_json(text: str):
    """Robust JSON extraction with improved error handling"""
    try:
        # First try direct parse
        text = text.strip()
        if text.startswith('{') and text.endswith('}'):
            return json.loads(text)
        
        # Handle code fences if present
        fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        if fenced:
            return json.loads(fenced.group(1))
        
        # Fallback: find first complete JSON object
        first = text.find('{')
        last = text.rfind('}')
        if first != -1 and last != -1:
            return json.loads(text[first:last+1])
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
    return None

def normalize_medicine_result(d: dict) -> dict:
    """Normalize medicine information with proper defaults"""
    if not isinstance(d, dict):
        return {}
    
    # Ensure all required fields exist with appropriate defaults
    out = {
        "medicine_name": d.get("medicine_name", "Not specified").strip(),
        "generic_name": d.get("generic_name", "Not specified").strip(),
        "uses": list(set(d.get("uses", ["Not specified"]))),
        "dosage": d.get("dosage", "Consult healthcare professional for proper dosage").strip(),
        "side_effects": list(set(d.get("side_effects", ["Not specified"]))),
        "precautions": list(set(d.get("precautions", ["Not specified"]))),
        "interactions": list(set(d.get("interactions", ["Not specified"]))),
        "storage": d.get("storage", "Store as per manufacturer instructions").strip(),
        "pregnancy_category": d.get("pregnancy_category", "Consult doctor before use during pregnancy").strip(),
        "availability": d.get("availability", "Not specified").strip(),
        "manufacturer": list(set(d.get("manufacturer", ["Various manufacturers"]))),
        "safety_warning": d.get("safety_warning", "WARNING: Always consult a healthcare professional before taking any medication. This information is for educational purposes only.").strip()
    }
    
    return out

def get_medicine_info(question: str, context: str) -> dict | None:
    """Get medicine information from AI model"""
    prompt = build_medicine_prompt(question, context)
    try:
        convo = model.start_chat(history=[])
        convo.send_message(prompt)
        raw = convo.last.text
        data = extract_json(raw)
        
        if not data:
            print("\n[WARN] Model returned invalid JSON. Providing basic information...")
            # Fallback response
            return {
                "medicine_name": question.split()[0] if question.split() else "Unknown",
                "generic_name": "Not specified",
                "uses": ["Please consult a pharmacist or doctor for accurate information"],
                "dosage": "Dosage must be determined by a healthcare professional based on individual needs",
                "side_effects": ["Consult medication leaflet or healthcare provider"],
                "precautions": ["Always read the package insert and follow doctor's instructions"],
                "interactions": ["Many drugs interact with other medications - consult your pharmacist"],
                "storage": "Follow storage instructions on packaging",
                "pregnancy_category": "Consult doctor before use during pregnancy or breastfeeding",
                "availability": "May require prescription - check with healthcare provider",
                "manufacturer": ["Various pharmaceutical companies"],
                "safety_warning": "IMPORTANT: This is general information. Always consult a healthcare professional for medical advice."
            }
            
        return normalize_medicine_result(data)
    except Exception as e:
        print(f"\n[ERROR] Medicine information retrieval failed: {str(e)}")
        return None

def print_medicine_info(result: dict):
    """Display medicine information in a user-friendly format"""
    print("\n" + "="*60)
    print("MEDICINE AI ASSISTANT - MEDICATION INFORMATION")
    print("="*60)
    
    print(f"\n💊 Medicine: {result.get('medicine_name')}")
    if result.get('generic_name') != "Not specified":
        print(f"   Generic: {result.get('generic_name')}")
    
    print(f"\n🏥 Primary Uses:")
    for use in result.get('uses', []):
        print(f"   • {use}")
    
    print(f"\n📋 Dosage Information:")
    print(f"   {result.get('dosage')}")
    
    print(f"\n⚠️  Side Effects:")
    for effect in result.get('side_effects', []):
        print(f"   • {effect}")
    
    print(f"\n🚫 Precautions:")
    for precaution in result.get('precautions', []):
        print(f"   • {precaution}")
    
    print(f"\n🔗 Interactions:")
    for interaction in result.get('interactions', []):
        print(f"   • {interaction}")
    
    print(f"\n🌡️  Storage: {result.get('storage')}")
    print(f"🤰 Pregnancy: {result.get('pregnancy_category')}")
    print(f"🛒 Availability: {result.get('availability')}")
    
    if result.get('manufacturer') and result.get('manufacturer')[0] != "Various manufacturers":
        print(f"\n🏭 Common Manufacturers:")
        for manufacturer in result.get('manufacturer', []):
            print(f"   • {manufacturer}")
    
    print(f"\n{'!'*20} IMPORTANT SAFETY WARNING {'!'*20}")
    print(f"🔴 {result.get('safety_warning')}")
    print(f"{'!'*60}")

# ----------------------------
# MAIN EXECUTION - MEDICINE AI ASSISTANT
# ----------------------------
if __name__ == "__main__":
    print("==== MEDICINE AI ASSISTANT ====")
    print("Your trusted source for medication information")
    print("DISCLAIMER: This is for informational purposes only. Always consult a healthcare professional.\n")
    
    while True:
        question = input("\nWhat medicine would you like to know about? (or type 'quit' to exit): ").strip()
        
        if question.lower() in ['quit', 'exit', 'bye']:
            print("Thank you for using Medicine AI Assistant. Stay healthy!")
            break
        
        if not question:
            print("Please enter a medicine name or question.")
            continue
        
        # context = input("Any additional context? (symptoms, conditions, etc. - press enter if none): ").strip()
        context = question.strip()
        
        print(f"\n🔍 Searching for information about: {question}")
        result = get_medicine_info(question, context)

        if result:
            print_medicine_info(result)
        else:
            print("\n[ERROR] Could not retrieve medicine information. Please try again with a different query.")
        
        print("\n" + "-"*60)


