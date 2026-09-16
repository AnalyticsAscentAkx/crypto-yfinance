from setuptools import setup, find_packages
from pathlib import Path

readme = Path("README.md").read_text(encoding="utf-8") if Path("README.md").exists() else ""

setup(
    name="crypto-yfinance",
    version="0.2.1",
    packages=find_packages(),
    install_requires=[
        "ccxt>=4.0.0",
        "pycoingecko>=3.1.0",
        "pandas>=1.5.0",
        "plotly>=5.0.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "ta": ["pandas-ta-classic>=0.3.15"],
        "full": ["pandas-ta-classic>=0.3.15"],
    },
    author="Aakash Chavan Ravindranath",
    author_email="craakash@gmail.com",
    description="Unified cryptocurrency data API — prices, on-chain, derivatives, DeFi, sentiment and more",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/craakash/crypto-yfinance",
    project_urls={
        "Source":   "https://github.com/craakash/crypto-yfinance",
        "Issues":   "https://github.com/craakash/crypto-yfinance/issues",
        "Homepage": "https://medium.com/@craakash",
        "LinkedIn": "https://www.linkedin.com/in/aakashcr/",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Science/Research",
    ],
    python_requires=">=3.9",
    license="MIT",
    license_files=["LICENSE"],
    keywords=[
        "crypto", "cryptocurrency", "bitcoin", "ethereum", "finance",
        "data", "api", "trading", "defi", "on-chain", "blockchain",
        "binance", "coingecko", "defillama", "yfinance",
    ],
)
