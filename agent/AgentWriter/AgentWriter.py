import os
import pickle
from .AgentWriterModels import (
    CharacterProfile,
    CharacterRelationship,
    Chunk,
    StoryIdea,
    StoryIdeaList,
    StoryDetails,
    StoryStructureList,
    StoryWorld,
    StoryCharacters,
    WritingStyle,
    PlotPoints,
    StoryOutline,
    StoryDraft,
    FullStoryContext,
    OutlineItem,
)


class AgentWriter:
    MAX_WORDS_PER_MAIN_SECTION = {
        "A1": 100,
        "A2": 150,
        "B1": 200,
        "B2": 250,
        "C1": 350,
    }

    DEEP_SUB_PLOT_POINTS_COUNT = {
        "A1": [1, 2],
        "A2": [1, 2],
        "B1": [2, 3],
        "B2": [2, 3],
        "C1": [3, 4],
    }

    def __init__(self, llm):
        self.llm = llm

    def generate_story(
        self, topic: str, level: str, story_id: str, directory_path: str
    ) -> FullStoryContext:
        """Orchestrates the complete story generation pipeline"""
        print(f"Starting story generation for topic: {topic}, level: {level}")

        full_story_context: FullStoryContext = FullStoryContext.create_default(level)

        # Step 1: Generate multiple story ideas
        story_ideas: StoryIdeaList = self._create_ideas(topic)
        print(f"Generated {len(story_ideas.all_ideas)} story ideas")

        # Step 2: Select the best idea
        selected_idea: StoryIdea = self._select_idea(story_ideas)
        print(f"Selected idea: {selected_idea.title} {selected_idea.description}")
        full_story_context.story_idea = selected_idea

        # Step 3: Create detailed story framework
        story_details: StoryDetails = self._create_story_details(full_story_context)
        print(f"Created story details: {story_details.theme}")
        full_story_context.story_details = story_details

        # Step 4: Build the story world
        world: StoryWorld = self._create_story_world(full_story_context)
        print("Created story world and cultural elements")
        full_story_context.world = world

        # Step 5: Develop characters
        characters: StoryCharacters = self._create_story_characters(full_story_context)
        print("Created characters and relationships")
        full_story_context.characters = characters

        # Step 6: Select writing style
        style: WritingStyle = self._select_writing_style(full_story_context)
        print(f"Selected writing style: {style.style}")
        full_story_context.style = style

        # Step 7: Define story structure
        structure: StoryStructureList = self._create_story_structure(full_story_context)
        print(f"Created story structure with {len(structure.all_sections)} sections")
        full_story_context.structure = structure

        # Step 8: Create plot points based on story structure
        plot_points: PlotPoints = self._create_plot_points(full_story_context)
        print(f"Created {len(plot_points.all_plot_points)} plot points")
        full_story_context.plot_points = plot_points

        # Step 9: Create detailed outline based on plot points
        outline: StoryOutline = self._create_outline(full_story_context)
        print("Created detailed story outline")
        full_story_context.outline = outline

        # Step 10: Write the first draft
        draft: StoryDraft = self._write_first_draft(full_story_context)
        draft.title = full_story_context.story_idea.title
        print(f"Completed first draft: {draft.title}")
        full_story_context.draft = draft

        print("--------------------------------")
        print(f"Full story context: {full_story_context.model_dump_json(indent=2)}")
        print("--------------------------------")

        # Save the story
        story_dir: str = f"{directory_path}/{story_id}"
        os.makedirs(story_dir, exist_ok=True)
        with open(f"{story_dir}/story.txt", "w", encoding="utf-8") as f:
            f.write(full_story_context.draft.story)

        return full_story_context

    def _create_ideas(self, topic: str) -> StoryIdeaList:
        """Generate multiple creative story ideas based on the topic"""

        system_prompt = """
            You are a creative Spanish story writer that can generate diverse, engaging story ideas that could be developed into 
            educational Spanish stories for language learners."""
        user_prompt = f"""
            [Context]
            Topic: {topic}

            [Instructions]
            I want you to create 5 different story ideas based on this topic: {topic}.
            
            [Rules]
            Each story must:
            - have conflict
            - have great character development
            - have potential for being made in the multipart series of stories
            - have a eye catching and interesting title

            [Output Format]
            Return 5 distinct story ideas with brief 1-2 sentence description for each.

            [Example Outputs]
            [
                {{
                    "title": "Aventura en el Castillo Encantado",
                    "description": "Sofía, una joven historiadora, es invitada a investigar un castillo aislado donde los objetos parecen cobrar vida. Allí, se enfrenta a un espíritu travieso que oculta un tesoro antiguo y se ve obligada a trabajar con un escéptico periodista para desentrañar la historia antes de que el castillo sea demolido."
                }},
                {{
                    "title": "Conspiración en Barcelona",
                    "description": "Eva Mendoza, experta en disfraces, persigue al villano 'El Ajedrecista', quien ha robado una joya con poderes legendarios. En Barcelona, Eva desentraña un complot peligroso mientras confronta un pasado amoroso complicado y su lealtad al servicio."
                }}
            ]
        """

        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=500,
            response_format=StoryIdeaList,
        )

        return response.choices[0].message.parsed

    def _select_idea(self, story_ideas: StoryIdeaList) -> StoryIdea:
        """Select the best story idea from the generated options"""

        ideas_context_text: str = ""
        for i, idea in enumerate(story_ideas.all_ideas):
            ideas_context_text += (
                f"{i + 1}. Title: {idea.title} Description: {idea.description}\n\n"
            )

        system_prompt = """You are an expert Spanish language educator that can select the best story idea from a list of options."""
        user_prompt = f"""
            [Context]
            {ideas_context_text}

            [Instructions]
            I want you to select the ONE story title and description that if turned into a full story, it would be the most interesting and fun to read for language learners.
            
            [Rules]
            - Choose only one title and description.
            - The title and description must be the most interesting and engaging for language learners to read.
            
            [Output Format]
            Return the selected title and description.
            
            [Example Output]
            {{
                "Title": "Aventura en el Castillo Encantado",
                "Description": "Sofía, una joven historiadora, es invitada a investigar un castillo aislado donde los objetos parecen cobrar vida. Allí, se enfrenta a un espíritu travieso que oculta un tesoro antiguo y se ve obligada a trabajar con un escéptico periodista para desentrañar la historia antes de que el castillo sea demolido."
            }}
        """

        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=500,
            response_format=StoryIdea,
        )

        return response.choices[0].message.parsed

    def _create_story_details(
        self, full_story_context: FullStoryContext
    ) -> StoryDetails:
        """Create comprehensive story details from the selected story"""

        system_prompt = f"""You are a expert Spanish language educator and story writer that can 
            create comprehensive story details for stories that will be appropriate for CEFR {full_story_context.level} Spanish language learners."""
        user_prompt = f"""
        [Context]
        Selected Story Title: {full_story_context.story_idea.title}
        Selected Story Description: {full_story_context.story_idea.description}

        [Instructions]
        I want you to create comprehensive story details for the selected story.

        [Rules]
        The story details should include the following elements:
        - It should include a theme (e.g. adventure, mystery, romance, etc.)
        - It should include a time period (e.g. modern day, roman times, futuristic, etc.)
        - It should include a specific location (e.g. Madrid, Barcelona, Rome, etc.)
        - It should include a main character with clear motivation
        - It should include a central conflict that drives the story
        - It should include a resolution that resolves the conflict
        - It should be appropriate for CEFR {full_story_context.level} Spanish language learners.

        [Output Format]
        Return the story details with the following fields:
        - theme: str
        - time_period: str
        - location: str
        - main_character: str
        - conflict: str
        - resolution: str

        [Example Output]
        {{
            "theme": "Aventura y misterio",
            "time_period": "Época moderna",
            "location": "Toledo, España",
            "main_character": "Marcos, un joven bibliotecario apasionado por los libros y la historia. Su motivación es proteger la biblioteca y sus secretos, además de vivir una aventura única.",
            "conflict": "Marcos descubre un pasadizo secreto en la biblioteca que lo lleva a un mundo alternativo donde los personajes de los libros cobran vida. Sin embargo, un villano literario, el malvado Capitán Garfio, escapa de su libro y amenaza con destruir el mundo real y el mundo alternativo. Marcos debe encontrar aliados entre los personajes literarios para detener al villano y salvar ambos mundos.",
            "resolution": "Marcos, con la ayuda de personajes como Don Quijote y Sherlock Holmes, elabora un plan astuto para engañar al Capitán Garfio y devolverlo a su libro. Al final, Marcos logra cerrar el pasadizo secreto, asegurando que los mundos permanezcan seguros, y descubre que la verdadera magia de los libros está en las historias que cuentan y las lecciones que enseñan."
        }}
        """

        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=800,
            response_format=StoryDetails,
        )

        return response.choices[0].message.parsed

    def _create_story_structure(
        self, full_story_context: FullStoryContext
    ) -> StoryStructureList:
        """Define the narrative structure for the story as a list of sections"""

        system_prompt = f"""
        You are a expert Spanish language story writer and can create narrative 
        structure for stories that will be appropriate for CEFR {full_story_context.level} Spanish language learners."""
        user_prompt = f"""
        [Context]
        Title: {full_story_context.story_idea.title}
        Description: {full_story_context.story_idea.description}
        Theme: {full_story_context.story_details.theme}
        Time Period: {full_story_context.story_details.time_period}
        Location: {full_story_context.story_details.location}
        Main Character: {full_story_context.story_details.main_character}
        Conflict: {full_story_context.story_details.conflict}
        Resolution: {full_story_context.story_details.resolution}

        World Description: {full_story_context.world.world_description}
        Time Period Description: {full_story_context.world.time_period_description}
        Struggles and Challenges of the World: {full_story_context.world.struggles_and_challenges}
        Cultural Elements: {full_story_context.world.cultural_elements}
        Atmosphere: {full_story_context.world.atmosphere}

        Main Character: {full_story_context.characters.main_character}
        Supporting Characters: {full_story_context.characters.supporting_characters}
        Villain: {full_story_context.characters.villain}
        Character Relationships: {full_story_context.characters.character_relationships}

        Writing Style: {full_story_context.style.style}
        Tone: {full_story_context.style.tone}
        Narrative Voice: {full_story_context.style.narrative_voice}

        [Instructions]
        I want you to create a narrative structure for the provided story details. Define
        6 main sections with 2 - 3 sentence descriptions of each section that will guide the story's progression.

        [Rules]
        Each section should:
        - Advance the plot logically and engagingly
        - Include character development
        - Focus on building up the conflict and tension as the story progresses towards the climax
        - Be appropriate for CEFR {full_story_context.level} Spanish language learners.

        [Output Format]
        Return the section titles and descriptions.

        [Example Output]
        {{
            {{
                "section_title": "El Robo de la Joya Sagrada",
                "section_description": [
                    "Introducción a Lucía y su misión.",
                    "Descripción del robo en la catedral.",
                    "Primera pista: un símbolo antiguo dejado por 'El Peregrino'."
                ]
            }},
            {{
                "section_title": "Primeros Pasos en el Camino",
                "section_description": [
                    "Lucía inicia su viaje por el Camino de Santiago.",
                    "Encuentros con peregrinos que ofrecen pistas y leyendas.",
                    "Descubrimiento de un códice antiguo que menciona la joya."
                ]
            }},
            {{
                "section_title": "El Enigma de los Códices",
                "section_description": [
                    "Lucía descifra los primeros códices.",
                    "Revelación de un mapa oculto que lleva a un monasterio.",
                    "Desarrollo de la conexión personal de Lucía con el camino."
                ]
            }},
            {{
                "section_title": "Trampas y Revelaciones",
                "section_description": [
                    "Lucía enfrenta trampas dejadas por 'El Peregrino'.",
                    "Encuentro con un aliado inesperado que conoce su legado familiar.",
                    "Nueva pista: un manuscrito que habla de rituales de inmortalidad."
                ]
            }},
            {{
                "section_title": "El Enfrentamiento en el Monasterio",
                "section_description": [
                    "Lucía llega al antiguo monasterio.",
                    "Confrontación directa con 'El Peregrino'.",
                    "Uso de inteligencia y valentía para superar obstáculos."
                ]
            }},
            {{
                "section_title": "El Legado Revelado",
                "section_description": [
                    "Lucía recupera la joya sagrada.",
                    "Descubrimiento del papel de sus antepasados como guardianes del camino.",
                    "Reflexión sobre su conexión personal y nuevo propósito."
                ]
            }},
            {{
                "section_title": "Regreso y Nuevo Comienzo",
                "section_description": [
                    "Lucía regresa con la joya a la catedral.",
                    "Reconocimiento de su éxito y legado.",
                    "Preparación para futuras aventuras con un renovado sentido de identidad."
                ]
            }}
        }}
        """

        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=1200,
            response_format=StoryStructureList,
        )

        return response.choices[0].message.parsed

    def _create_story_world(self, full_story_context: FullStoryContext) -> StoryWorld:
        """Build the cultural and environmental context for the story"""

        system_prompt = """
        You are an Expert Spanish language story writer that can create rich, culturally authentic world for Spanish stories.
        """
        user_prompt = f"""
        [Context]
        Title: {full_story_context.story_idea.title}
        Description: {full_story_context.story_idea.description}
        Theme: {full_story_context.story_details.theme}
        Time Period: {full_story_context.story_details.time_period}
        Location: {full_story_context.story_details.location}
        Main Character: {full_story_context.story_details.main_character}
        Conflict: {full_story_context.story_details.conflict}
        Resolution: {full_story_context.story_details.resolution}

        [Instructions]
        I want you to create a rich, culturally authentic world for the provided story details.

        [Rules]
        The world should include the following elements:
        - Detailed world description (sights, sounds, smells, emotions, etc.)
        - Detailed time period description (e.g. modern day, roman times, futuristic, etc.)
        - Struggles and challenges of the world (e.g. war, poverty, social injustice, etc.)
        - Specific cultural elements (foods, traditions, customs, expressions, etc.)
        - Overall atmosphere and mood

        [Output Format]
        Return the 1-2 sentences of each element: world description, time period description, struggles and challenges of the world, cultural elements, and atmosphere.

        [Example Output]
        {{
            "world_description": "El Camino de Santiago serpentea a través de verdes paisajes gallegos, donde el aroma a eucalipto se mezcla con el eco de antiguas campanas de iglesias. Los pueblos de piedra, con sus plazas empedradas, vibran con el murmullo de peregrinos compartiendo historias al calor del fuego en albergues acogedores.",
            "time_period_description": "Época moderna, donde la tecnología convive con la historia; los peregrinos llevan mochilas ligeras y teléfonos inteligentes para navegar, pero aún sienten la presencia de siglos de tradición y espiritualidad en cada paso.",
            "struggles_and_challenges": "El pulpo a la gallega y la tarta de Santiago son platos emblemáticos que los peregrinos disfrutan en tabernas rústicas. Las fiestas del Apóstol Santiago en Compostela, con sus procesiones y fuegos artificiales, celebran la llegada de los peregrinos. Expresiones como '¡Buen Camino!' resuenan a lo largo de la travesía.",
            "cultural_elements": "El pulpo a la gallega y la tarta de Santiago son platos emblemáticos que los peregrinos disfrutan en tabernas rústicas. Las fiestas del Apóstol Santiago en Compostela, con sus procesiones y fuegos artificiales, celebran la llegada de los peregrinos. Expresiones como "¡Buen Camino!" resuenan a lo largo de la travesía.",
            "atmosphere": "La atmósfera es de misterio y reverencia, donde cada camino esconde secretos y cada encuentro ofrece una conexión inesperada. Hay una sensación de búsqueda y descubrimiento, tanto personal como histórico, que envuelve a Lucía en su misión."
        }}
        """

        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=700,
            response_format=StoryWorld,
        )

        return response.choices[0].message.parsed

    def _create_story_characters(
        self, full_story_context: FullStoryContext
    ) -> StoryCharacters:
        """Develop detailed character profiles and relationships"""

        system_prompt = """You are an Expert Spanish language story writer that can create rich, interesting, and authentic characters for Spanish stories."""
        user_prompt = f"""
        [Context]
        Title: {full_story_context.story_idea.title}
        Description: {full_story_context.story_idea.description}
        Time Period: {full_story_context.story_details.time_period}
        Location: {full_story_context.story_details.location}
        Main Character: {full_story_context.story_details.main_character}
        Conflict: {full_story_context.story_details.conflict}
        Resolution: {full_story_context.story_details.resolution}

        World Description: {full_story_context.world.world_description}
        Time Period Description: {full_story_context.world.time_period_description}
        Struggles and Challenges of the World: {full_story_context.world.struggles_and_challenges}
        Cultural Elements: {full_story_context.world.cultural_elements}
        Atmosphere: {full_story_context.world.atmosphere}

        [Instructions]
        I want you to create a rich, interesting, and authentic characters for the provided story details.

        [Rules]
        The characters should include the following elements:
        - Names should be 2-3 words long and should be unique.
        - Each Character Profile should contain 1 sentence description for the personality, background, motivations, and appearance.
        - Include 2-3 supporting characters.
        - Include 1 villain character.
        - Clear relationships and dynamics between characters.

        [Output Format]
        Return the character profiles for the main character, supporting characters, and villain character, and character relationships.
        """

        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=1000,
            response_format=StoryCharacters,
        )

        return response.choices[0].message.parsed

    def _select_writing_style(
        self, full_story_context: FullStoryContext
    ) -> WritingStyle:
        """Choose appropriate writing style for the story and level"""

        system_prompt = f"""You are an Expert Spanish language story writer that can select the most appropriate writing 
        style for stories that will be effective for CEFR {full_story_context.level} Spanish language learners."""
        user_prompt = f"""
        [Context]
        Title: {full_story_context.story_idea.title}
        Description: {full_story_context.story_idea.description}
        Theme: {full_story_context.story_details.theme}
        Time Period: {full_story_context.story_details.time_period}
        Location: {full_story_context.story_details.location}
        Main Character: {full_story_context.story_details.main_character}
        Conflict: {full_story_context.story_details.conflict}
        Resolution: {full_story_context.story_details.resolution}

        World Description: {full_story_context.world.world_description}
        Time Period Description: {full_story_context.world.time_period_description}
        Struggles and Challenges of the World: {full_story_context.world.struggles_and_challenges}
        Cultural Elements: {full_story_context.world.cultural_elements}
        Atmosphere: {full_story_context.world.atmosphere}

        Main Character: {full_story_context.characters.main_character}
        Supporting Characters: {full_story_context.characters.supporting_characters}
        Villain: {full_story_context.characters.villain}
        Character Relationships: {full_story_context.characters.character_relationships}

        [Instructions]
        I want you to select the most appropriate writing style for the provided story details.

        [Rules]
        The writing style should include the following elements:
        - Select the most appropriate Writing style (narrative, descriptive, dialogue-heavy, etc.)
        - Select the most appropriate Tone (warm, adventurous, reflective, humorous, etc.)
        - Select the most appropriate Narrative voice (first person, third person, etc.)

        [Output Format]
        Return the writing style, tone, and narrative voice.

        [Example Output]
        {{
            "style": "narrative",
            "tone": "warm",
            "narrative_voice": "first person"
        }}
        """

        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=500,
            response_format=WritingStyle,
        )

        return response.choices[0].message.parsed

    def _create_plot_points(self, full_story_context: FullStoryContext) -> PlotPoints:
        system_prompt = """You are an Expert Spanish language story writer that can create specific plot points that will drive stories forward."""
        user_prompt = f"""
        [Context]
        Title: {full_story_context.story_idea.title}
        Description: {full_story_context.story_idea.description}
        Theme: {full_story_context.story_details.theme}
        Time Period: {full_story_context.story_details.time_period}
        Location: {full_story_context.story_details.location}
        Main Character: {full_story_context.story_details.main_character}
        Conflict: {full_story_context.story_details.conflict}
        Resolution: {full_story_context.story_details.resolution}

        World Description: {full_story_context.world.world_description}
        Time Period Description: {full_story_context.world.time_period_description}
        Struggles and Challenges of the World: {
            full_story_context.world.struggles_and_challenges
        }
        Cultural Elements: {full_story_context.world.cultural_elements}
        Atmosphere: {full_story_context.world.atmosphere}

        Main Character: {full_story_context.characters.main_character}
        Supporting Characters: {full_story_context.characters.supporting_characters}
        Villain: {full_story_context.characters.villain}
        Character Relationships: {full_story_context.characters.character_relationships}

        Writing Style: {full_story_context.style.style}
        Tone: {full_story_context.style.tone}
        Narrative Voice: {full_story_context.style.narrative_voice}

        Story Structure: {full_story_context.structure.all_sections}

        [Instructions]
        I want you to create 2 plot points based on each section in the story structure that will drive the story forward.

        [Rules]
        The plot points should include the following elements:
        - Advance the narrative toward the climax and resolution
        - Include character development and growth
        - Build up tension towards the climax and involve conflict between characters and story elements
        - Include dialogue opportunities between characters

        [Output Format]
        Return the plot points for each section in the story structure.

        [Example Output]
        {{
            "all_plot_points": [
                {{
                    "section_title": "La Misión en Granada",
                    "section_plot_points": [
                        "Inicio de la Misión: Javier es convocado a una reunión secreta en la sede del Servicio de Inteligencia Española. El director le entrega un dossier sobre 'El Espectro' y le recuerda que esta misión es su oportunidad para redimir su reputación. Javier acepta con determinación, pensando en su último fracaso.",
                        "Preparativos y Reflexiones: Antes de partir a Granada, Javier reflexiona sobre lo que está en juego. En un diálogo interno, se compromete a no dejarse vencer por el pasado. Esto establece su motivación para la misión y su deseo de restaurar su honor."
                    ]
                }},
                {{
                    "section_title": "Encuentros y Alianzas",
                    "section_plot_points": [
                        "Reunión con Sofía: Al llegar a Granada, Javier se encuentra con Sofía en un café cerca de la Alhambra. En un diálogo inicial, Sofía comparte su entusiasmo por la historia del lugar y expresa su deseo de proteger sus secretos. Esta reunión sella su alianza.",
                        "Encuentro con Carlos: Javier se reúne con Carlos en un bar local. A pesar de la calidez inicial, Javier nota una mirada esquiva en Carlos cuando menciona la misión. Este encuentro siembra las primeras semillas de desconfianza."
                    ]
                }},
                {{
                    "section_title": "Las Pistas del Espectro",
                    "section_plot_points": [
                        "Descubrimiento de la Primera Pista: Javier y Sofía encuentran un pergamino antiguo escondido en un rincón olvidado de la Alhambra. Mientras lo descifran, Javier se ve obligado a confrontar un recuerdo de su infancia relacionado con su familia, añadiendo una capa personal al misterio.",
                        "Tensión Creciente: A medida que avanzan por la Alhambra siguiendo las pistas, Javier y Sofía tienen un diálogo tenso sobre la importancia de la misión y cómo cada pista parece estar diseñada para desafiar a Javier personalmente. Esto aumenta la presión sobre él."
                    ]
                }},
                {{
                    "section_title": "Traiciones y Revelaciones",
                    "section_plot_points": [
                        "Revelación de Carlos: Javier descubre pruebas de que Carlos ha estado pasando información a 'El Espectro'. Enfrenta a Carlos en un tenso diálogo, donde Carlos confiesa su ambición y justifica sus acciones. Este conflicto lleva a Javier a reevaluar sus alianzas.",
                        "Alianza con María: Después de la traición de Carlos, Javier y Sofía encuentran a María, quien les ofrece información crucial sobre un pasaje secreto en la Alhambra. En un diálogo cauteloso, María revela su propio interés en proteger el legado familiar."
                    ]
                }},
                {{
                    "section_title": "El Enigma Final",
                    "section_plot_points": [
                        "Descifrado del Enigma: Con la ayuda de Sofía y María, Javier finalmente descifra el último enigma que los lleva al escondite de la joya. En un momento de epifanía, Javier conecta todas las pistas y comprende la verdadera intención de 'El Espectro'.",
                        "Confrontación Final: En una confrontación climática, Javier enfrenta a 'El Espectro' en un duelo de ingenios. Utilizando su astucia y conocimientos adquiridos, Javier logra capturar al villano en un intercambio de palabras lleno de tensión y astucia."
                    ]
                }},
                {{
                    "section_title": "La Reconciliación y el Triunfo",
                    "section_plot_points": [
                        "Restauración del Honor: Javier regresa al Servicio de Inteligencia con la joya recuperada. En un diálogo con el director, se le felicita por su éxito y se le asegura que su reputación ha sido restaurada, lo que le proporciona una sensación de logro personal.",
                        "Reconciliación Familiar: Javier descubre la verdad detrás de los secretos familiares revelados durante la misión. En un emotivo diálogo con Sofía, comparte su nuevo entendimiento y la paz que ha encontrado, cerrando así un capítulo importante de su vida."
                    ]
                }},
            ]
        }}

        """

        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=1500,
            response_format=PlotPoints,
        )

        return response.choices[0].message.parsed

    def _create_outline(self, full_story_context: FullStoryContext) -> StoryOutline:
        """Create a detailed story outline incorporating all elements"""

        main_plot_points = [
            plot_point.section_title
            for plot_point in full_story_context.plot_points.all_plot_points
        ]
        sub_plot_points = [
            plot_point.section_plot_points
            for plot_point in full_story_context.plot_points.all_plot_points
        ]

        plot_points_str = ""
        for i in range(len(main_plot_points)):
            plot_points_str += f"Main Plot Point: {main_plot_points[i]}\n"
            for sub_plot_point in sub_plot_points[i]:
                plot_points_str += f"Sub Plot Point: {sub_plot_point}\n"
            plot_points_str += "\n"

        system_prompt = """You are an Expert Spanish language story writer that can create a detailed story outline that will guide story writing."""
        user_prompt = f"""
        [Context]
        Title: {full_story_context.story_idea.title}
        Description: {full_story_context.story_idea.description}
        Theme: {full_story_context.story_details.theme}
        Time Period: {full_story_context.story_details.time_period}
        Location: {full_story_context.story_details.location}
        Main Character: {full_story_context.story_details.main_character}
        Conflict: {full_story_context.story_details.conflict}
        Resolution: {full_story_context.story_details.resolution}

        World Description: {full_story_context.world.world_description}
        Time Period Description: {full_story_context.world.time_period_description}
        Struggles and Challenges of the World: {full_story_context.world.struggles_and_challenges}
        Cultural Elements: {full_story_context.world.cultural_elements}
        Atmosphere: {full_story_context.world.atmosphere}

        Main Character: {full_story_context.characters.main_character}
        Supporting Characters: {full_story_context.characters.supporting_characters}
        Villain: {full_story_context.characters.villain}
        Character Relationships: {full_story_context.characters.character_relationships}

        Writing Style: {full_story_context.style.style}
        Tone: {full_story_context.style.tone}
        Narrative Voice: {full_story_context.style.narrative_voice}

        All Plot Points:
        {plot_points_str}

        [Instructions]
        I want you to create a detailed story outline using the story context provided. This outline will be used to guide the story writing in final draft.

        [Rules]
        The outline should include the following elements:
        - Read all the context provided and use it to guide your creation of the outline.
        - For each already provided sub plot point you must develop at least {self.DEEP_SUB_PLOT_POINTS_COUNT[full_story_context.level][0]} to {self.DEEP_SUB_PLOT_POINTS_COUNT[full_story_context.level][1]} deep sub plot points to guide the story writing in final draft.
        - The outline should be detailed and comprehensive so that the story writing in final draft can be followed easily.
        - The outline should follow the characters, world, conflicts, location, and story that is provided in the context so that the story is cohesive and coherent.

        [Output Format]
        Return the story outline.
        """

        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=7000,
            response_format=StoryOutline,
        )

        return response.choices[0].message.parsed

    # def _write_first_draft(self, full_story_context: FullStoryContext) -> StoryDraft:
    #     """Write the complete first draft of the story"""

    #     word_length = {
    #         "A1": (300, 600),
    #         "A2": (600, 900),
    #         "B1": (900, 1200),
    #         "B2": (1200, 1500),
    #         "C1": (1500, 2000),
    #     }[full_story_context.level]
    #     system_prompt = """You are an expert Spanish language creative writer and can write complete, engaging Spanish stories based on outlines."""
    #     user_prompt = f"""
    #     [Context]
    #     Title: {full_story_context.story_idea.title}
    #     Description: {full_story_context.story_idea.description}
    #     Theme: {full_story_context.story_details.theme}
    #     Time Period: {full_story_context.story_details.time_period}
    #     Location: {full_story_context.story_details.location}
    #     Main Character: {full_story_context.story_details.main_character}
    #     Conflict: {full_story_context.story_details.conflict}
    #     Resolution: {full_story_context.story_details.resolution}

    #     World Description: {full_story_context.world.world_description}
    #     Time Period Description: {full_story_context.world.time_period_description}
    #     Struggles and Challenges of the World: {full_story_context.world.struggles_and_challenges}
    #     Cultural Elements: {full_story_context.world.cultural_elements}
    #     Atmosphere: {full_story_context.world.atmosphere}

    #     Main Character: {full_story_context.characters.main_character}
    #     Supporting Characters: {full_story_context.characters.supporting_characters}
    #     Villain: {full_story_context.characters.villain}
    #     Character Relationships: {full_story_context.characters.character_relationships}

    #     Writing Style: {full_story_context.style.style}
    #     Tone: {full_story_context.style.tone}
    #     Narrative Voice: {full_story_context.style.narrative_voice}

    #     Story Outline: {full_story_context.outline.outline}

    #     [Instructions]
    #     I want you to write the complete first draft of the story based on the outline provided.

    #     [Rules]
    #     The story should include the following elements:
    #     - Write entirely in Spanish
    #     - Adjust your vocabulary and grammar to match the exact CEFR level specified ({full_story_context.level})
    #     - Follow the outline structure and elaborate on each of the sections to make sure you cover all the sub plot points and main plot points.
    #     - Include natural dialogue
    #     - Format dialogue on separate lines with proper quotation marks
    #     - The word length of the entire story should be between {word_length[full_story_context.level][0]} and {word_length[full_story_context.level][1]} words.
    #     - Write as a continuous narrative without section headers or chapter numbers
    #     - You can use the context provided to help with choosing writing style, tone, and narrative voice, or any other details that you think are relevant to the story.

    #     [Output Format]
    #     Return the complete first draft of the story.
    #     """

    #     response = self.llm.chat.completions.parse(
    #         model="gpt-4o",
    #         messages=[
    #             {"role": "system", "content": system_prompt},
    #             {"role": "user", "content": user_prompt},
    #         ],
    #         temperature=0.7,
    #         max_tokens=10000,
    #         response_format=StoryDraft,
    #     )

    #     return response.choices[0].message.parsed

    def _write_first_draft(self, full_story_context: FullStoryContext) -> StoryDraft:
        """Writes the complete first draft of the story"""

        story_draft: StoryDraft = StoryDraft(title="", story="")
        prev_summary: Chunk = Chunk(data="")
        for i, outline_item in enumerate(full_story_context.outline.outline):
            [written_section, summary] = self._write_story_section(
                outline_item, prev_summary, full_story_context
            )
            print(
                f"Completed section {i + 1} of {len(full_story_context.outline.outline)}"
            )
            story_draft.story += written_section.data + "\n"
            prev_summary = summary
            full_story_context.summary += f"Section {i + 1}: {summary.data}\n\n"
        return story_draft

    def _write_story_section(
        self,
        outline_item: OutlineItem,
        prev_summary: Chunk,
        full_story_context: FullStoryContext,
    ) -> tuple[Chunk, Chunk]:
        """Writes a story section based on the outline item"""

        main_plot_point = outline_item.main_section_title
        sub_plot_points = [
            ssp.sub_section_point for ssp in outline_item.sub_section_points
        ]
        plot_outline_str = f"Main Plot Point: {main_plot_point}\nSub Plot Points:\n"
        for sub_plot_point in sub_plot_points:
            plot_outline_str += f"-{sub_plot_point}:\n"

        # LLM call to write story section
        system_prompt = """You are an expert Spanish language creative writer that can write story sections based on the outline item."""
        user_prompt = f"""
        [Context]
        Full Story Context:
        {full_story_context.model_dump_json(indent=2)}
        
        Previous Summary: {prev_summary.data}

        Outline Item:
        {plot_outline_str}

        [Instructions]
        I want you to write the story for the given outline item.
        
        [Rules]
        - Write entirely in Spanish
        - Use the previous summary to understand the context of the story so far and continue the story from there.
        - Take each Deep Sub Plot Point from the outline item and write your paragraphs for the story based on them.
        - Make sure to cover all the Deep Sub Plot Points for the outline item.
        - The maximum number of words for the main section should not exceed {self.MAX_WORDS_PER_MAIN_SECTION[full_story_context.level]}.
        - Adjust your vocabulary and grammar to match the exact CEFR level specified ({full_story_context.level})
        - Include natural dialogue
        - Format dialogue on separate lines with proper quotation marks
        - Do NOT include any section headers or chapter numbers in the story.
        - You can use the context provided to help with choosing writing style, tone, and narrative voice, or any other details that you think are relevant to the story.
        """
        # - Aim for 1-3 paragraphs for each Deep Sub Plot Point.
        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=10000,
            response_format=Chunk,
        )

        written_section: Chunk = response.choices[0].message.parsed

        # LLM call to summarize written section for context on next section
        summary: Chunk = self._summarize_story_section(written_section)

        print("--------------------------------")
        print("Summarizing story section")
        print("Outline Item:")
        print(f"main section title: {outline_item.main_section_title}")
        print("sub section points and deep sub section points:")
        for idx, sub_section in enumerate(outline_item.sub_section_points):
            print(f"  Sub Section Point {idx + 1}: {sub_section.sub_section_point}")
            for jdx, deep_sub in enumerate(sub_section.deep_sub_section_points):
                print(f"    Deep Sub Section Point {jdx + 1}: {deep_sub}")
            print()
        print("--------------------------------")
        print(f"Written Section: {written_section.data}")
        print("--------------------------------")
        print(f"Summary: {summary.data}")
        print("--------------------------------")
        print()
        print()

        # return written section and summary
        return (written_section, summary)

    def _summarize_story_section(self, section: Chunk) -> Chunk:
        system_prompt = """You are an expert Spanish language creative writer that can summarize a story sections into a few sentences."""
        user_prompt = f"""
        [Context]
        Story Section: {section.data}

        [Instructions]
        I want you to summarize the story section into a few sentences.

        [Rules]
        - Summarize the story section into a few sentences.
        - Keep the most important details and events of the story section.
        - The summary should be in Spanish.
        """
        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=1000,
            response_format=Chunk,
        )
        return response.choices[0].message.parsed
