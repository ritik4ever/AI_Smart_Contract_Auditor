from fastapi import FastAPI, File, UploadFile, HTTPException
import subprocess
import openai
import os

app = FastAPI()

# Load OpenAI API Key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY as an environment variable.")

openai.api_key = OPENAI_API_KEY

def run_slither(contract_path):
    try:
        result = subprocess.run(["slither", contract_path], capture_output=True, text=True, timeout=60)
        return result.stdout if result.returncode == 0 else f"Slither Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Slither analysis timed out."

def analyze_with_ai(report):
    try:
        prompt = f"Analyze the following Solidity audit report and suggest improvements:\n{report}"
        response = openai.ChatCompletion.create(
            model="gpt-4", messages=[{"role": "system", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI Analysis Error: {str(e)}"

@app.post("/analyze/")
async def analyze_contract(file: UploadFile = File(...)):
    contract_path = f"temp/{file.filename}"
    os.makedirs("temp", exist_ok=True)

    with open(contract_path, "wb") as f:
        f.write(await file.read())

    slither_output = run_slither(contract_path)
    ai_analysis = analyze_with_ai(slither_output)

    return {"slither": slither_output, "ai_analysis": ai_analysis}
