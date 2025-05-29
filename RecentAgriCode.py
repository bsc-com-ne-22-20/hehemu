import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()  # Load GOOGLE_API_KEY from .env

app = Flask(__name__)
os.environ['GOOGLE_API_KEY'] = 'AIzaSyCeij7bg5CCqgAAdgyi2t0gJrMFKRZ8qqg'
class Farmer_AgriGemini:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required")
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

    def generate_recommendations(self, soil_data, weather_data):
        try:
            if 'ph' not in soil_data or 'temperature' not in weather_data:
                return "Error: Missing required 'ph' or 'temperature'."

            prompt = f"""
            You are an expert agronomist. Based on the following input:

            Soil pH: {soil_data.get('ph')}
            Temperature: {weather_data.get('temperature')}°C
            Additional soil data: {soil_data}
            Additional weather data: {weather_data}

            Provide clear recommendations in 6 sentences or fewer:
            1. Suitable crops
            2. Soil improvements
            3. Watering suggestions
            4. Potential pest risks
            """

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }

            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            candidates = response.json().get("candidates", [])
            if not candidates:
                return "No response from Gemini model."
            return candidates[0]["content"]["parts"][0]["text"].strip()

        except requests.exceptions.RequestException as e:
            return f"Gemini API Error: {str(e)}"
        except Exception as e:
            return f"Processing Error: {str(e)}"

# Initialize with Google API Key
try:
    agrigpt = Farmer_AgriGemini(os.environ["GOOGLE_API_KEY"])
except Exception as e:
    print(f"Failed to initialize AgriGemini: {e}")
    exit(1)

@app.route('/')
def home():
    return """
    <h1>AgriGemini API</h1>
    <p>Send POST requests to <code>/recommend</code> with JSON like:</p>
    <pre>
    {
        "soil_data": {"ph": 6.5, "nitrogen": 10},
        "weather_data": {"temperature": 26, "humidity": 50}
    }
    </pre>
    """

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        soil_data = data.get("soil_data", {})
        weather_data = data.get("weather_data", {})

        if not soil_data or not weather_data:
            return jsonify({"error": "Both soil_data and weather_data are required"}), 400

        recommendations = agrigpt.generate_recommendations(soil_data, weather_data)

        return jsonify({
            "status": "success",
            "soil_data": soil_data,
            "weather_data": weather_data,
            "recommendations": recommendations
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8009))
    app.run(host='0.0.0.0', port=port, debug=True)
