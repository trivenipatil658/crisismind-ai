from llm_service import is_ollama_available, OLLAMA_MODEL
print("LLM service imported OK")
print("Ollama available:", is_ollama_available())
print("Model:", OLLAMA_MODEL)

from langgraph_workflow import workflow
print("Workflow with ollama_explanation_node compiled OK")
