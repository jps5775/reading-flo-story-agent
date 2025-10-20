import os
from pydantic import BaseModel

class StoryIdeas(BaseModel):
    ideas: list[str]

class StoryDetails(BaseModel):
    title: str
    theme: str
    setting: str
    main_character: str
    conflict: str
    resolution: str

class StoryStructure(BaseModel):
    structure: list[str]

class StoryWorld(BaseModel):
    world_description: str
    cultural_elements: list[str]
    atmosphere: str

class StoryCharacters(BaseModel):
    main_character: str
    supporting_characters: list[str]
    character_relationships: str

class WritingStyle(BaseModel):
    style: str
    tone: str
    narrative_voice: str

class PlotPoints(BaseModel):
    plot_points: list[str]

class StoryOutline(BaseModel):
    outline: str

class StoryDraft(BaseModel):
    title: str
    story: str

class EntireStoreContext(BaseModel):
    title: str
    structure: StoryStructure
    world: StoryWorld
    characters: StoryCharacters
    style: WritingStyle
    plot_points: PlotPoints
    outline: StoryOutline

class AgentWriter:
    def __init__(self, llm):
        self.llm = llm

    def generate_story(self, topic, level, story_id, directory_path) -> EntireStoreContext:
        """Orchestrates the complete story generation pipeline"""
        print(f"Starting story generation for topic: {topic}, level: {level}")
        
        # Step 1: Generate multiple story ideas
        ideas = self._create_ideas(topic)
        print(f"Generated {len(ideas.ideas)} story ideas")
        
        # Step 2: Select the best idea
        selected_idea = self._select_idea(ideas.ideas)
        print(f"Selected idea: {selected_idea}")
        
        # Step 3: Create detailed story framework
        story_details = self._create_story_details(selected_idea, level)
        print(f"Created story details: {story_details.title}")
        
        # Step 4: Define story structure
        structure = self._create_story_structure(story_details)
        print(f"Created story structure with {len(structure.structure)} sections")
        
        # Step 5: Build the story world
        world = self._create_story_world(story_details)
        print("Created story world and cultural elements")
        
        # Step 6: Develop characters
        characters = self._create_story_characters(story_details)
        print(f"Created {len(characters.supporting_characters) + 1} characters")
        
        # Step 7: Select writing style
        style = self._select_writing_style(story_details, level)
        print(f"Selected writing style: {style.style}")
        
        # Step 8: Create plot points
        plot_points = self._create_plot_points(story_details, structure)
        print(f"Created {len(plot_points.plot_points)} plot points")
        
        # Step 9: Create detailed outline
        outline = self._create_outline(plot_points, story_details, world, characters, style, level)
        print("Created detailed story outline")
        
        # Step 10: Write the first draft
        draft = self._write_first_draft(outline, level)
        print(f"Completed first draft: {draft.title}")
        
        # Save the story
        story_dir = f"{directory_path}/{story_id}"
        os.makedirs(story_dir, exist_ok=True)
        
        with open(f"{story_dir}/story.txt", "w", encoding="utf-8") as f:
            f.write(draft.story)
        
        # returns the url of the story
        return EntireStoreContext(
            title=draft.title,
            structure=structure,
            world=world,
            characters=characters,
            style=style,
            plot_points=plot_points,
            outline=outline)

    def _create_ideas(self, topic: str) -> StoryIdeas:
        """Generate multiple creative story ideas based on the topic"""
        
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You are a creative Spanish story writer. Generate diverse, engaging story ideas that could be developed into educational Spanish stories for language learners.

Each idea should:
- Be suitable for language learning (clear, relatable situations)
- Include cultural elements from Spanish-speaking countries
- Have potential for character development and dialogue
- Be engaging and age-appropriate
- Allow for natural vocabulary and grammar progression

