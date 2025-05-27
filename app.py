import os
import json
import re
import time
import datetime
from flask import Flask, request
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

import ollama 

import openai
from openai import OpenAI





app = Flask(__name__)


# swagger ui template
custom_swagger_ui_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>%(title)s</title>
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css">
  <style>
    /* Your CSS styles here */
    .topbar {
      background-color: #003366;
      padding: 15px 0;
    }
    .topbar-wrapper img {
      content: url('https://smartbear.com/wp-content/themes/smartbear/images/logo-sb-white.svg');
      height: 40px;
    }
    /* Add all other styles from the previous example */
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function() {
      const ui = SwaggerUIBundle({
        url: "%(spec_url)s",
        dom_id: '#swagger-ui',
        deepLinking: True,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        plugins: [
          SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout"
      });
      window.ui = ui;
    };
  </script>
</body>
</html>
"""


CORS(app)  # Enable CORS for all routes

# Configure Swagger UI with OAS3 and custom branding
app.config['SWAGGER_UI_CONFIG'] = {
    'deepLinking': True,
    'persistAuthorization': True,
    'displayOperationId': True,
    'filter': True,
    'docExpansion': 'none',
    'tagsSorter': 'alpha',
    'operationsSorter': 'alpha',
    'validatorUrl': None,
    'supportedSubmitMethods': ['get', 'post', 'put', 'delete', 'patch'],
    'showCommonExtensions': True,
    'showExtensions': True,
    'showMutatedRequest': True,
    'defaultModelsExpandDepth': 1,
    'defaultModelExpandDepth': 1,
    'defaultModelRendering': 'example',
    'displayRequestDuration': True,
    'tryItOutEnabled': True
}

# Initialize API with custom Swagger UI template
api = Api(
    app,
    version='1.0.0',
    title='Website Security Analysis API',
    description='A comprehensive API for analyzing website security and privacy concerns with OAS3 support',
    doc='/docs/',
    contact='SmartBear Support',
    contact_url='https://support.smartbear.com',
    license='Apache 2.0',
    license_url='https://www.apache.org/licenses/LICENSE-2.0.html',
    authorizations={
        'Bearer Auth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Type in the *Value* input box: Bearer {your JWT token}'
        }
    }
)

# Namespace for the API
ns = api.namespace('api/v1', description='Website analysis operations')

# Request models
analyze_page_model = api.model('AnalyzePageRequest', {
    'url': fields.String(required=True, description='Website URL to analyze', example='https://example.com')
})

analysis_data_model = api.model('AnalysisDataRequest', {
    'analysis_data': fields.Raw(required=True, description='Analysis data from analyze_page endpoint')
})

# Response models
analysis_response_model = api.model('AnalysisResponse', {
    'url': fields.String(description='Analyzed URL'),
    'scripts': fields.List(fields.String, description='List of external script URLs'),
    'cookies': fields.List(fields.Raw, description='List of cookies with their properties'),
    'local_storage': fields.Raw(description='Contents of localStorage'),
    'session_storage': fields.Raw(description='Contents of sessionStorage'),
    'meta_data': fields.Raw(description='Metadata extracted from meta tags'),
    'trackers': fields.List(fields.Raw, description='Detected tracking scripts'),
    'pii_risks': fields.List(fields.Raw, description='Potential PII collection risks')
})

ai_analysis_response_model = api.model('AIAnalysisResponse', {
    'PII': fields.Nested(api.model('PIIAnalysis', {
        'risk_count': fields.Integer,
        'risk_items': fields.List(fields.Raw),
        'analysis': fields.String,
        'summary': fields.List(fields.Raw),
        'compliance_violations': fields.List(fields.String)
    })),
    'TRACKERS': fields.Nested(api.model('TrackerAnalysis', {
        'risk_count': fields.Integer,
        'domains': fields.List(fields.String),
        'vendor_analysis': fields.Raw
    })),
    'COOKIES': fields.Nested(api.model('CookieAnalysis', {
        'risk_count': fields.Integer,
        'issues_by_type': fields.Raw,
        'high_risk_cookies': fields.List(fields.Raw)
    })),
    'BOTS': fields.Nested(api.model('BotAnalysis', {
        'detected': fields.Boolean,
        'confidence': fields.String,
        'indicators': fields.List(fields.String)
    })),
    'DATA_EXFILTRATION': fields.Nested(api.model('DataExfiltrationAnalysis', {
        'mules_detected': fields.Boolean,
        'drop_houses_detected': fields.Boolean,
        'suspicious_endpoints': fields.List(fields.String)
    })),
    'LOCAL_CACHE': fields.Nested(api.model('LocalCacheAnalysis', {
        'risk_count': fields.Integer,
        'sensitive_data_found': fields.Boolean,
        'items': fields.List(fields.String)
    })),
    'OVERALL_SECURITY_ASSESSMENT': fields.Nested(api.model('OverallAssessment', {
        'risk_score': fields.Integer,
        'critical_issues': fields.List(fields.String),
        'recommended_actions': fields.List(fields.String)
    })),
    '_metadata': fields.Nested(api.model('Metadata', {
        'model': fields.String,
        'context_window': fields.Integer,
        'analysis_timestamp': fields.DateTime
    }))
})

error_model = api.model('ErrorResponse', {
    'error': fields.String(description='Error type'),
    'message': fields.String(description='Detailed error message'),
    'code': fields.Integer(description='HTTP status code'),
    'timestamp': fields.DateTime(description='When the error occurred')
})

# Helper function to create error response
def create_error_response(error, message, code):
    return {
        'error': error,
        'message': message,
        'code': code,
        'timestamp': datetime.datetime.now().isoformat()
    }, code


def setup_selenium():
    """Configure and return a Selenium WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--page-load-strategy=none")
    
    # Use webdriver-manager to handle ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver



@ns.route('/analyze_page')
class AnalyzePage(Resource):
    @ns.doc('analyze_website_page')
    @ns.expect(analyze_page_model, validate=True)
    @ns.response(200, 'Success', analysis_response_model)
    @ns.response(400, 'Bad Request', error_model)
    @ns.response(500, 'Internal Server Error', error_model)
    @ns.produces(['application/json'])
    def post(self):
        """Analyze a webpage and return technical data"""
        data = request.json
        url = data.get('url')
        
        if not url:
            return create_error_response('ValidationError', 'URL is required', 400)
        
        driver = setup_selenium()
        try:
            if not url.startswith('http'):
                url = 'https://' + url

            html = get_page_content(url, driver)
            soup = BeautifulSoup(html, 'html.parser')

            # Extract scripts
            scripts = [script.get('src') for script in soup.find_all('script') if script.get('src')]

            # Extract cookies and storage
            cookies = driver.get_cookies()
            
            try:
                local_storage = driver.execute_script("return Object.fromEntries(Object.entries(window.localStorage));")
            except:
                local_storage = "Could not access localStorage"
                
            try:
                session_storage = driver.execute_script("return Object.fromEntries(Object.entries(window.sessionStorage));")
            except:
                session_storage = "Could not access sessionStorage"

            # Extract meta tags
            meta_tags = soup.find_all('meta')
            meta_data = {meta.get('name'): meta.get('content') for meta in meta_tags if meta.get('name')}

            # Detect common trackers
            common_trackers = {
                'google': ['google-analytics.com', 'googletagmanager.com', 'googleadservices.com'],
                'facebook': ['facebook.net', 'fb.com', 'facebook.com'],
                'twitter': ['twitter.com', 'twimg.com'],
                'linkedin': ['linkedin.com'],
                'advertising': ['doubleclick.net', 'adsrvr.org', 'adnxs.com']
            }

            detected_trackers = []
            for script in scripts:
                for tracker_type, domains in common_trackers.items():
                    if any(domain in script for domain in domains):
                        detected_trackers.append({
                            'type': tracker_type,
                            'source': script,
                            'risk': 'medium' if tracker_type == 'advertising' else 'low'
                        })

            # Detect potential PII risks
            pii_risks = []
            pii_keywords = ['user', 'email', 'name', 'address', 'phone', 'credit', 'ssn', 'password']
            
            if isinstance(local_storage, dict):
                for key, value in local_storage.items():
                    if any(keyword in key.lower() for keyword in pii_keywords):
                        pii_risks.append({
                            'location': 'localStorage',
                            'key': key,
                            'value_sample': str(value)[:50] + '...' if value else None,
                            'risk': 'high'
                        })

            if isinstance(session_storage, dict):
                for key, value in session_storage.items():
                    if any(keyword in key.lower() for keyword in pii_keywords):
                        pii_risks.append({
                            'location': 'sessionStorage',
                            'key': key,
                            'value_sample': str(value)[:50] + '...' if value else None,
                            'risk': 'high'
                        })

            # Check form fields for PII collection
            forms = soup.find_all('form')
            for form in forms:
                inputs = form.find_all('input')
                for input_tag in inputs:
                    input_type = input_tag.get('type', '').lower()
                    input_name = input_tag.get('name', '').lower()
                    if (input_type in ['email', 'password', 'tel', 'text'] and 
                        any(keyword in input_name for keyword in pii_keywords)):
                        pii_risks.append({
                            'location': 'form_input',
                            'form_action': form.get('action', ''),
                            'input_name': input_tag.get('name'),
                            'input_type': input_type,
                            'risk': 'high'
                        })

            # Prepare Analysis Data
            analysis_data = {
                'url': url,
                'scripts': scripts,
                'cookies': cookies,
                'local_storage': local_storage,
                'session_storage': session_storage,
                'meta_data': meta_data,
                'trackers': detected_trackers,
                'pii_risks': pii_risks
            }

            return analysis_data, 200
          # Pass the analysis_data to analyze_with_ollama endpoint
            with app.test_request_context(
                '/api/v1/analyze_with_ollama',
                method='POST',
                json={'analysis_data': analysis_data}
            ):
                try:
                    response = AnalyzeWithOllama().post()
                    print(response)
                    if isinstance(response, tuple) and len(response) == 2:
                        return response  # Return the (data, status_code) tuple directly
                    else:
                        return response
                except Exception as e:
                    return create_error_response('AnalyzeWithOllamaError', str(e), 500)

        except Exception as e:
            return create_error_response('AnalysisError', str(e), 500)
        finally:
            driver.quit()

@ns.route('/analyze_with_ollama')
class AnalyzeWithOllama(Resource):
    @ns.doc('analyze_with_ollama')
    @ns.expect(analysis_data_model, validate=True)
    @ns.response(200, 'Success', ai_analysis_response_model)
    @ns.response(400, 'Bad Request', error_model)
    @ns.response(500, 'Internal Server Error', error_model)
    @ns.produces(['application/json'])
    def post(self):
        """Analyze website data using Ollama (Llama3)"""
        data = request.json
        analysis_data = data.get('analysis_data')
        
        if not analysis_data:
            return create_error_response('ValidationError', 'analysis_data is required', 400)
        
        try:
            MODEL_NAME = "llama3:8b-instruct-q6_K"
            PROMPT_TEMPLATE = """
            [SYSTEM INSTRUCTIONS]
            You are a senior privacy/security analyst. Perform a technical audit of this website data.
            Respond ONLY with valid JSON matching the exact structure below.
            Never include markdown, comments, or explanatory text.

            [ANALYSIS FOCUS AREAS]
            1. PII collection risks (prioritize email, phone, location, identifiers)
            2. Tracker analysis (vendor, purpose, data flows)
            3. Cookie compliance (expiration, security flags, consent requirements)
            4. Malicious activity indicators (bots, data mules, drop houses)
            5. Local/session storage risks

            [INPUT DATA]
            {analysis_data}

            [REQUIRED RESPONSE FORMAT]
            {{
              "PII": {{
                "risk_count": <int>,
                "risk_items": [
                  {{
                    "field": <str>,
                    "type": <str>,
                    "risk_level": "low/medium/high",
                    "evidence": <str>
                  }}
                ],
                "compliance_violations": ["GDPR", "CCPA", ...]
              }},
              "TRACKERS": {{
                "risk_count": <int>,
                "domains": [<str>, ...],
                "vendor_analysis": {{
                  "<domain>": {{
                    "purpose": <str>,
                    "data_collected": [<str>, ...],
                    "reputation": "known-good/neutral/high-risk"
                  }}
                }}
              }},
              "COOKIES": {{
                "risk_count": <int>,
                "issues_by_type": {{
                  "expiration": <int>,
                  "security_flags": <int>,
                  "consent_issues": <int>
                }},
                "high_risk_cookies": [
                  {{
                    "name": <str>,
                    "issues": [<str>, ...],
                    "expiration_days": <int>
                  }}
                ]
              }},
              "BOTS": {{
                "detected": <bool>,
                "confidence": "low/medium/high",
                "indicators": [<str>, ...]
              }},
              "DATA_EXFILTRATION": {{
                "mules_detected": <bool>,
                "drop_houses_detected": <bool>,
                "suspicious_endpoints": [<str>, ...]
              }},
              "LOCAL_CACHE": {{
                "risk_count": <int>,
                "sensitive_data_found": <bool>,
                "items": [<str>, ...]
              }},
              "OVERALL_SECURITY_ASSESSMENT": {{
                "risk_score": 0-100,
                "critical_issues": [<str>, ...],
                "recommended_actions": [<str>, ...]
              }}
            }}
            """.format(analysis_data=json.dumps(analysis_data, indent=2))

            response = ollama.chat(
                model=MODEL_NAME,
                # options={
                #     "num_ctx": 4096,
                #     "temperature": 0.2,
                #     "top_p": 0.9
                # },
                 options={
                    "num_ctx": 4096,
                    "num_thread": 16,   
                    "num_gqa": 2,      
                    "num_gpu": 0,     
                    "main_gpu": 0,
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "num_batch": 14    
                },
                messages=[{
                    "role": "system",
                    "content": "You are a privacy compliance auditor. Respond ONLY with valid JSON."
                }, {
                    "role": "user",
                    "content": PROMPT_TEMPLATE
                }]
            )

            content = response['message']['content']
            
            # Enhanced JSON extraction that handles more edge cases
            json_str = content.strip()
            for pattern in [r"```(?:json)?\s*(\{.*\})\s*```", r"```\s*(\{.*\})\s*```"]:
                match = re.search(pattern, json_str, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    break

            # Validate and parse JSON
            result = json.loads(json_str)
            
            # Add model metadata to response
            result["_metadata"] = {
                "model": MODEL_NAME,
                "context_window": 4096,
                "analysis_timestamp": datetime.datetime.now().isoformat()
            }

            return result, 200

        except json.JSONDecodeError as e:
            return create_error_response(
                'ParsingError',
                f'Failed to parse Ollama response: {str(e)}',
                500
            )
        except Exception as e:
            return create_error_response('AnalysisError', str(e), 500)




@ns.route('/analyze_with_openai')
class AnalyzeWithOpenAI(Resource):
    @ns.doc('analyze_with_openai')
    @ns.expect(analysis_data_model, validate=True)
    @ns.response(200, 'Success', ai_analysis_response_model)
    @ns.response(400, 'Bad Request', error_model)
    @ns.response(500, 'Internal Server Error', error_model)
    @ns.produces(['application/json'])
    def post(self):
        """Analyze website data using OpenAI"""
        data = request.json
        analysis_data = data.get('analysis_data')
        
        if not analysis_data:
            return create_error_response('ValidationError', 'analysis_data is required', 400)
        
        try:
            load_dotenv(override=True)
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return create_error_response('ConfigurationError', 'OPENAI_API_KEY not found in environment', 500)
                
            openai.api_key = api_key
            client = OpenAI()

            prompt1 = f"""
            You are a privacy and security expert. Analyze this website data collection and identify:
            1. Potential PII collection risks
            2. Trackers and their purposes
            3. Cookie purposes and their expiration
            4. Any evidences of Bots, Drop houses, or mules
            5. Data being stored in localStorage/sessionStorage

            Data: {json.dumps(analysis_data, indent=2)}

            Format your response as a JSON object with the following structure:
            {{
              "PII": {{
                "risk_count": <number of PII risks>,
                "risk_items": [
                  {{
                    "type": "<type of risk>",
                    "key": "<name/identifier>",
                    "risk": "<risk level: low, medium, high>"
                  }}
                ],
                "analysis": "<brief overview of PII risks>",
                "summary": [
                  {{
                    "item": "<category name>",
                    "item_risk": "<risk level>",
                    "item_analysis": "<brief description>",
                    "item_count": <number of items>,
                    "item_names": ["<item1>", "<item2>", ...]
                  }}
                ]
              }},
              "TRACKERS": {{
                "risk_count": <number of trackers>,
                "risk_items": [
                  {{
                    "type": "<type of tracker>",
                    "key": "<name/identifier>",
                    "risk": "<risk level: low, medium, high>"
                  }}
                ],
                "analysis": "<brief overview of trackers>",
                "summary": [
                  {{
                    "item": "<category name>",
                    "item_risk": "<risk level>",
                    "item_analysis": "<brief description>",
                    "item_count": <number of items>,
                    "item_names": ["<item1>", "<item2>", ...]
                  }}
                ]
              }},
              "COOKIES": {{
                "risk_count": <number of cookie risks>,
                "risk_items": [
                  {{
                    "type": "<type of cookie>",
                    "key": "<name/identifier>",
                    "risk": "<risk level: low, medium, high>"
                  }}
                ],
                "analysis": "<brief overview of cookies>",
                "summary": [
                  {{
                    "item": "<category name>",
                    "item_risk": "<risk level>",
                    "item_analysis": "<brief description>",
                    "item_count": <number of items>,
                    "item_names": ["<item1>", "<item2>", ...]
                  }}
                ]
              }},
              "BOTS": {{
                "risk_count": <number of bot risks>,
                "risk_items": [
                {{
                    "type": "<type of bot>",
                    "key": "<name/identifier>",
                    "risk": "<risk level: low, medium, high>"
                  }}
                ],
                "analysis": "<brief overview of bot findings>",
                "summary": [
                {{
                    "item": "<category name>",
                    "item_risk": "<risk level>",
                    "item_analysis": "<brief description>",
                    "item_count": <number of items>,
                    "item_names": ["<item1>", "<item2>", ...]
                  }}
                ]
              }},
              "MULES": {{
                "risk_count": <number of mule risks>,
                "risk_items": [
                {{
                    "type": "<type of bot>",
                    "key": "<name/identifier>",
                    "risk": "<risk level: low, medium, high>"
                  }}
                ],
                "analysis": "<brief overview of mule findings>",
                "summary": [
                {{
                    "item": "<category name>",
                    "item_risk": "<risk level>",
                    "item_analysis": "<brief description>",
                    "item_count": <number of items>,
                    "item_names": ["<item1>", "<item2>", ...]
                  }}
                ]
              }},
              "DROP_HOUSES": {{
                "risk_count": <number of drop house risks>,
                "risk_items": [
                 {{
                    "type": "<type of bot>",
                    "key": "<name/identifier>",
                    "risk": "<risk level: low, medium, high>"
                  }}
                ],
                "analysis": "<brief overview of drop house findings>",
                "summary": [
                {{
                    "item": "<category name>",
                    "item_risk": "<risk level>",
                    "item_analysis": "<brief description>",
                    "item_count": <number of items>,
                    "item_names": ["<item1>", "<item2>", ...]
                  }}
                ]
              }},
              "LOCAL_CACHE": {{
                "risk_count": <number of local cache risks>,
                "risk_items": [
                  {{
                    "type": "<type of storage>",
                    "key": "<name/identifier>",
                    "risk": "<risk level: low, medium, high>"
                  }}
                ],
                "analysis": "<brief overview of local cache findings>",
                "summary": [
                  {{
                    "item": "<category name>",
                    "item_risk": "<risk level>",
                    "item_analysis": "<brief description>",
                    "item_count": <number of items>,
                    "item_names": ["<item1>", "<item2>", ...]
                  }}
                ]
              }},
              "OVERALL_SECURITY_ASSESSMENT": "<overall security assessment text>"
            }}

            Ensure the response is properly formatted as valid JSON with no syntax errors.
            """
            prompt = """
            [SYSTEM INSTRUCTIONS]
            You are a senior privacy/security analyst. Perform a technical audit of this website data.
            Respond ONLY with valid JSON matching the exact structure below.
            Never include markdown, comments, or explanatory text.

            [ANALYSIS FOCUS AREAS]
            1. PII collection risks (prioritize email, phone, location, identifiers)
            2. Tracker analysis (vendor, purpose, data flows)
            3. Cookie compliance (expiration, security flags, consent requirements)
            4. Malicious activity indicators (bots, data mules, drop houses)
            5. Local/session storage risks

            [INPUT DATA]
            {analysis_data}

            [REQUIRED RESPONSE FORMAT]
            {{
              "PII": {{
                "risk_count": <int>,
                "risk_items": [
                  {{
                    "field": <str>,
                    "type": <str>,
                    "risk_level": "low/medium/high",
                    "evidence": <str>
                  }}
                ],
                "compliance_violations": ["GDPR", "CCPA", ...]
              }},
              "TRACKERS": {{
                "risk_count": <int>,
                "domains": [<str>, ...],
                "vendor_analysis": {{
                  "<domain>": {{
                    "purpose": <str>,
                    "data_collected": [<str>, ...],
                    "reputation": "known-good/neutral/high-risk"
                  }}
                }}
              }},
              "COOKIES": {{
                "risk_count": <int>,
                "issues_by_type": {{
                  "expiration": <int>,
                  "security_flags": <int>,
                  "consent_issues": <int>
                }},
                "high_risk_cookies": [
                  {{
                    "name": <str>,
                    "issues": [<str>, ...],
                    "expiration_days": <int>
                  }}
                ]
              }},
              "BOTS": {{
                "detected": <bool>,
                "confidence": "low/medium/high",
                "indicators": [<str>, ...]
              }},
              "DATA_EXFILTRATION": {{
                "mules_detected": <bool>,
                "drop_houses_detected": <bool>,
                "suspicious_endpoints": [<str>, ...]
              }},
              "LOCAL_CACHE": {{
                "risk_count": <int>,
                "sensitive_data_found": <bool>,
                "items": [<str>, ...]
              }},
              "OVERALL_SECURITY_ASSESSMENT": {{
                "risk_score": 0-100,
                "critical_issues": [<str>, ...],
                "recommended_actions": [<str>, ...]
              }}
            }}
            """.format(analysis_data=json.dumps(analysis_data, indent=2))


            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a highly skilled privacy and security analyst with expertise in web technologies, data collection practices, and threat detection. You always return responses in valid JSON format when requested."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            try:
                json_response = json.loads(response.choices[0].message.content)
                return json_response, 200
            except json.JSONDecodeError:
                return create_error_response(
                    'ParsingError',
                    'Failed to parse OpenAI response as JSON',
                    500
                )
        except Exception as e:
            return create_error_response('AnalysisError', str(e), 500)




def get_page_content(url, driver):
    """Fetch page content using Selenium."""
    driver.get(url)
    time.sleep(5)  # Allow time for JavaScript execution
    return driver.page_source

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)