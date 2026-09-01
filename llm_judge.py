import os, json
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def judge_company(company_name: str, signals: dict) -> dict:
    prompt = f"""You are an expert B2B sales intelligence analyst.
Company: {company_name}
Signals: {json.dumps(signals, indent=2)}

Evaluate if this company is a good fit for AI automation services.
Output ONLY valid JSON matching this exact schema:
{{
  "fit_call": "Yes" or "No",
  "confidence": <integer 0-100>,
  "reasoning": "<2-3 sentence reasoning based on evidence, NOT a summary>",
  "follow_up_question": "<specific, actionable question>"
}}"""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=500
    )
    return json.loads(response.choices[0].message.content)