Return 5 distinct story concepts, each as a brief 1-2 sentence description."""},
                {"role": "user", "content": f"Topic: {topic}"}
            ],
            temperature=0.8,
            max_tokens=500,
            response_format=StoryIdeas
        )
        
        return response.choices[0].message.parsed

    def _select_idea(self, ideas: list[str]) -> str:
        """Select the best story idea from the generated options"""
        ideas_text = "\n".join([f"{i+1}. {idea}" for i, idea in enumerate(ideas)])
        
        response = self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You are an expert Spanish language educator. Select the ONE story idea that would be most effective for language learning.

Consider:
- Educational value (vocabulary, grammar, cultural learning)
- Engagement potential for learners
- Clarity and simplicity for language acquisition
- Cultural authenticity
- Potential for natural dialogue and interaction

Return only the selected idea text (not the number)."""},
                {"role": "user", "content": f"Story Ideas:\n{ideas_text}"}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()

    def _create_story_details(self, selected_idea: str, level: str) -> StoryDetails:
        """Create detailed story framework from the selected idea"""
        
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""You are a Spanish language educator and story developer. Create a detailed framework for stories that will be appropriate for {level} level learners.

Develop:
- A compelling Spanish title
- Clear theme/message
- Specific setting (time, place, cultural context)
- Main character with clear motivation
- Central conflict that drives the story
- Satisfying resolution

Ensure all elements are appropriate for {level} level vocabulary and grammar complexity."""},
                {"role": "user", "content": f"Selected Story Idea: {selected_idea}"}
            ],
            temperature=0.6,
            max_tokens=800,
            response_format=StoryDetails
        )
        
        return response.choices[0].message.parsed

    def _create_story_structure(self, story_details: StoryDetails) -> StoryStructure:
        """Define the narrative structure for the story"""
        
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """Create a clear narrative structure for stories. Define 4-6 main sections that will guide the story's progression.

Each section should:
- Advance the plot logically
- Include opportunities for character development
- Provide natural language learning moments
- Build toward the resolution

Return the section titles/descriptions as a list."""},
                {"role": "user", "content": f"""Story Details:
Title: {story_details.title}
Theme: {story_details.theme}
Setting: {story_details.setting}
Main Character: {story_details.main_character}
Conflict: {story_details.conflict}
Resolution: {story_details.resolution}"""}
            ],
            temperature=0.5,
            max_tokens=1200,
            response_format=StoryStructure
        )
        
        return response.choices[0].message.parsed

    def _create_story_world(self, story_details: StoryDetails) -> StoryWorld:
        """Build the cultural and environmental context for the story"""
        
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """Create a rich, culturally authentic world for Spanish stories. Focus on elements that will help language learners understand Spanish-speaking cultures.

Develop:
- Detailed world description (sights, sounds, atmosphere)
- Specific cultural elements (foods, traditions, customs, expressions)
- Overall atmosphere and mood

Ensure cultural elements are authentic and educational for language learners."""},
                {"role": "user", "content": f"""Story Details:
Title: {story_details.title}
Setting: {story_details.setting}
Theme: {story_details.theme}"""}
            ],
            temperature=0.6,
            max_tokens=700,
            response_format=StoryWorld
        )
        
        return response.choices[0].message.parsed

    def _create_story_characters(self, story_details: StoryDetails) -> StoryCharacters:
        """Develop detailed character profiles and relationships"""
        
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """Develop rich, authentic characters for Spanish stories. Create characters that will provide good language learning opportunities through dialogue and interaction.

Develop:
- Detailed main character profile (personality, background, motivations)
- 2-3 supporting characters with distinct personalities
- Clear relationships and dynamics between characters

Focus on creating characters that represent diverse aspects of Spanish-speaking cultures."""},
                {"role": "user", "content": f"""Story Details:
