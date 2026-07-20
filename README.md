# 🎓 Smart AI Student Assistant: Grammar & Writing Advisor

This project is a high-performance **Student Academic Assistant** designed to find and correct grammatical errors in text. It is built in Python using **Streamlit** for a premium user interface and integrates two primary AI architectures:
1. **Local Hugging Face Transformer**: A locally hosted Text-to-Text Transfer Transformer (T5) model fine-tuned for Grammar Error Correction (GEC). It runs completely free, offline, and privately on your computer.
2. **Cloud-Based Large Language Model (LLM)**: An API-driven connection to Google Gemini 1.5 Flash (free-tier key) providing complex syntactic and stylistic suggestions alongside categorical annotations.


## 💡 Quick Academic Explanation (For your Deliverables)

For the project submission report, here is how the backends work:

### 1. The Local NLP Transformer (GEC Architecture)
- **Model Used**: `vennify/t5-base-grammar-correction`
- **Concept**: Text-to-Text Transfer Transformer (T5). T5 re-frames all NLP tasks into a unified text-to-text format. 
- **Methodology**: In our code, we prepend `"gec: "` (Grammar Error Correction) to the student's text. The model parses the tokens, projects them into a high-dimensional vector space, calculates attention weights between tokens (Self-Attention mechanism), and generates corrected sequence tokens.
- **Benefits**: 100% Free, runs offline, protects user privacy.

### 2. Large Language Model (Gemini LLM API)
- **Model Used**: `gemini-1.5-flash`
- **Concept**: Auto-regressive LLM with massive parameter counts trained on diverse linguistic patterns.
- **Methodology**: We supply the text alongside a *Structured System Prompt* requesting the output in raw JSON format. This enables us to dynamically extract structured fields like `corrected_text`, `original` errors, their `replacement`, and a contextual linguistic `explanation`.
- **Benefits**: Extreme structural and contextual accuracy, detects sophisticated errors (tone, styling, run-on sentences) and yields rich descriptive feedback.
