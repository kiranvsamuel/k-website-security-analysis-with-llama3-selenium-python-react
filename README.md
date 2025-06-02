# K-Website Security Analysis Tool
- (AI Agent Built with Llama3 (8B) + Selenium to Detect PII, Trackers & Personal Data – Running Locally)
  
A comprehensive web security analysis tool that combines automated scanning with AI-powered analysis to identify privacy and security risks on websites.

## Features

- **Automated Website Scanning**:
  - Detects third-party scripts and trackers
  - Analyzes cookies and storage mechanisms (localStorage, sessionStorage)
  - Examines form fields for potential PII collection
  - Identifies meta tags and their security implications

- **AI-Powered Analysis**:
  - Llama3 local model option for privacy-focused analysis
  - Structured JSON output for easy integration

- **Risk Assessment**:
  - PII (Personally Identifiable Information) detection
  - Tracker classification (Google, Facebook, advertising networks)
  - Bot and malicious activity detection
  - Data exfiltration risk analysis

## Architecture
Frontend (React) → Flask API → Selenium/BeautifulSoup → AI Analysis (OpenAI/Llama3)


## Installation

### Prerequisites

- Python 3.9+
- Node.js 16+
- Chrome browser
- ChromeDriver (matching your Chrome version)
- Ollama (if using local Llama3 model)

### Backend Setup

Clone the repository:
   [git clone https://github.com/yourusername/k-website-security-analysis.git](https://github.com/kiranvsamuel/k-website-security-analysis-with-llama3-selenium-python-react.git)
   cd k-website-security-analysis/backend

Create and activate a virtual environment:
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

Install dependencies


Run the Flask API


## Frontend Setup
1. Navigate to the frontend directory: cd ../frontend 
2. Install dependencies: npm install 
3. Call the API end point REACT_APP_API_URL=http://localhost:5000 
4. Start the development server: npm start 
Usage
1. Access the web interface at http://localhost:3000
2. Enter a URL to analyze (e.g., https://example.com)
3. View the comprehensive security report including:
    * Detected trackers and scripts
    * Cookie analysis
    * PII collection risks
    * Local storage examination
    * AI-generated security assessment
    * 
API Endpoints
* POST /api/analyze {
*   "url": "www.cnn.com"
* } 
* Response: json {
*   "technical_analysis": { ... },
*   "ai_analysis": { ... }
* }
  

## License:
Distributed under the MIT License. 


## Contact:

Kiran Veerabatheni - kiran.veerabatheni@hotmail.com

@AppliedAIwithKiran

https://github.com/kiranvsamuel

https://www.linkedin.com/in/kiranveerabatheni



## Project Link:

https://github.com/kiranvsamuel](https://github.com/kiranvsamuel/k-website-security-analysis-with-llama3-selenium-python-react
