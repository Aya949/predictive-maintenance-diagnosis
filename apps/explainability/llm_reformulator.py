"""
Optional layer: reformulates the structured diagnosis into natural,
readable prose using a local LLM (Ollama). Strictly grounded — the LLM
is only allowed to rephrase, never invent new facts.
"""

import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"


def reformulate_diagnosis(diagnosis: dict) -> str:
    """
    diagnosis: the dict returned by DiagnosticEngine.diagnose()
    Returns a natural-language paragraph, or None if the LLM is unavailable
    (caller should fall back to the structured display).
    """
    facts = {
        "predicted_condition": diagnosis["predicted_class"],
        "confidence_percent": round(diagnosis["confidence"] * 100, 1),
        "top_features": [f["feature"] for f in diagnosis["top_features"][:3]],
        "root_causes": [
            {"cause": rc["cause"], "likelihood": rc["likelihood"], "action": rc["recommended_action"]}
            for rc in diagnosis["root_causes"]
        ],
    }

    prompt = f"""
        You are a technical maintenance report writer.

        Your task is to transform the structured engineering diagnosis provided below
        into exactly TWO sections for a professional maintenance report.

        IMPORTANT RULES:
        - The diagnosis has already been determined by the diagnostic system.
        - Do NOT make a new diagnosis.
        - Use ONLY the information provided in the facts.
        - Do NOT invent causes, symptoms, measurements, mechanisms, or recommendations.
        - Do NOT add external engineering knowledge.
        - Do NOT modify confidence or likelihood values.
        - Do NOT exaggerate the severity of the fault.
        - Preserve the meaning of the provided engineering knowledge.
        - Write clearly for a maintenance technician or engineer.
        - Do not mention that an LLM was used.

        SECTION 1 — Diagnostic Summary
        Write ONE concise paragraph explaining:
        - what condition was detected,
        - the model confidence,
        - the main contributing features,
        - and the engineering phenomenon identified by the knowledge base.

        SECTION 2 — Engineering Details
        Write ONE more detailed paragraph explaining:
        - what the important features indicate according to the provided knowledge,
        - how the observed pattern relates to the identified engineering phenomenon,
        - the most probable root causes and their likelihood,
        - and the recommended inspection or maintenance actions.

        OUTPUT FORMAT:

        Diagnostic Summary
        [one paragraph]

        Engineering Details
        [one paragraph]

        FACTS PROVIDED BY THE DIAGNOSTIC SYSTEM:
        {json.dumps(facts, indent=2)}

        Generate the two sections now.
        """

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=60
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        print(f"LLM reformulation unavailable: {e}")
        return None
    
def generate_full_report_narrative(diagnosis: dict) -> str:
    """
    Longer, more detailed narrative specifically for the PDF report.
    Still strictly grounded — no invented facts.
    """
    facts = {
        "predicted_condition": diagnosis["predicted_class"],
        "confidence_percent": round(diagnosis["confidence"] * 100, 1),
        "top_features": diagnosis["top_features"][:5],
        "root_causes": diagnosis["root_causes"],
    }

    prompt = f"""You are writing a detailed maintenance diagnostic report section for an engineer.

STRICT RULES:
- Use ONLY the facts provided below. Do not invent any new cause, symptom, or number.
- Do not change any likelihood, urgency, or recommended action stated in the facts.
- Write in a professional, technical tone, in full paragraphs (not bullet points).
- Cover: (1) what was detected and why, referencing the key contributing sensor features,
  (2) for each root cause, explain the physical mechanism and typical symptoms,
  (3) close with an overall recommendation summarizing priority actions.
- Aim for 2-3 well-developed paragraphs, not a short summary.

FACTS:
{json.dumps(facts, indent=2)}

Detailed report:"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=180
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        print(f"LLM full report unavailable: {e}")
        return None
    