Title: {story_details.title}
Main Character: {story_details.main_character}
Setting: {story_details.setting}"""}
            ],
            temperature=0.6,
            max_tokens=800,
            response_format=StoryCharacters
        )
        
        return response.choices[0].message.parsed

    def _select_writing_style(self, story_details: StoryDetails, level: str) -> WritingStyle:
        """Choose appropriate writing style for the story and level"""
        
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""Select the most appropriate writing style for stories that will be effective for {level} level Spanish learners.

Choose:
- Writing style (narrative, descriptive, dialogue-heavy, etc.)
- Tone (warm, adventurous, reflective, humorous, etc.)
- Narrative voice (first person, third person, etc.)

Consider the CEFR level requirements:
- A1/A2: Simple, clear, repetitive structures
- B1/B2: More complex but accessible
- C1: Sophisticated but not overwhelming

Select styles that will enhance language learning while maintaining engagement."""},
                {"role": "user", "content": f"""Story Details:
Title: {story_details.title}
Theme: {story_details.theme}"""}
            ],
            temperature=0.4,
            max_tokens=400,
            response_format=WritingStyle
        )
        
        return response.choices[0].message.parsed

    def _create_plot_points(self, story_details: StoryDetails, structure: StoryStructure) -> PlotPoints:
        """Create specific plot points that drive the story forward"""
        structure_text = "\n".join([f"- {section}" for section in structure.structure])
        
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """Create specific plot points that will drive stories forward. Each plot point should:
- Advance the narrative toward the resolution
- Include opportunities for character development
- Provide natural language learning moments
- Build tension and engagement
- Include dialogue opportunities where appropriate

Create 6-8 specific plot points that will guide the story writing."""},
                {"role": "user", "content": f"""Story Details:
Title: {story_details.title}
Conflict: {story_details.conflict}
Resolution: {story_details.resolution}

Story Structure:
{structure_text}"""}
            ],
            temperature=0.6,
            max_tokens=800,
            response_format=PlotPoints
        )
        
        return response.choices[0].message.parsed

    def _create_outline(self, plot_points: PlotPoints, story_details: StoryDetails, 
                      world: StoryWorld, characters: StoryCharacters, 
                      style: WritingStyle, level: str) -> StoryOutline:
        """Create a detailed story outline incorporating all elements"""
        plot_text = "\n".join([f"- {point}" for point in plot_points.plot_points])
        
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""Create a detailed story outline that incorporates all story elements. The outline should:
- Follow the plot points in logical sequence
- Include specific scenes and dialogue opportunities
- Incorporate cultural elements naturally
- Ensure appropriate language complexity for {level} level
- Provide clear guidance for writing each section

Make the outline detailed enough to guide the actual story writing."""},
                {"role": "user", "content": f"""Story Details:
Title: {story_details.title}
Theme: {story_details.theme}
Setting: {story_details.setting}
Conflict: {story_details.conflict}
Resolution: {story_details.resolution}

Plot Points:
{plot_text}

World Elements:
- Description: {world.world_description}
- Cultural Elements: {', '.join(world.cultural_elements)}
- Atmosphere: {world.atmosphere}

Characters:
- Main: {characters.main_character}
- Supporting: {', '.join(characters.supporting_characters)}
- Relationships: {characters.character_relationships}

Writing Style:
- Style: {style.style}
- Tone: {style.tone}
- Voice: {style.narrative_voice}"""}
            ],
            temperature=0.5,
            max_tokens=2000,
            response_format=StoryOutline
        )
        
        return response.choices[0].message.parsed

    def _write_first_draft(self, outline: StoryOutline, level: str) -> StoryDraft:
        """Write the complete first draft of the story"""
        
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""You are an expert Spanish language educator and creative writer. Write complete, engaging Spanish stories based on outlines.

Requirements:
- Write entirely in Spanish
- Match the exact CEFR level specified ({level})
- Follow the outline structure precisely
- Include natural dialogue and cultural elements
- Use appropriate vocabulary and grammar for the level
- Create an engaging, educational story
- Word count: A1: 300-400, A2: 400-500, B1: 500-600, B2: 600-700, C1: 700-800
- DO NOT include section headers, chapter numbers, or structural markers (like "#### I. Introducción")
- Write as a continuous narrative without section headers or chapter numbers
- Format dialogue on separate lines with proper quotation marks

CEFR Level Guidelines:
{self._get_cefr_guidelines(level)}

Write a complete story that is both entertaining and pedagogically valuable for Spanish language learners."""},
                {"role": "user", "content": f"Story Outline:\n{outline.outline}"}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format=StoryDraft
        )
        
        return response.choices[0].message.parsed

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