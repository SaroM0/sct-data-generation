# SCT Data Generation

Automated generation of Script Concordance Test (SCT) items for medical education using Large Language Models.

## Overview

This project implements an automated system for generating high-quality Script Concordance Test (SCT) items in the field of hepatology and gastroenterology. Based on research findings from "Using Large Language Models to Generate Script Concordance Test in Medical Education: ChatGPT and Claude," this implementation supports both OpenAI and Google Gemini APIs for generating clinically relevant assessment items.

### What are Script Concordance Tests?

Script Concordance Tests (SCT) are assessment tools designed to evaluate clinical reasoning in situations of uncertainty. Each SCT item consists of:

1. **A clinical vignette** with controlled ambiguity (one patient case)
2. **Three independent evaluation scenarios**:
   - **Diagnosis scenario**: Evaluates diagnostic reasoning ("If you were thinking of [diagnosis]... and then you find that... this hypothesis becomes...")
   - **Management scenario**: Evaluates treatment decisions ("If you were thinking of [intervention]... and then you find that... this action becomes...")
   - **Follow-up scenario**: Evaluates monitoring strategies ("If you were thinking of [follow-up plan]... and then you find that... this plan becomes...")
3. **A 5-point Likert scale** for each scenario to assess the change in likelihood/appropriateness

**Important**: Each scenario is completely independent - information from one scenario does NOT carry over to the others.

### Key Features

- **Multiple LLM Providers**: Choose between OpenAI or Google Gemini for generation
- **Automated Generation**: Creates complete SCT items using structured outputs API
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
│   ├── llm/                   # LLM clients (OpenAI and Gemini)
│   │   ├── openai/            # OpenAI client and services
│   │   └── gemini/            # Gemini client and services
│   ├── generator/             # SCT generation logic
│   ├── validators/            # Validation rules and utilities
│   ├── schemas/               # Pydantic data models
│   └── prompts/               # XML prompt templates
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
- OpenAI API key and/or Google Gemini API key

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

