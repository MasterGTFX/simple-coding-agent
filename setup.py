from setuptools import setup

setup(
    name="simple-coding-agent",
    version="0.1.0",
    py_modules=["agent", "tools"],
    install_requires=["langchain-openai", "langchain-core"],
    entry_points={"console_scripts": ["coding-agent=agent:main"]},
    python_requires=">=3.10",
)
