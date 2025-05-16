# CAMEL OSINT System

A multi-agent system for OSINT (Open-Source Intelligence) collection, verification, and reporting, built on the CAMEL (Communicative Agents for "Mind" Exploration of Large-scale LMs) framework.

## Overview

This system uses a team of specialized AI agents to investigate human rights violations, wartime atrocities, and other events by gathering and analyzing open-source information. The system works through a pipeline of agents:

1. **Collector Agent**: Gathers data from various online sources (news, social media, etc.)
2. **Verification Agent**: Authenticates and validates the collected information
3. **Report Writer Agent**: Compiles verified information into comprehensive reports
4. **Ethical Filter Agent**: Reviews reports for compliance with ethical standards

## Features

- **Multi-agent architecture**: Specialized agents work together in a coordinated workflow
- **Automated OSINT workflow**: From data collection to report generation
- **Verification tools**: Reverse image search, geolocation, shadow analysis, and more
- **Ethical considerations**: Content moderation and privacy protection
- **GUI interface**: User-friendly interface for submitting queries and viewing results
- **API access**: RESTful API and WebSocket support for integration

## Installation

### Prerequisites

- Python 3.10+
- pip package manager
- Virtual environment (recommended)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/camel-osint.git
   cd camel-osint
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=your_openai_api_key
   BING_API_KEY=your_bing_api_key
   GOOGLE_GEOCODE_API_KEY=your_google_api_key
   ```

## Usage

### Running the Application

You can run the application in different modes:

1. **Both API and GUI** (default):
   ```bash
   python main.py
   ```

2. **API server only**:
   ```bash
   python main.py --mode api
   ```

3. **GUI only**:
   ```bash
   python main.py --mode gui
   ```

### Using the GUI

1. Launch the application
2. Enter your OSINT query in the text box (e.g., "Investigate bombing of Al-Shifa Hospital in Gaza in October 2023")
3. Click "Submit Query"
4. View real-time progress in the Status tab
5. When processing is complete, view the report in the Report tab

### Using the API

The API is available at `http://localhost:8000` with the following endpoints:

- `POST /query`: Submit a new OSINT query
  ```json
  {
    "query": "Investigate bombing of Al-Shifa Hospital in Gaza in October 2023"
  }
  ```

- `GET /status`: Check the current processing status
- `GET /report`: Get the final report
- `WebSocket /ws`: Connect for real-time updates

## Customization

### Adding New Tools

1. Create a new tool function in the appropriate file in `app/tools/`
2. Register the tool in the relevant agent's `__init__` method
3. Update the tool imports in `app/tools/__init__.py`

### Modifying Agent Prompts

Agent prompts can be customized in `app/config/config.py` under the respective prompt template variables.

## Limitations

- The current implementation uses mock OSINT tools for demonstration purposes
- To use real tools, you'll need to replace the mock implementations with actual API calls
- Some features require additional API keys and subscriptions to external services

## License

[MIT License](LICENSE)

## Acknowledgments

- This project is built on the [CAMEL](https://github.com/camel-ai/camel) framework
- The OSINT methodology is inspired by open-source investigators like Bellingcat and CIR 