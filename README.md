# SCT Data Generation

Automated generation of Script Concordance Test (SCT) items for medical education using Large Language Models.

## Overview

This project implements an automated system for generating high-quality Script Concordance Test (SCT) items in the field of hepatology and gastroenterology. Based on research findings from "Using Large Language Models to Generate Script Concordance Test in Medical Education: ChatGPT and Claude," this implementation uses OpenAI's API exclusively due to its superior performance in generating clinically relevant assessment items.

### What are Script Concordance Tests?

Script Concordance Tests (SCT) are assessment tools designed to evaluate clinical reasoning in situations of uncertainty. Each SCT item presents:

1. A clinical vignette with controlled ambiguity
2. A diagnostic, therapeutic, or test-related hypothesis
3. New information that modulates the hypothesis
4. A 5-point Likert scale to assess probability change

### Key Features

- **Automated Generation**: Creates complete SCT items using OpenAI's structured outputs API
- **Configurable Domains**: Customizable clinical domains (HCC, Obesity, Celiac Disease, GERD, IBD, Pancreatitis, etc.)
- **Validation System**: Automatic quantitative validation of generated items
- **Organized Storage**: Triple-folder system for cataloging all, validated, and failed items
- **Structured Output**: Guaranteed JSON schema compliance using Pydantic models
- **Complete Logging**: Comprehensive tracking of generation and validation processes

## Project Structure

```
sct-data-generation/
├── src/
│   ├── config.py              # Configuration management
│   ├── logging.py             # Logging setup
│   ├── main.py                # Application entry point
│   ├── llm/                   # OpenAI client and services
│   ├── generator/             # SCT generation logic
│   ├── validators/            # Validation rules and utilities
│   ├── schemas/               # Pydantic data models
│   └── prompts/               # Generation prompt templates
├── data/
│   ├── generated/             # All generated items
│   ├── validated/             # Items that passed validation
│   └── validation_failed/     # Items that failed validation
├── pyproject.toml             # Poetry dependencies
└── .env                       # Environment configuration
```

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (Python package manager)
- OpenAI API key

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sct-data-generation
   ```

2. **Install Poetry** (if not already installed)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set your OpenAI API key**
   
   Edit `.env` file:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   NUM_SCTS_TO_GENERATE=10
   MODEL=chatgpt-4o-latest
   DOMAIN_DISTRIBUTION=HCC,Obesity,Celiac_Disease,GERD,IBD,Pancreatitis
   LOG_LEVEL=INFO
   ```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | - | Yes |
| `NUM_SCTS_TO_GENERATE` | Number of items to generate | 10 | Yes |
| `MODEL` | OpenAI model to use | chatgpt-4o-latest | Yes |
| `DOMAIN_DISTRIBUTION` | Comma-separated clinical domains | HCC,Obesity,... | Yes |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, WARNING, ERROR) | INFO | No |

### Clinical Domains

The system distributes items across configurable clinical domains. Default domains include:

- **HCC**: Hepatocellular carcinoma and liver masses
- **Obesity**: Obesity-related hepatology conditions
- **Celiac_Disease**: Celiac disease and malabsorption
- **GERD**: Gastroesophageal reflux disease
- **IBD**: Inflammatory bowel disease
- **Pancreatitis**: Acute and chronic pancreatitis

You can customize domains by modifying `DOMAIN_DISTRIBUTION` in the `.env` file.

## Usage

### Running the Application

**Basic execution:**
```bash
poetry run sct-generate
```

**Generate specific number of items:**
```bash
NUM_SCTS_TO_GENERATE=5 poetry run sct-generate
```

**Alternative execution method:**
```bash
poetry run python -m src.main
```

### Output

The application generates three types of outputs:

