# MedicaLLM System Prompt Guide

## Overview

The system prompt has been completely overhauled to provide clear, structured guidance for the LangChain agent. It now includes comprehensive tool documentation, response guidelines, and role-specific language adjustments.

## Prompt Structure

### 1. Core Principles

```
1. EVIDENCE-BASED: Ground all clinical claims in retrieved sources or database information
2. CONVERSATIONAL: Respond naturally to greetings and casual questions
3. MULTI-TOOL: Chain tools intelligently when needed
4. CLEAR & STRUCTURED: Use clear formatting with headers, bullet points, and tables
```

### 2. Available Tools Section

Provides detailed documentation for all 7 tools:
- Tool name and signature
- When to use it
- Example queries

This helps the agent understand:
- Which tool to use for each query type
- How to call tools correctly
- When to chain multiple tools

### 3. Response Guidelines

Specific guidance for each query type:

#### Drug Information Queries
- Use `get_drug_info` with appropriate detail level
- Present information in clear sections
- Include relevant warnings

#### Interaction Queries
- Use interaction checking tools
- State severity clearly
- Explain clinical significance
- Suggest alternatives for high-severity interactions

#### Patient Medication Analysis
- Use `analyze_patient_medications` when patient context active
- Present findings in clear sections
- Prioritize by severity
- Provide actionable recommendations

#### Treatment Recommendations
- Use search tools
- Present options with descriptions
- Always remind to consult healthcare provider

#### Alternative Drug Requests
- Use `recommend_alternative_drug`
- Explain why each alternative is suitable
- Note important differences

### 4. Formatting Rules

Clear guidelines for response formatting:
- **Bold** for drug names and important terms
- Bullet points for lists
- Tables for comparisons (each row on separate line)
- Emoji severity indicators: 🔴 MAJOR, 🟠 MODERATE, 🟡 MINOR, ✅ SAFE
- Concise but complete responses

### 5. Safety Reminders

- Include appropriate disclaimers
- Flag high-severity interactions prominently
- Note when information is limited
- Never provide specific dosing recommendations (unless from database)

### 6. Conversation Style

- Professional but approachable
- Respond to greetings naturally
- Ask clarifying questions when needed
- Acknowledge uncertainty when appropriate
- Use medical terminology appropriately based on user's role

## Role-Specific Prompts

### Healthcare Professional Mode

Activated when `is_doctor=True`:

```
# RESPONSE LANGUAGE — HEALTHCARE PROFESSIONAL:

You are speaking with a qualified healthcare professional. Adjust your language accordingly:

- Use precise clinical terminology
- Include mechanism of action details
- Discuss pharmacokinetic considerations (ADME)
- Provide evidence-based citations when available
- Include relevant dosing considerations from database
- Assume medical training; no need for lay explanations of standard concepts
```

**Key Characteristics:**
- Technical medical terminology
- Detailed pharmacological information
- Evidence-based approach
- Assumes medical knowledge

### General User Mode

Activated when `is_doctor=False`:

```
# RESPONSE LANGUAGE — GENERAL USER:

You are speaking with a member of the general public. Adjust your language accordingly:

- Use plain, accessible language
- Avoid medical jargon; explain technical terms when necessary
- Focus on practical safety advice
- Always recommend consulting a licensed healthcare provider
- Emphasize that this is educational information, not medical advice
```

**Key Characteristics:**
- Plain language
- Explanations of technical terms
- Safety-focused
- Clear disclaimers

## Patient Context Block

When a patient is active (`patient is not None`):

```
# ACTIVE PATIENT PROFILE:

**Patient:** [Name]
**DOB:** [Date] | **Gender:** [Gender]
**Chronic Conditions:** [List or "None"]
**Current Medications:** [List or "None"]
**Known Allergies:** [List or "None"]
**Clinical Notes:** [Notes if available]

**IMPORTANT PATIENT CONTEXT RULES:**
- Consider this patient's profile when answering EVERY question
- Proactively flag conflicts between patient's allergies and any mentioned drug
- Proactively flag conflicts between patient's current medications and any new drug discussed
- When asked to analyze this patient's medications, use the analyze_patient_medications tool
- The analyze_patient_medications tool will automatically access this patient's data
```

**Key Features:**
- Clear patient information display
- Explicit rules for using patient context
- Proactive conflict detection
- Tool usage guidance

## Prompt Assembly

The final prompt is assembled in `build_system_prompt()`:

```python
def build_system_prompt(
    is_doctor: bool = False,
    patient: PatientDetails | None = None,
) -> str:
    parts = [SYSTEM_PROMPT]
    
    if is_doctor:
        parts.append(_ROLE_HEALTHCARE)
    else:
        parts.append(_ROLE_GENERAL)
    
    if patient:
        parts.append(patient_block)
    
    return "\n".join(parts)
```

