from setuptools import setup, find_packages

setup(
    name="llmops-sdk",
    version="1.0.0",
    description="LLMOps Monitoring Platform SDK",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    author="LLMOps Platform",
    packages=find_packages(),
    install_requires=["httpx>=0.28.0"],
    extras_require={"groq": ["groq>=0.13.0"], "all": ["groq>=0.13.0", "google-generativeai>=0.8.0"]},
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
