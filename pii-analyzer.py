
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import ollama
import re
import json
import os
import openai
from openai import OpenAI
from dotenv import load_dotenv

def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--page-load-strategy=none")  # Don't wait for full page load
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_page_content(url, driver):
    driver.get(url)
    time.sleep(5)
    return driver.page_source

def analyze_page(url):
    driver = setup_selenium()
    try:
        if not url.startswith('http'):
            url = 'https://' + url

        html = get_page_content(url, driver)
        soup = BeautifulSoup(html, 'html.parser')

        # Pull the scripts
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
        
        # Check for common PII patterns in localStorage/sessionStorage
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

        return analysis_data
    except Exception as e:
        print(f"Error analyzing page: {e}")
        return None
    finally:
        driver.quit()



def analyze_with_openai0(analysis_data):
    # Load environment variables in a file called .env

    load_dotenv(override=True)
    api_key = os.getenv('OPENAI_API_KEY') 
    openai.api_key =api_key
    client = OpenAI()  # Automatically uses your API key from environment variables
    
    prompt = f"""
    You are a privacy and security expert. Analyze this website data collection and identify:
    1. Potential PII collection risks
    2. Trackers and their purposes
    3. Cookie purposes and their expiration
    4. Any evidences of Bots, Drop houses, or mules
    5. Data being stored in localStorage/sessionStorage

    Data: {json.dumps(analysis_data, indent=2)}

    Provide a detailed security assessment with clear categorization of findings.
    """

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",  # or "gpt-4-turbo" for the latest
        messages=[
            {
                "role": "system",
                "content": "You are a highly skilled privacy and security analyst with expertise in web technologies, data collection practices, and threat detection."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5,
        max_tokens=2000
    )

    return response.choices[0].message.content

def analyze_with_openai(analysis_data):
    # Load environment variables in a file called .env
    load_dotenv(override=True)
    api_key = os.getenv('OPENAI_API_KEY') 
    openai.api_key = api_key
    client = OpenAI()  # Automatically uses your API key from environment variables

    prompt = f"""
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

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",  # or "gpt-4-turbo" for the latest
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
        response_format={"type": "json_object"}  # Explicitly request JSON output
    )

    # Parse the response to ensure it's valid JSON
    try:
        json_response = json.loads(response.choices[0].message.content)
        return json_response
    except json.JSONDecodeError:
        # Fallback in case the response isn't valid JSON
        return {
            "error": "Failed to parse response as JSON",
            "raw_response": response.choices[0].message.content
        }

def analyze_with_ollama0(analysis_data):
        prompt = f"""
        You are a privacy and security expert. Analyze this website data collection and identify:
        1. Potential PII collection risks
        2. Trackers and their purposes
        3. Cookie purposes and their expiration
        4. Any evidences of Bots, Drop houses, or mules
        5. Data being stored in localStorage/sessionStorage

        Data: {json.dumps(analysis_data, indent=2)}

        Provide a detailed security assesment.
        """

        response = ollama.chat(model="llama3", messages =[
            {
                'role': 'user',
                'content': prompt,
                'temperature': 0.7,
            }
        ])

        return response['message']['content']


def analyze_with_ollama(analysis_data):
    """
    Analyze website data collection using llama3:8b-instruct-q6_K with optimized settings for 32GB RAM.
    
    Args:
        analysis_data (dict): Website data to analyze (cookies, trackers, storage, etc.)
    
    Returns:
        dict: Analysis results in structured JSON format or error information
    """
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

    try:
        # Optimized model parameters for 32GB systems
        response = ollama.chat(
            model=MODEL_NAME,
            options={
                "num_ctx": 4096,  # Optimal context window
                "temperature": 0.2,  # More deterministic output
                "top_p": 0.9  # Balance between creativity and focus
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
        return {
            **result,
            "_metadata": {
                "model": MODEL_NAME,
                "context_window": 4096,
                "analysis_timestamp": datetime.datetime.now().isoformat()
            }
        }

    except json.JSONDecodeError as e:
        return {
            "error": "JSON parsing failed",
            "cause": str(e),
            "content_sample": content[:200] + "..." if 'content' in locals() else None,
            "remediation": "Try reducing the input data size or simplify the prompt"
        }
    except Exception as e:
        return {
            "error": "Analysis failed",
            "exception_type": type(e).__name__,
            "details": str(e),
            "model_attempted": MODEL_NAME
        }
    
def main():
    url = input("Enter the URL to analyze: ")
    print(f"Analyzing url {url}...")

    #step 1: Collect technical data
    analysis_data = analyze_page(url)
    
    # Step 2: Perform analysis with Llama3
    ai_analysis = analyze_with_ollama(analysis_data)

    # Step 2: Perform analysis with Openai
    # ai_analysis = analyze_with_openai(analysis_data)
    print(ai_analysis)
    # 3: Save the results
    if not analysis_data:
        print("Analysis failed. Could not retrieve page data.")
        return
    with open('analysis_results.json', 'w') as f:
        json.dump(analysis_data, f, indent=2)
    with open('analysis_results.txt', 'w') as f:
        f.write(f"Technical Analysis:\n{json.dumps(analysis_data, indent=2 )}\n\n") 
        f.write(f"AI Security Assesment:\n{json.dumps(ai_analysis, indent=2 )}\n\n") 
        
    print("Analysis complete. Results saved to analysis_results.json and analysis_results.txt.")

if(__name__ == "__main__"):
        main()