**Assembly Order:**
1. Core system prompt (tools, guidelines, formatting)
2. Role-specific prompt (healthcare or general)
3. Patient context block (if patient active)

## Example Prompts

### Example 1: General User, No Patient

```
[SYSTEM_PROMPT]
- Core principles
- Tool documentation
- Response guidelines
- Formatting rules
- Safety reminders
- Conversation style

[_ROLE_GENERAL]
- Plain language
- Explain technical terms
- Safety focus
- Disclaimers
```

### Example 2: Healthcare Professional, No Patient

```
[SYSTEM_PROMPT]
- Core principles
- Tool documentation
- Response guidelines
- Formatting rules
- Safety reminders
- Conversation style

[_ROLE_HEALTHCARE]
- Clinical terminology
- Detailed pharmacology
- Evidence-based
- Assumes medical knowledge
```

### Example 3: Healthcare Professional, With Patient

```
[SYSTEM_PROMPT]
- Core principles
- Tool documentation
- Response guidelines
- Formatting rules
- Safety reminders
- Conversation style

[_ROLE_HEALTHCARE]
- Clinical terminology
- Detailed pharmacology
- Evidence-based
- Assumes medical knowledge

[PATIENT_BLOCK]
- Patient demographics
- Chronic conditions
- Current medications
- Known allergies
- Clinical notes
- Patient context rules
```

## Best Practices

### 1. Tool Documentation
- Keep tool descriptions concise but complete
- Include clear examples
- Update when tools change

### 2. Response Guidelines
- Provide specific guidance for each query type
- Include formatting examples
- Emphasize safety and disclaimers

### 3. Role Adaptation
- Make role differences clear
- Adjust terminology appropriately
- Maintain professional tone in both modes

### 4. Patient Context
- Display patient information clearly
- Provide explicit rules for using context
- Emphasize proactive conflict detection

### 5. Formatting
- Use consistent markdown formatting
- Include visual indicators (emojis)
- Keep responses structured

## Maintenance

### When to Update

1. **New Tools Added:**
   - Add tool documentation to SYSTEM_PROMPT
   - Add response guidelines for new query types
   - Update ALL_TOOLS list

2. **Tool Signatures Change:**
   - Update tool documentation
   - Update example usage
   - Test with agent

3. **New Response Patterns:**
   - Add to response guidelines
   - Include formatting examples
   - Update conversation style if needed

4. **Safety Requirements Change:**
   - Update safety reminders section
   - Adjust disclaimers
   - Update role-specific prompts if needed

### Testing Prompt Changes

1. **Test with Different Roles:**
   - Healthcare professional mode
   - General user mode
   - Verify language differences

2. **Test with Patient Context:**
   - Active patient
   - No patient
   - Verify context usage

3. **Test Tool Selection:**
   - Various query types
   - Verify correct tool selection
   - Check tool chaining

4. **Test Response Formatting:**
   - Check markdown rendering
   - Verify emoji indicators
   - Check table formatting

## Troubleshooting

### Agent Not Using Tools

**Possible Causes:**
- Tool documentation unclear
- Query doesn't match use cases
- Tool signature incorrect

**Solutions:**
- Clarify tool descriptions
- Add more example queries
- Verify tool signatures

### Incorrect Tool Selection

**Possible Causes:**
- Overlapping tool descriptions
- Unclear use cases
- Missing response guidelines

**Solutions:**
- Make tool purposes distinct
- Add specific use cases
- Provide clear response guidelines

### Poor Response Formatting

**Possible Causes:**
- Formatting rules unclear
- Examples missing
- Conflicting guidelines

**Solutions:**
- Clarify formatting rules
- Add formatting examples
- Remove conflicting guidelines

### Role Adaptation Not Working

**Possible Causes:**
- Role prompts too similar
- Role differences not emphasized
- Conflicting instructions

**Solutions:**
- Make role differences clearer
- Emphasize key distinctions
- Remove conflicting instructions

## Future Enhancements

1. **Dynamic Tool Documentation:**
   - Generate tool docs from tool definitions
   - Keep docs in sync with code

2. **Context-Aware Prompts:**
   - Adjust based on conversation history
   - Adapt to user expertise level

3. **Multi-Language Support:**
   - Language-specific prompts
   - Cultural adaptations

4. **Specialized Modes:**
   - Emergency mode
   - Research mode
   - Teaching mode

5. **Prompt Optimization:**
   - A/B testing different prompts
   - Metrics-driven improvements
   - User feedback integration