5. **Set your API key(s)**
   
   Edit `.env` file:
   ```bash
   # Choose your provider: "openai" or "gemini"
   LLM_PROVIDER=openai
   
   # Set the appropriate API key
   OPENAI_API_KEY=your-openai-api-key-here
   GEMINI_API_KEY=your-gemini-api-key-here
   
   # Configure generation settings
   NUM_SCTS_TO_GENERATE=10
   MODEL=chatgpt-4o-latest  # or gemini-2.5-flash for Gemini
   DOMAIN_DISTRIBUTION=HCC,Obesity,Celiac_Disease,GERD,IBD,Pancreatitis
   LOG_LEVEL=INFO
   ```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LLM_PROVIDER` | LLM provider to use ("openai" or "gemini") | openai | Yes |
| `OPENAI_API_KEY` | Your OpenAI API key | - | If using OpenAI |
| `GEMINI_API_KEY` | Your Google Gemini API key | - | If using Gemini |
| `NUM_SCTS_TO_GENERATE` | Number of items to generate | 10 | Yes |
| `MODEL` | LLM model to use | chatgpt-4o-latest | Yes |
| `DOMAIN_DISTRIBUTION` | Comma-separated clinical domains | HCC,Obesity,... | Yes |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, WARNING, ERROR) | INFO | No |

### Supported Models

**OpenAI:**
- `chatgpt-4o-latest` (recommended)
- `gpt-4o`
- `gpt-4o-mini`

**Google Gemini:**
- `gemini-2.5-flash` (recommended)
- `gemini-2.5-pro`
- `gemini-2.0-flash`

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

**Use Gemini instead of OpenAI:**
```bash
LLM_PROVIDER=gemini MODEL=gemini-2.5-flash poetry run sct-generate
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
  LLM Provider: OPENAI
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
  "guideline": "american",
  "vignette": "Clinical case (120-240 words)...",
  "questions": [
    {
      "question_type": "diagnosis",
      "hypothesis": "hepatocellular carcinoma",
      "new_information": "AFP is 450 ng/mL with arterial enhancement on CT",
      "effect_phrase": "this hypothesis becomes",
      "options": ["+2", "+1", "0", "-1", "-2"],
      "author_notes": "High AFP with arterial enhancement strongly supports HCC..."
    },
    {
      "question_type": "management",
      "hypothesis": "scheduling transarterial chemoembolization",
      "new_information": "patient has portal vein thrombosis on imaging",
      "effect_phrase": "this action becomes",
      "options": ["+2", "+1", "0", "-1", "-2"],
      "author_notes": "Portal vein thrombosis is a relative contraindication for TACE..."
    },
    {
      "question_type": "followup",
      "hypothesis": "repeating imaging in 3 months to assess response",
      "new_information": "AFP has decreased from 450 to 80 ng/mL after treatment",
      "effect_phrase": "this plan becomes",
      "options": ["+2", "+1", "0", "-1", "-2"],
      "author_notes": "Significant AFP decrease suggests good response; 3-month imaging is appropriate..."
    }
  ]
}
```

**Note**: Each generated item now includes **3 independent scenarios** (diagnosis, management, and follow-up) for comprehensive assessment.

## Validation System

The system performs automatic quantitative validation on all generated items:

### Validation Rules

**Domain:**
- Required, not empty
- Format: `^[A-Za-z0-9_]{3,40}$`
- Length: 3-40 characters

**Vignette:**
- Required, not empty
- Length: 120-240 words (aim for 150-200)
- Single paragraph (no line breaks)

**Questions Array:**
- Exactly 3 questions required
- Must be in order: diagnosis → management → followup
- Each question is validated independently

**For Each Question:**

- **Question Type**: Must be "diagnosis", "management", or "followup"
- **Hypothesis**: 
  - Required, not empty
  - Length: 8-25 words
  - Must be affirmative (no question marks)
- **New Information**:
  - Required, not empty
  - Length: 8-30 words
  - Declarative only (no questions)
  - Maximum 2 sentences
- **Options**:
  - Required, exactly 5 elements
  - Must be: `["+2", "+1", "0", "-1", "-2"]` in that order
- **Author Notes**:
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
- **LLM Providers**: OpenAI (Responses API) and Google Gemini
- **Data Validation**: Pydantic v2
- **Prompt Format**: Structured XML
- **Configuration**: Pydantic Settings + python-dotenv

### Choosing a Provider

This implementation supports both OpenAI and Google Gemini:

**OpenAI:**
- Excellent clinical accuracy
- Strong adherence to SCT format specifications
- Consistent structured output generation
- Superior reasoning in ambiguous scenarios

**Google Gemini:**
- Fast response times (especially with 2.5 Flash)
- Cost-effective for high-volume generation
- Good structured output support
- Native thinking capabilities for complex reasoning

### Dependencies

```toml
python = "^3.10"
openai = "^1.0.0"
google-genai = "^0.3.0"
pydantic = "^2.0.0"
pydantic-settings = "^2.0.0"
python-dotenv = "^1.0.0"
```

## Troubleshooting

### Common Issues

**Issue: "Invalid LLM_PROVIDER"**
- Solution: Set `LLM_PROVIDER` to either "openai" or "gemini" in your `.env` file

**Issue: "OPENAI_API_KEY not configured" or "GEMINI_API_KEY not configured"**
- Solution: Ensure your `.env` file contains the appropriate API key for your chosen provider

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

## Recent Updates (October 2025)

### New SCT Format: 3 Independent Evaluation Scenarios

The system has been updated to match the authentic Script Concordance Test format used in medical education. Key changes:

✅ **Each vignette now generates 3 independent scenarios**:
- Diagnosis scenario (evaluates diagnostic reasoning)
- Management scenario (evaluates treatment decisions)
- Follow-up scenario (evaluates monitoring strategies)

✅ **Authentic SCT format**: "If you were thinking of... and then you find that... this hypothesis/plan becomes..."

✅ **Complete independence**: Each scenario starts fresh from the vignette - no information carryover

✅ **Enhanced CSV export**: Generates 3 rows per vignette (one per scenario)

✅ **Updated validation**: Checks all 3 scenarios independently

### Migration Information

- **Old format files**: Existing single-question JSON files remain valid for reference
- **New generations**: All new items automatically use the 3-scenario format
- **Documentation**: See `MIGRATION_GUIDE.md` (English) and `RESUMEN_CAMBIOS.md` (Spanish) for detailed information
- **Testing**: Run `poetry run python test_new_format.py` to verify the new format

### Benefits

1. **More authentic**: Matches real SCT format from medical education
2. **Comprehensive**: Each case assesses diagnosis, management, AND follow-up
3. **3x more data**: Each vignette provides 3 evaluation scenarios
4. **Better training**: Independent scenarios avoid compound dependencies

## Research Background

This implementation is based on findings from:

**"Using Large Language Models to Generate Script Concordance Test in Medical Education: ChatGPT and Claude"**

The research demonstrated that Large Language Models, particularly GPT-4-based models, can generate clinically relevant SCT items with appropriate ambiguity and reasoning complexity suitable for medical education assessment.