
import os
import sys
from dotenv import load_dotenv

# Load env from .env file
load_dotenv(".env")

try:
    from runtime.crewai.model_config import get_llm_for_agent, LLMClientError
    from crewai import LLM
except ImportError:
    # Add project root to path
    sys.path.append(os.getcwd())
    from runtime.crewai.model_config import get_llm_for_agent, LLMClientError
    from crewai import LLM

def test_chutes_connection():
    print("Testing Chutes AI connection...")
    
    # Check key presence
    key = os.environ.get("CHUTES_API_KEY")
    if not key:
        print("❌ CHUTES_API_KEY is not set in environment or .env file")
        return
    
    print(f"✅ CHUTES_API_KEY found (length: {len(key)})")
    
    try:
        # Try to get the LLM for gap_analyzer (which uses Chutes)
        print("Attempting to initialize LLM for gap_analyzer...")
        llm = get_llm_for_agent("gap_analyzer")
        print(f"✅ LLM initialized: {llm.model}")
        
        # Try a simple completion
        print("Sending test completion request...")
        response = llm.call(messages=[{"role": "user", "content": "Hello, are you DeepSeek?"}])
        print(f"✅ Response received: {response}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chutes_connection()
