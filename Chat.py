import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

class Farmer_AgriGpt:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required in .env file")
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def generate_recommendations(self, soil_data, weather_data):
        """
        Generates agricultural recommendations using OpenAI's API.
        
        Args:
            soil_data (dict): Must contain at least 'ph' key
            weather_data (dict): Must contain at least 'temperature' key
            
        Returns:
            str: AI-generated recommendations or error message
        """
        try:
            # Validate input data
            if not isinstance(soil_data, dict) or not isinstance(weather_data, dict):
                return "Error: soil_data and weather_data must be dictionaries"
                
            if 'ph' not in soil_data or 'temperature' not in weather_data:
                return "Error: soil_data requires 'ph' and weather_data requires 'temperature'"

            # Construct the AI prompt
            prompt = f"""
            **Agricultural Recommendation Request**
            Soil pH: {soil_data.get('ph')}
            Temperature: {weather_data.get('temperature')}°C
            Additional soil data: {soil_data}
            Additional weather data: {weather_data}

            Provide specific recommendations for:
            1. Suitable crops
            2. Soil amendments
            3. Irrigation advice
            4. Potential pest risks
            """

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert agronomist. Provide concise, practical farming advice."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }

            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()  # Raises HTTPError for bad responses
            
            return response.json()["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.RequestException as e:
            return f"API Error: {str(e)}"
        except Exception as e:
            return f"Processing Error: {str(e)}"

# Initialize with API key
try:
    agrigpt = Farmer_AgriGpt(os.environ["OPENAI_API_KEY"])
except Exception as e:
    print(f"Failed to initialize AgriGPT: {e}")
    exit(1)

@app.route('/')
def home():
    """Root endpoint with usage instructions"""
    return """
    <h1>AgriGPT API</h1>
    <p>Send POST requests to /recommend with JSON:</p>
    <pre>
    {
        "soil_data": {"ph": 6.5, ...},
        "weather_data": {"temperature": 25, ...}
    }
    </pre>
    """

@app.route('/recommend', methods=['POST'])
def recommend():
    """
    Main recommendation endpoint
    Example request:
    {
        "soil_data": {"ph": 6.2, "nitrogen": 20},
        "weather_data": {"temperature": 22, "humidity": 60}
    }
    """
    try:
        data = request.get_json()
        
        # Input validation
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        soil_data = data.get('soil_data', {})
        weather_data = data.get('weather_data', {})
        
        if not soil_data or not weather_data:
            return jsonify({"error": "Both soil_data and weather_data are required"}), 400
            
        # Get AI recommendations
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