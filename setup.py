from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="esim-tool-manager",
    version="1.0.0",
    author="eSim Development Team",
    author_email="esim-dev@fossee.in",
    description="Automated Tool Manager for eSim external EDA tools and dependencies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://esim.fossee.in",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "esim_tool_manager": ["data/*.json"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "esim-tools=esim_tool_manager.cli:main",
        ],
    },
)