1. **data/generated/**: All generated items (clean JSON)
2. **data/validated/**: Items that passed validation (JSON + metadata)
3. **data/validation_failed/**: Items that failed validation (JSON + metadata)

Each file is named with the pattern: `sct_{domain}_{timestamp}.json`

### Example Output

**Console output:**
```
======================================================================
SCT DATA GENERATION APPLICATION
======================================================================

Configuration:
  Number of SCTs: 10
  Model: chatgpt-4o-latest
  Domains: HCC, Obesity, Celiac_Disease, GERD, IBD, Pancreatitis (6 total)
  All items: data/generated/
  Validated: data/validated/
  Failed: data/validation_failed/

Starting generation of 10 SCT items
======================================================================

[1/10] Generating SCT item - Domain: HCC
✓ Validation passed
✓ Item saved to all folders (generated + validated)
✓ Successfully generated and saved item 1/10
...
```

**Generated JSON structure:**
```json
{
  "domain": "HCC",
  "vignette": "Clinical case (70-120 words)...",
  "hypothesis": "Diagnostic or therapeutic proposition",
  "new_information": "Additional data that modulates the hypothesis",
  "question": "How does the probability of the hypothesis change?",
  "options": ["+2", "+1", "0", "-1", "-2"],
  "author_notes": "Clinical rationale for internal review"
}
```

## Validation System

The system performs automatic quantitative validation on all generated items:

### Validation Rules

**Domain:**
- Required, not empty
- Format: `^[A-Za-z0-9_]{3,40}$`
- Length: 3-40 characters

**Vignette:**
- Required, not empty
- Length: 70-120 words
- Single paragraph (no line breaks)

**Hypothesis:**
- Required, not empty
- Length: 8-25 words
- Must be affirmative (no question marks)

**New Information:**
- Required, not empty
- Length: 8-30 words
- Declarative only (no questions)
- Maximum 2 sentences

**Question:**
- Required, must be exactly: "How does the probability of the hypothesis change?"

**Options:**
- Required, exactly 5 elements
- Must be: `["+2", "+1", "0", "-1", "-2"]` in that order

**Author Notes:**
- Optional
- Maximum 300 characters
- Maximum 3 sentences

### Validation Metadata

Items in `validated/` and `validation_failed/` folders include validation metadata:

```json
{
  "domain": "...",
  "vignette": "...",
  ...
  "_validation": {
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "validated_at": "2025-10-23T00:27:13.045102"
  }
}
```

## Technical Details

### Architecture

- **Language**: Python 3.10+
- **Package Manager**: Poetry
- **LLM Provider**: OpenAI (Responses API)
- **Data Validation**: Pydantic v2
- **Template Engine**: Jinja2
- **Configuration**: Pydantic Settings + python-dotenv

### Why OpenAI?

This implementation uses OpenAI exclusively based on research findings showing superior performance in:
- Clinical accuracy
- Adherence to SCT format specifications
- Consistency in structured output generation
- Quality of reasoning in ambiguous scenarios

### Dependencies

```toml
python = "^3.10"
openai = "^1.0.0"
pydantic = "^2.0.0"
pydantic-settings = "^2.0.0"
jinja2 = "^3.0.0"
python-dotenv = "^1.0.0"
```

## Troubleshooting

### Common Issues

**Issue: "OPENAI_API_KEY not configured"**
- Solution: Ensure your `.env` file contains a valid OpenAI API key

**Issue: "No domains configured"**
- Solution: Set `DOMAIN_DISTRIBUTION` in your `.env` file

**Issue: "Poetry command not found"**
- Solution: Install Poetry: `curl -sSL https://install.python-poetry.org | python3 -`

**Issue: Items failing validation**
- Check logs for specific validation errors
- Review items in `data/validation_failed/` folder
- Adjust prompt templates if systematic issues occur

## Development

### Project Commands

```bash
# Install dependencies
poetry install

# Add new dependency
poetry add <package-name>

# Update dependencies
poetry update

# Activate virtual environment
poetry shell

# Run application
poetry run sct-generate
```

### File Organization

- All generated items are saved to `data/generated/` (clean JSON for analysis)
- Validated items are also copied to `data/validated/` (with metadata)
- Failed items are also copied to `data/validation_failed/` (with error details)

This redundancy ensures complete traceability and easy filtering for different use cases.

## Research Background

This implementation is based on findings from:

**"Using Large Language Models to Generate Script Concordance Test in Medical Education: ChatGPT and Claude"**

The research demonstrated that Large Language Models, particularly GPT-4-based models, can generate clinically relevant SCT items with appropriate ambiguity and reasoning complexity suitable for medical education assessment.