import streamlit as st
import time
import os
from grammar_checker import GrammarChecker
from diff_match_patch import diff_match_patch

# Load local .env file manually if it exists to load pre-configured API keys
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                parts = line.strip().split("=", 1)
                if len(parts) == 2:
                    os.environ[parts[0].strip()] = parts[1].strip()

# Page Configuration
st.set_page_config(
    page_title="Academic AI Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Backend Engine
@st.cache_resource
def load_engine():
    return GrammarChecker()

engine = load_engine()

# Inject Premium Custom CSS Styles
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        background: linear-gradient(135deg, #6366F1 0%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Main container styling */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    
    /* Elegant Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1E293B !important;
        border-right: 1px solid #334155;
    }
    
    /* Custom cards with Glassmorphism */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* Metrics section */
    .metric-box {
        text-align: center;
        padding: 15px;
        background: rgba(99, 102, 241, 0.1);
        border-radius: 12px;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #818CF8;
    }
    .metric-label {
        font-size: 12px;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Color coding for Diff text */
    ins {
        background-color: rgba(16, 185, 129, 0.2);
        color: #34D399;
        text-decoration: none;
        padding: 2px 4px;
        border-radius: 4px;
        font-weight: bold;
    }
    del {
        background-color: rgba(239, 68, 68, 0.2);
        color: #F87171;
        text-decoration: line-through;
        padding: 2px 4px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to render a premium card
def card_wrapper(content_html: str):
    st.markdown(f'<div class="glass-card">{content_html}</div>', unsafe_allow_html=True)

# App Title & Subtitle
st.markdown("<h1>🎓 Academic AI Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8; font-size: 1.1rem; margin-top: -10px;'>A smart, free-of-cost grammar & writing advisor utilizing local Hugging Face Transformers and advanced AI APIs.</p>", unsafe_allow_html=True)
st.write("---")

# SIDEBAR OPTIONS
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1546410531-bb4caa6b424d?auto=format&fit=crop&q=80&w=300", use_container_width=True)
    st.markdown("### ⚙️ Control Dashboard")
    
    backend_mode = st.radio(
        "Correction Engine Backend",
        [
            "🌐 Google Gemini LLM API (Fast Online & Detailed Insights) [Recommended]",
            "☁️ Hugging Face Cloud API (Fast Online T5)",
            "🚀 Local NLP Transformer (Offline - Slow first run)"
        ],
        index=0,
        help="Select the AI brain. Gemini LLM runs online and offers rich detailed grammar logs. Hugging Face Cloud runs the T5 model online without heavy CPU usage. Local runs fully offline."
    )
    
    api_key = ""
    hf_token = ""
    
    # Pre-populate keys from environment variables if present
    env_gemini_key = os.environ.get("GEMINI_API_KEY", "")
    env_hf_token = os.environ.get("HF_TOKEN", "")
    
    if "Gemini" in backend_mode:
        st.markdown("#### 🔑 Get Gemini API Key")
        api_key = st.text_input(
            "Enter Gemini API Key", 
            value=env_gemini_key,
            type="password", 
            help="Get a free key from Google AI Studio."
        )
        st.markdown("[Get Free Gemini API Key ↗](https://aistudio.google.com/)")
    elif "Hugging Face Cloud" in backend_mode:
        st.markdown("#### 🔑 Optional HF Token")
        hf_token = st.text_input(
            "Enter Hugging Face Token (Optional)", 
            value=env_hf_token,
            type="password", 
            help="Enter a free Hugging Face access token to bypass rate limits."
        )
        st.markdown("[Get Free HF Token ↗](https://huggingface.co/settings/tokens)")
        
    st.write("---")
    st.markdown("#### ℹ️ Project Context")
    st.caption("This project demonstrates modern Large Language Models (LLMs) and NLP pipelines as a Student Assistant deliverable.")

# MAIN INTERFACE
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("### 📝 Enter Academic Text")
    
    # Text Input & File Upload
    uploaded_file = st.file_uploader("Upload an essay or document (.txt)", type=["txt"])
    
    default_text = "I has went to the university yesterday to met my professors. They is very friendly and helps me with mine project assignment. I hopes i receives high grades."
    
    if uploaded_file is not None:
        try:
            default_text = uploaded_file.read().decode("utf-8")
            st.success("File uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            
    input_text = st.text_area(
        "Paste your text here to analyze:",
        value=default_text,
        height=280
    )
    
    analyze_btn = st.button("🔍 Check Grammar & Style", use_container_width=True, type="primary")

with col_right:
    st.markdown("### ✨ Results & Analysis")
    
    if analyze_btn:
        if not input_text.strip():
            st.warning("Please enter some text to check.")
        else:
            with st.spinner("Analyzing text with AI..."):
                start_time = time.time()
                
                # Run the selected engine
                if "Gemini" in backend_mode:
                    if not api_key:
                        st.error("Please provide a Gemini API Key in the sidebar to run this model.")
                        result = None
                    else:
                        result = engine.check_gemini(input_text, api_key)
                elif "Hugging Face Cloud" in backend_mode:
                    result = engine.check_huggingface_api(input_text, hf_token if hf_token else None)
                else:
                    result = engine.check_local(input_text)
                
                duration = time.time() - start_time
                
                if result and result.get("success"):
                    # Extract outputs
                    corrected_text = result["corrected_text"]
                    
                    # Highlight diffs
                    dmp = diff_match_patch()
                    diffs = dmp.diff_main(input_text, corrected_text)
                    dmp.diff_cleanupSemantic(diffs)
                    
                    html_diff = ""
                    for op, data in diffs:
                        if op == 1: # Insert
                            html_diff += f"<ins>{data}</ins>"
                        elif op == -1: # Delete
                            html_diff += f"<del>{data}</del>"
                        else:
                            html_diff += data
                    
                    # Metric calculations
                    original_words = len(input_text.split())
                    corrected_words = len(corrected_text.split())
                    error_count = sum(1 for op, _ in diffs if op != 0) // 2
                    
                    # Display Stats Row
                    stat_col1, stat_col2, stat_col3 = st.columns(3)
                    with stat_col1:
                        st.markdown(f'<div class="metric-box"><div class="metric-value">{error_count}</div><div class="metric-label">Mistakes Found</div></div>', unsafe_allow_html=True)
                    with stat_col2:
                        st.markdown(f'<div class="metric-box"><div class="metric-value">{corrected_words}</div><div class="metric-label">Words Counted</div></div>', unsafe_allow_html=True)
                    with stat_col3:
                        st.markdown(f'<div class="metric-box"><div class="metric-value">{duration:.2f}s</div><div class="metric-label">Latency Speed</div></div>', unsafe_allow_html=True)
                    
                    st.write("")
                    
                    # Display Side-by-Side tabs
                    tab1, tab2, tab3 = st.tabs(["📝 Highlighted Changes", "✅ Polished Text", "📋 Detailed Explanations"])
                    
                    with tab1:
                        st.markdown(
                            f'<div style="background-color: #1E293B; border-radius: 12px; padding: 20px; line-height: 1.6; border: 1px solid #334155;">{html_diff}</div>', 
                            unsafe_allow_html=True
                        )
                        st.caption("🟢 Green words were added. 🔴 Red words with strikethroughs were corrected or deleted.")
                        
                    with tab2:
                        st.text_area("Corrected text ready to copy:", value=corrected_text, height=180)
                        
                    with tab3:
                        if "errors" in result and result["errors"]:
                            for item in result["errors"]:
                                st.markdown(
                                    f"🚨 **Correction:** `{item['original']}` ➔ `{item['replacement']}` "
                                    f"({item['category']})\n\n"
                                    f"*Explanation:* {item['explanation']}"
                                )
                                st.write("---")
                        else:
                            st.info(
                                "Detailed explanations are fully supported under the Google Gemini backend. "
                                "Your local Transformer model corrects sentences directly, but does not output individual error breakdowns. "
                                "Enable the Google Gemini backend in the sidebar for complete linguistic logs!"
                            )
                            
                    # Export options
                    st.write("")
                    report_content = (
                        f"# AI Academic Assistant Writing Report\n"
                        f"Correction Engine: {result['method']}\n"
                        f"Original Text: {input_text}\n\n"
                        f"Corrected Text: {corrected_text}\n"
                    )
                    st.download_button(
                        label="💾 Download Corrected Report (.txt)",
                        data=report_content,
                        file_name="academic_assistant_report.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                elif result:
                    st.error(f"Analysis failed: {result.get('error')}")
    else:
        # Default placeholder panel
        st.info("👈 Input text on the left and click 'Check Grammar' to see analysis here!")
        st.image("https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?auto=format&fit=crop&q=80&w=600", use_container_width=True)
