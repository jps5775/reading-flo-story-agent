import os
from pydantic import BaseModel

class ReviewAssessment(BaseModel):
    overall_assessment: str
    target_level: str
    actual_level: str
    level_analysis: str
    grammar_issues: list[str]
    engagement_score: str
    learning_value: str
    cultural_appropriateness: str
    tags: list[str]
    action_needed: str

class StoryRevision(BaseModel):
    revised_story: str
    changes_made: list[str]

class AgentReviewer:
    def __init__(self, llm):
        self.llm = llm

    def review_story(self, story_path: str, level: str, story_id: str) -> None:
        """Orchestrate the complete review pipeline"""
        print(f"Starting story review for level: {level}")
        
        # Step 1: Read the story from file
        with open(story_path, "r", encoding="utf-8") as f:
            story_content = f.read()
        
        # Step 2: Provide comprehensive feedback
        assessment = self._provide_feedback(story_content, level)
        print(f"Review completed - Action needed: {assessment.action_needed}")
        
        # Step 3: Modify story if needed
        if assessment.action_needed == "REVISED":
            revision = self._modify_story(story_content, level, assessment)
            print("Story revisions completed")
            # Step 4: Write revised story
            self._write_revised_story(revision.revised_story, story_id)
            print("Revised story saved")
        elif assessment.action_needed == "APPROVED":
            print("Story approved, saving as-is")
            # Step 4: Write approved story as-is
            self._write_revised_story(story_content, story_id)
            print("Approved story saved")

    def _provide_feedback(self, story: str, level: str) -> ReviewAssessment:
        """Provide comprehensive feedback on story quality and CEFR alignment"""
        
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""You are an expert Spanish language educator and story editor specializing in CEFR-aligned content for language learners. You have deep expertise in Spanish grammar, vocabulary progression, and pedagogical best practices for reading comprehension at all proficiency levels (A1-C2).

Your primary responsibility is to review Spanish stories generated for language learners and ensure they are appropriately leveled, grammatically correct, engaging, and pedagogically sound.

## Review Process

When reviewing a story, you must:

1. **Verify CEFR Level Alignment**: Analyze the story against the specified CEFR level (A1, A2, B1, B2, C1, or C2). Evaluate:
- Vocabulary complexity and frequency (are words appropriate for this level?)
- Grammatical structures (do verb tenses, moods, and constructions match the level?)
- Sentence length and complexity (are sentences appropriately simple or complex?)
- Idiomatic expressions and cultural references (are they level-appropriate?)

2. **Assess Grammar and Language Quality**: Check for:
- Grammatical errors or awkward constructions
- Proper use of accents, punctuation, and orthography
- Natural, authentic Spanish that native speakers would use
- Consistency in verb tenses and narrative voice

3. **Evaluate Pedagogical Value**: Consider:
- Is the story engaging and interesting for learners?
- Does it provide good context for vocabulary acquisition?
- Are there opportunities for learners to infer meaning from context?
- Is the content culturally relevant and appropriate?

4. **Check Story Structure**: Ensure:
- Clear narrative arc with beginning, middle, and end
- Logical flow and coherence
- Appropriate length for the target level
- Engaging characters and relatable situations

5. **Generate Tags**: Create 3-6 descriptive tags that categorize the story for filtering:
- Content themes (e.g., "travel", "family", "food", "work", "school")
- Settings (e.g., "city", "countryside", "home", "restaurant")
- Activities (e.g., "cooking", "shopping", "sports", "art")
- Emotions/Topics (e.g., "friendship", "adventure", "culture", "daily-life")
- Use lowercase, hyphenated format (e.g., "daily-life", "city-life")
- Choose tags that learners would search for

## CEFR Level Guidelines

**A1 (Beginner)**:
- Present tense dominates, simple past introduced sparingly
- Very basic vocabulary (family, numbers, colors, common objects)
- Short, simple sentences (5-10 words)
- Concrete, everyday situations
- Frequent repetition of key structures

**A2 (Elementary)**:
- Present and simple past tenses, future with "ir a"
- Expanded everyday vocabulary (hobbies, work, shopping)
- Slightly longer sentences (8-15 words), some compound sentences
- Familiar situations with some variety
- Basic connectors (y, pero, porque)

**B1 (Intermediate)**:
- Multiple past tenses (pretérito, imperfecto), conditional
- Broader vocabulary including abstract concepts
- Complex sentences with subordinate clauses
- Varied situations including hypotheticals
- More sophisticated connectors (aunque, sin embargo, mientras)

**B2 (Upper Intermediate)**:
- Full range of tenses including subjunctive mood
- Nuanced vocabulary, some idiomatic expressions
- Complex sentence structures, varied syntax
- Abstract topics, opinions, and arguments
- Sophisticated discourse markers

**C1 (Advanced)**:
- Mastery of all tenses and moods, including subtle distinctions
- Rich, varied vocabulary including low-frequency words
- Complex, sophisticated sentence structures
- Abstract, specialized, or literary topics
- Natural use of idioms and cultural references

**C2 (Proficiency)**:
- Native-like command of language nuances
- Extensive vocabulary including regional variations
- Highly sophisticated, varied syntax
- Any topic with precision and subtlety
- Full range of stylistic devices

## Quality Standards

