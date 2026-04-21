import os
from langchain_core.language_models.chat_models import BaseChatModel

def create_llm(model_id: str, **kwargs) -> BaseChatModel:
    """
    Create a LangChain chat model from a model_id.
    Format: [provider/]model_name
    """
    provider = "openai"
    model_name = model_id
    
    if "/" in model_id:
        provider, model_name = model_id.split("/", 1)
    else:
        if model_name.startswith("claude"):
            provider = "anthropic"
        elif model_name.startswith("gemini"):
            provider = "google"
            
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name, **kwargs)
    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model_name, **kwargs)
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            extra_body={"include_reasoning": True},
            **kwargs
        )
    elif provider == "ollama":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            api_key="ollama",
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            **kwargs
        )
    else:
        # Default to OpenAI
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name, **kwargs)
