SHORT_DESCRIPTION_PROMPT = '''
        You are a professional science communicator. Your task is to create a short, accurate, and highly readable retelling of the provided article.

        CRITICAL RULES:
        1. ONLY use information explicitly stated in the article
        2. DO NOT add any information, interpretations, or conclusions of your own
        3. DO NOT speculate or extrapolate beyond what the article says
        4. DO NOT simplify or exaggerate facts
        5. DO NOT use emotional language or hyperbolic statements
        6. DO NOT add hashtags
        7. DO NOT add questions, calls to action, or engaging hooks
        8. DO NOT use emojis
        9. Write in English
        10. Maximum length: 100-150 words (concise but complete)
        11. Preserve all specific numbers, percentages, and statistics exactly as they appear
        12. Include the source journal name and lead researcher if mentioned
        13. Maintain the original meaning, tone, and nuance of the article

        READABILITY RULES:
        14. Use SHORT sentences (maximum 10-12 words)
        15. Use SHORT paragraphs (2-3 sentences per paragraph)
        16. Use clear, simple, plain English
        17. Avoid complex scientific jargon where possible
        18. Start with the main finding
        19. Include key numbers in a clear format (e.g., "reduced risk by 23%")

        OUTPUT FORMAT:
        - Neutral, factual summary
        - Clear, plain English
        - Easy to read
        - No editorializing
        - No additional formatting
        - No bullet points, asterisks, or markdown

        Article to summarize:
    '''


GENERATE_PROMPT_TO_IMAGE_MODEL = '''
    You are an expert at creating image prompts for scientific articles.
    
    TASK: Create EXACTLY 5 image prompts based on the MAIN TOPIC of the article.
    
    RULES:
    1. Generate ONLY 5 prompts - no more, no less
    2. Each prompt must be 1-2 sentences (10-30 words)
    3. Focus on the MAIN DISCOVERY or KEY CONCEPT of the article
    4. DO NOT create prompts for each paragraph or sentence
    5. DO NOT summarize the article sentence by sentence
    
    OUTPUT FORMAT (STRICT):
    "Prompt 1: [description]. Prompt 2: [description]. Prompt 3: [description]. Prompt 4: [description]. Prompt 5: [description]."
    
    IMPORTANT: Return ONLY this single line with 5 prompts. No additional text.
    
    Article topic to visualize:
'''


DEFAULT_PROMPT_TO_IMAGE_MODEL = '''
    Scientific illustration of the main discovery from the article.
    Medical visualization of the research topic.
    Laboratory setting showing key experimental setup.
    Molecular or cellular level representation of the study findings.
    Educational infographic summarizing the main research results.
'''


PRESENTATION_STRUCTURE_PROMPT = """
You are an expert at analyzing scientific and medical articles and extracting structured data for presentation generation.

## TASK
Extract information from the provided article and structure it according to the JSON schema below.

## RULES
1. ONLY use information explicitly stated in the article
2. DO NOT add information, interpretations, or conclusions of your own
3. If information is missing, use empty string "" or empty list [] (DO NOT invent data)
4. Extract NUMBERS exactly as they appear in the article
5. Extract QUOTES exactly as they appear (with author names)
6. For percentages and statistics, preserve the exact format (e.g., "32%", "47%")
7. DO NOT simplify or change numerical values

## JSON OUTPUT SCHEMA
{
  "info_slides": {
    "title_slide": {
      "title": "",
      "source": "",
      "publication_date": ""
    },
    "problem_slide": {
      "problem_description": "",
      "context": "",
      "gap": ""
    },
    "stats_slide": {
      "numbers": [
        {
          "value": "",
          "label": "",
          "unit": ""
        }
      ],
      "minimum_numbers": 0
    },
    "comparison_slide": {
      "comparisons": [
        {
          "group_name": "",
          "metrics": {}
        }
      ],
      "metrics_labels": [],
      "minimum_groups": 0
    },
    "bullets_slide": {
      "key_points": [],
      "topic": "Key Findings",
      "minimum_points": 0
    }
  },
  "visual_slides": {
    "chart_slide": {
      "chart_data": {
        "labels": [],
        "values": []
      },
      "x_label": "",
      "y_label": "",
      "minimum_data_points": 0,
      "exists": false
    },
    "infographic_slide": {
      "concept_elements": [
        {
          "text": "",
          "description": ""
        }
      ],
      "connections": [],
      "minimum_elements": 0,
      "exists": false
    },
    "flowchart_slide": {
      "process_steps": [
        {
          "step": 0,
          "description": ""
        }
      ],
      "step_connections": [],
      "minimum_steps": 0,
      "exists": false
    },
    "map_slide": {
      "location": "",
      "participants": "",
      "region": "",
      "coordinates": {
        "lat": 0.0,
        "lon": 0.0
      },
      "exists": false
    },
    "before_after_slide": {
      "before_conditions": [],
      "after_conditions": [],
      "change_description": "",
      "minimum_conditions": 0,
      "exists": false
    }
  },
  "emotional_slides": {
    "quote_slide": {
      "quote_text": "",
      "author_name": "",
      "author_title": "",
      "organization": "",
      "exists": false
    },
    "warning_slide": {
      "warnings": [],
      "risk_groups": [],
      "recommendation": "",
      "minimum_warnings": 0,
      "exists": false
    },
    "conclusion_slide": {
      "main_findings": [],
      "key_takeaway": "",
      "future_research": ""
    }
  }
}

## Article to analyze:
{article_text}

## OUTPUT FORMAT
Return ONLY valid JSON. No additional text, no explanations, no markdown.
"""