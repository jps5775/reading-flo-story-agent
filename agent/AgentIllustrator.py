import os
import requests
from typing import Optional, List
from pydantic import BaseModel
from agent.AgentWriter.AgentWriterModels import FullStoryContext


class ImagePrompt(BaseModel):
    prompt: str
    insertion_point: str
    image_description: str


class ArtStyleSelection(BaseModel):
    selected_style: str
    style_justification: str


class KeyMomentsSelection(BaseModel):
    selected_moments: List[ImagePrompt]


class AgentIllustrator:
    def __init__(self, llm):
        self.llm = llm

    def illustrate_story(
        self, full_story_context: FullStoryContext, story_id: str
    ) -> None:
        """Generate images for a Spanish story and modify story-revised.txt"""
        print(f"Starting illustration process for story: {story_id}")

        # Step 1: Select art style
        print("Step 1: Selecting art style...")
        art_style = self._select_art_style(full_story_context)
        print(f"Selected art style: {art_style.selected_style}")

        # Step 2: Select key moments
        print("Step 2: Selecting key moments...")
        key_moments = self._select_key_moments(full_story_context, art_style)
        print(f"Selected {len(key_moments.selected_moments)} key moments")

        # Step 3: Generate images
        print("Step 3: Generating images...")
        self._generate_images(key_moments, story_id)

        # Step 4: Create illustrated story
        print("Step 4: Creating illustrated story...")
        self._create_illustrated_story(story_id, key_moments)

        print("Illustration process completed!")

    def _select_art_style(
        self, full_story_context: FullStoryContext
    ) -> ArtStyleSelection:
        """Select appropriate art style based on FullStoryContext"""
        available_art_styles = {
            "Watercolor illustration": "soft watercolor illustration with dreamy textures, gentle colors, and artistic brush strokes",
            "Digital children's book style": "clean and colorful digital children's book illustration, modern vector style, smooth lines, bright friendly palette",
            "Traditional children's book illustration": "classic hand-painted children's book illustration, warm colors, detailed characters, textured paper feel",
            "Minimalist illustration": "simple, clean, modern minimalist illustration with flat colors and lots of white space",
            "Folk art style": "traditional folk art style with handcrafted textures, bold colors, cultural motifs, and decorative patterns",
            "Realistic illustration": "highly detailed and lifelike illustration, natural lighting, photographic realism",
            "Cartoon/animated style": "fun and playful cartoon illustration with expressive characters, bold outlines, and vibrant colors",
            "Mixed media collage": "artistic mixed media collage with textured paper layers, cut-out shapes, and a handcrafted feel",
        }

        system_prompt = """You are an expert art director specializing in children's book illustration. Your task is to select the most appropriate art style for a Spanish story based on its context."""
        user_prompt = f"""
        [Context]
        AVAILABLE ART STYLES:
        {available_art_styles}

        Title: {full_story_context.story_idea.title}
        Description: {full_story_context.story_idea.description}
        Theme: {full_story_context.story_details.theme}
        Time Period: {full_story_context.story_details.time_period}
        Location: {full_story_context.story_details.location}
        CEFR Level: {full_story_context.level}

        World Description: {full_story_context.world.world_description}
        Cultural Elements: {full_story_context.world.cultural_elements}
        Atmosphere: {full_story_context.world.atmosphere}
        Writing Style: {full_story_context.style.style}
        Tone: {full_story_context.style.tone}

        [Instructions]
        Select the most appropriate art style for this Spanish story.

        [Rules]
        - Choose from the available art styles listed above
        - Consider the CEFR level and target audience
        - Match the story's mood, tone, and cultural elements
        - Provide clear justification for your choice

        [Output Format]
        Return the selected art style and justification.
        """
        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=500,
            response_format=ArtStyleSelection,
        )
        return response.choices[0].message.parsed

    def _select_key_moments(
        self, full_story_context: FullStoryContext, art_style: ArtStyleSelection
    ) -> KeyMomentsSelection:
        """Select key moments from PlotPoints for illustration"""
        plot_points_text = ""
        for plot_point in full_story_context.plot_points.all_plot_points:
            plot_points_text += f"Section: {plot_point.section_title}\n"
            for point in plot_point.section_plot_points:
                plot_points_text += f"- {point}\n"
            plot_points_text += "\n"

        system_prompt = """You are an expert visual storytelling specialist. Your task is to select the most compelling moments from a story's plot points that would benefit from illustration."""
        user_prompt = f"""
        [Context]
        Title: {full_story_context.story_idea.title}
        Selected Art Style: {art_style.selected_style}
        CEFR Level: {full_story_context.level}

        Plot Points:
        {plot_points_text}

        [Instructions]
        Select 3-5 key moments from the plot points that would make compelling illustrations.

        [Rules]
        - Choose moments that show key actions, settings, or emotional scenes
        - Ensure moments are distributed throughout the story (beginning, middle, end)
        - Create detailed image prompts using the selected art style
        - Include specific visual details: character appearance, setting, lighting, mood
        - Write prompts in English for optimal AI interpretation
        - Provide brief descriptions for each image

        [Output Format]
        Return the selected moments with detailed prompts and descriptions.
        """
        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=2000,
            response_format=KeyMomentsSelection,
        )
        return response.choices[0].message.parsed

    def _generate_images(self, key_moments: KeyMomentsSelection, story_id: str) -> None:
        """Generate images using DALL-E 3 API"""
        images_dir = f"agent-generated-stories/{story_id}/imgs"
        os.makedirs(images_dir, exist_ok=True)

        image_prompts: List[ImagePrompt] = key_moments.selected_moments

        for i, prompt_data in enumerate(image_prompts, 1):
            print(f"Generating image {i}/{len(image_prompts)}...")

            try:
                image_url = self._call_dalle_api(prompt_data.prompt)
                if image_url:
                    file_path = f"{images_dir}/image-{i}.png"
                    success = self._download_image(image_url, file_path)
                    if success:
                        print(f"✓ Image {i} generated and saved successfully")
                    else:
                        print(f"✗ Image {i} download failed")
                else:
                    print(f"✗ Image {i} generation failed")
            except Exception as e:
                print(f"✗ Image {i} failed with error: {str(e)}")

    def _call_dalle_api(self, prompt: str) -> Optional[str]:
        """Call DALL-E 3 API to generate image"""
        try:
            response = self.llm.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                response_format="url",
                n=1,
            )
            return response.data[0].url
        except Exception as e:
            print(f"DALL-E API error: {str(e)}")
            return None

    def _download_image(self, image_url: str, file_path: str) -> bool:
        """Download image from URL and save to file"""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            with open(file_path, "wb") as f:
                f.write(response.content)

            # Verify file was created and has content
            return os.path.exists(file_path) and os.path.getsize(file_path) > 0
        except Exception as e:
            print("Download error: " + str(e))
            return False

    def _create_illustrated_story(
        self, story_id: str, key_moments: KeyMomentsSelection
    ) -> None:
        """Modify story-revised.txt with image insertions"""
        story_dir = f"agent-generated-stories/{story_id}"
        revised_story_path = f"{story_dir}/story-revised.txt"
        images_dir = f"{story_dir}/imgs"

        if not os.path.exists(revised_story_path):
            print(f"Warning: {revised_story_path} not found.")
            return

        if not os.path.exists(images_dir):
            print(f"Warning: Images directory {images_dir} not found.")
            return

        # Read story and get images
        with open(revised_story_path, "r", encoding="utf-8") as f:
            story_text = f.read()

        paragraphs = [p.strip() for p in story_text.strip().split("\n\n") if p.strip()]
        image_files = sorted([f for f in os.listdir(images_dir) if f.endswith(".png")])

        if not image_files:
            print("No images found to insert.")
            return

        # Distribute images evenly with descriptions
        insertion_interval = max(1, len(paragraphs) // len(image_files))
        illustrated_parts = []
        image_index = 0

        for i, paragraph in enumerate(paragraphs):
            illustrated_parts.append(paragraph)
            if (i + 1) % insertion_interval == 0 and image_index < len(image_files):
                image_path = f"{images_dir}/{image_files[image_index]}"
                # Get the corresponding image description from the key moments
                if image_index < len(key_moments.selected_moments):
                    image_description = key_moments.selected_moments[
                        image_index
                    ].image_description
                else:
                    image_description = f"Story illustration {image_index + 1}"
                illustrated_parts.append(
                    f"\n\n[IMAGE: {image_path} | DESCRIPTION: {image_description}]\n"
                )
                image_index += 1

        # Write back to file
        with open(revised_story_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(illustrated_parts))

        print(f"Created illustrated story with {len(image_files)} images inserted")
