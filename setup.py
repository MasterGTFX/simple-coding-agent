from setuptools import setup

setup(
    name="simple-coding-agent",
    version="0.1.0",
    py_modules=["agent", "tools", "commands", "llm", "config"],
    install_requires=[
        "langchain-openai", 
        "langchain-core", 
        "python-dotenv",
        "langchain-anthropic",
        "langchain-google-genai",
        "openai",
        "anthropic",
        "google-generativeai",
        "platformdirs"
    ],
    entry_points={"console_scripts": ["coding-agent=agent:main"]},
    python_requires=">=3.10",
)