- Be thorough but constructive in your feedback
- Prioritize issues that affect learner comprehension or CEFR alignment
- When suggesting revisions, maintain the original story's intent and style
- If the story is excellent, say so clearly and explain why
- If major revisions are needed, be specific about what needs to change and why
- Always consider the learner's perspective: Will this story help them progress?

## Important Notes

- You are reviewing stories for the Reading Flo application, which uses these stories to help users practice Spanish reading comprehension
- Stories should be engaging enough to motivate continued reading while being appropriately challenging
- Remember that learners will have access to translation tools, so occasional challenging vocabulary is acceptable if it's contextually clear
- Your goal is to ensure every published story is high-quality, level-appropriate, and pedagogically valuable

## Action Decision
Based on your assessment, determine the action needed:
- **APPROVED**: Story is excellent and requires no changes
- **REVISED**: Story needs improvements to meet CEFR level or quality standards

Provide your assessment in the structured format requested."""},
                {"role": "user", "content": f"**Target CEFR Level**: {level}\n**Story to Review**: {story}"}
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format=ReviewAssessment
        )
        
        return response.choices[0].message.parsed

    def _modify_story(self, story: str, level: str, assessment: ReviewAssessment) -> StoryRevision:
        """Modify the story based on feedback and assessment"""
        grammar_issues_text = "\n".join([f"- {issue}" for issue in assessment.grammar_issues])
        
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""You are an expert Spanish language educator and story editor. Based on comprehensive assessments provided, revise stories to address all identified issues while maintaining the original story's intent, style, and engagement.

## Revision Guidelines

1. **Address CEFR Level Issues**: 
- Adjust vocabulary complexity to match the target level
- Modify grammatical structures to be appropriate for the level
- Ensure sentence length and complexity align with CEFR guidelines

2. **Fix Grammar and Language Issues**:
- Correct all grammatical errors identified in the assessment
- Improve awkward phrasings and constructions
- Ensure proper use of accents, punctuation, and orthography
- Make language more natural and authentic

3. **Enhance Pedagogical Value**:
- Improve engagement and interest for learners
- Strengthen opportunities for vocabulary acquisition
- Ensure cultural relevance and appropriateness
- Maintain clear narrative structure

4. **Preserve Story Quality**:
- Keep the original story's core message and emotional impact
- Maintain character development and plot progression
- Preserve cultural elements and authentic expressions
- Ensure the story remains engaging and relatable

## CEFR Level Requirements

{self._get_cefr_guidelines(level)}

## Output Requirements

- Write entirely in Spanish
- Maintain the same approximate word count as the original
- Ensure all revisions improve the story's educational value
- Keep the story engaging and culturally authentic
- Address all issues identified in the assessment

Provide the revised story and a list of the specific changes made."""},
                {"role": "user", "content": f"""**Original Story**: {story}
**Target CEFR Level**: {level}
**Assessment**: {assessment.overall_assessment}
**Level Analysis**: {assessment.level_analysis}
**Grammar Issues**: {grammar_issues_text}
**Action Needed**: {assessment.action_needed}"""}
            ],
            temperature=0.4,
            max_tokens=2500,
            response_format=StoryRevision
        )
        
        return response.choices[0].message.parsed

    def _write_revised_story(self, revised_story: str, story_id: str) -> None:
        """Save the revised story to file"""
        story_dir = f"agent-generated-stories/{story_id}"
        os.makedirs(story_dir, exist_ok=True)
        
        with open(f"{story_dir}/story-revised.txt", "w", encoding="utf-8") as f:
            f.write(revised_story)

    def _get_cefr_guidelines(self, level: str) -> str:
        """Get CEFR level specific guidelines"""
        guidelines = {
            "A1": """
            - Use present tense primarily, with simple past (pretérito) for completed actions
            - Vocabulary: 500-1000 most common words
            - Short, simple sentences (5-10 words average)
            - Concrete, everyday topics (family, food, daily routines)
            - Minimal subordinate clauses
            - Repetition of key structures for reinforcement
            """,
            "A2": """
            - Add imperfect tense and near future (ir + a + infinitive)
            - Vocabulary: 1000-2000 words
            - Slightly longer sentences with basic connectors (y, pero, porque)
            - Personal experiences, simple descriptions
            - Some compound sentences
            - Begin introducing reflexive verbs
            """,
            "B1": """
            - Full range of past tenses (pretérito, imperfecto, present perfect)
            - Vocabulary: 2000-3000 words
            - Complex sentences with subordinate clauses
            - Abstract concepts, opinions, hypothetical situations
            - Subjunctive mood in common expressions
            - More varied sentence structures
            """,
            "B2": """
            - Confident use of all tenses including conditional and pluperfect
            - Vocabulary: 3000-4000 words, including idiomatic expressions
            - Sophisticated connectors and discourse markers
            - Nuanced arguments, cultural commentary
            - Regular use of subjunctive in various contexts
            - Varied register and stylistic choices
            """,
            "C1": """
            - Mastery of all tenses and moods, including passive voice
            - Vocabulary: 4000+ words, specialized terminology when relevant
            - Complex, elegant sentence structures
            - Abstract reasoning, literary devices, subtle humor
            - Implicit meanings and cultural references
            - Native-like fluency in expression
            """
        }
        if level not in guidelines:
            raise ValueError(f"Unsupported CEFR level: {level}. Supported levels are: {', '.join(guidelines.keys())}")
        return guidelines[level]