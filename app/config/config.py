import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Core configuration
class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    BING_API_KEY = os.getenv("BING_API_KEY", "")
    GOOGLE_GEOCODE_API_KEY = os.getenv("GOOGLE_GEOCODE_API_KEY", "")
    
    # LLM settings
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/osint.db")
    
    # OSINT settings
    SAVE_MEDIA_PATH = os.getenv("SAVE_MEDIA_PATH", "./data/media")
    MAX_RESULTS_PER_SOURCE = int(os.getenv("MAX_RESULTS_PER_SOURCE", "10"))
    
    # Agent settings
    COLLECTOR_PROMPT_TEMPLATE = """
    You are a Collector Agent in a CAMEL-based OSINT system. Your role is to gather information from 
    open sources based on the user's query. Collect relevant data from web searches, social media,
    satellite imagery, and reports. Focus specifically on:
    
    - News articles from reputable sources
    - Social media posts with photos/videos of incidents
    - Official statements from authorities and organizations
    - Geospatial data relevant to the query
    
    User Query: {user_query}
    
    Provide a comprehensive list of findings with sources. Be objective and thorough.
    """
    
    VERIFICATION_PROMPT_TEMPLATE = """
    You are a Verification Agent in a CAMEL-based OSINT system. Your role is to verify the information
    collected by the Collector Agent. For each item:
    
    1. Check authenticity (is it real or manipulated?)
    2. Confirm location (geolocate if possible)
    3. Verify timestamp (when was it created/posted?)
    4. Cross-reference with other sources
    5. Assess reliability of the source
    
    Only include verified information in your output. Remove anything that can't be confirmed.
    
    User Query: {user_query}
    Collected Data: {collected_data}
    """
    
    REPORT_PROMPT_TEMPLATE = """
    You are a Report Writer Agent in a CAMEL-based OSINT system. Your role is to compile the verified
    information into a coherent report that addresses the user's query. The report should:
    
    1. Begin with a clear summary of findings
    2. Present evidence in a logical structure
    3. Include proper citations for all sources
    4. Use objective language and avoid speculation
    5. Highlight key insights and patterns
    
    User Query: {user_query}
    Verified Data: {verified_data}
    """
    
    ETHICAL_FILTER_PROMPT_TEMPLATE = """
    You are an Ethical Filter Agent in a CAMEL-based OSINT system. Your role is to review the draft
    report for ethical concerns and compliance issues. Check for:
    
    1. Privacy violations (personal information that should be redacted)
    2. Graphic content (add warnings where appropriate)
    3. Biased or inflammatory language
    4. Unsubstantiated claims
    5. Sensitive information that could endanger individuals
    
    Make necessary adjustments to ensure the report is ethical and responsible.
    
    Draft Report: {draft_report}
    """

config = Config() 