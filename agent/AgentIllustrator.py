import os
import requests
import json
from typing import Optional
from pydantic import BaseModel
from agent.AgentWriter import EntireStoreContext

class ImagePrompt(BaseModel):
    prompt: str
    scene_description: str
    moment_justification: str
    insertion_point: str  # Where in the story this image should be placed
    image_description: str  # Description to show under the image

class ImageGenerationResult(BaseModel):
    image_number: int
    prompt: str
    image_url: Optional[str] = None
    file_path: Optional[str] = None
    status: str  # "success", "failed", "pending"
    error_message: Optional[str] = None
    insertion_point: str
    image_description: str

class StoryContext(BaseModel):
    story_summary: str
    key_moments: list[str]
    cultural_elements: list[str]
    target_audience: str
    mood_and_tone: str
    visual_themes: list[str]

class ArtStyleSelection(BaseModel):
    selected_style: str
    style_justification: str
    visual_consistency_notes: str

class StoryAnalysis(BaseModel):
    story_summary: str
    selected_moments: list[ImagePrompt]
    cultural_elements: list[str]
    art_style: str
    target_audience: str

class IllustrationResults(BaseModel):
    story_id: str
    total_images: int
    successful_images: int
    failed_images: int
    image_results: list[ImageGenerationResult]
    summary: str

class AgentIllustrator:
    def __init__(self, llm):
        self.llm = llm

    def illustrate_story(self, story_path: str, entire_story_context: EntireStoreContext, story_id: str) -> IllustrationResults:
        """
        Main method to generate images for a Spanish story using three-step process
        """
        print(f"Starting illustration process for story: {story_id}")
        
        # Read story from file
        story_data = self._read_story(story_path)
        
        # Step 1: Analyze story context
        print("Step 1: Analyzing story context...")
        story_context = self._analyze_story_context(story_data, entire_story_context)
        print(f"Extracted {len(story_context.key_moments)} key moments")
        
        # Step 2: Select art style
        print("Step 2: Selecting art style...")
        art_style = self._select_art_style(story_context)
        print(f"Selected art style: {art_style.selected_style}")
        
        # Step 3: Generate image prompts
        print("Step 3: Generating image prompts...")
        analysis = self._generate_image_prompts(story_data, story_context, art_style, entire_story_context)
        print(f"Generated {len(analysis.selected_moments)} image prompts")
        
        # Create images directory
        images_dir = f"agent-generated-stories/{story_id}/imgs"
        os.makedirs(images_dir, exist_ok=True)
        
        # Generate images
        results = self._generate_images(analysis, images_dir, story_id)
        
        # Create summary
        summary = self._create_summary(analysis, results)
        
        return IllustrationResults(
            story_id=story_id,
            total_images=len(analysis.selected_moments),
            successful_images=results.successful_images,
            failed_images=results.failed_images,
            image_results=results.image_results,
            summary=summary
        )

    def _read_story(self, story_path: str) -> str:
        """Read story from file"""
        with open(story_path, "r", encoding="utf-8") as f:
            return f.read()

    def _analyze_story_context(self, story_data: str, entire_story_context: EntireStoreContext) -> StoryContext:
        """Step 1: Analyze story and extract key context for art style selection"""
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You are an expert story analyst specializing in Spanish children's literature. Your task is to analyze a story and extract key contextual information that will help determine the most appropriate art style for illustrations.

ANALYSIS TASKS:
1. Create a concise story summary
2. Identify 3-5 key narrative moments that would benefit from illustration
3. Extract cultural elements and themes
4. Determine target audience and reading level
5. Analyze mood, tone, and atmosphere
6. Identify visual themes and motifs

OUTPUT REQUIREMENTS:
- Story summary: 2-3 sentences capturing the essence
- Key moments: Brief descriptions of pivotal scenes
- Cultural elements: Spanish/Latin American cultural aspects
- Target audience: Age range and reading level
- Mood and tone: Emotional atmosphere of the story
- Visual themes: Recurring visual elements or motifs

Focus on providing rich context that will help select the most appropriate art style for this specific story."""},
                {"role": "user", "content": f"""STORY TO ANALYZE:
{story_data}

STORY CONTEXT:
Title: {entire_story_context.title}
World: {entire_story_context.world.world_description}
Cultural Elements: {', '.join(entire_story_context.world.cultural_elements)}
Atmosphere: {entire_story_context.world.atmosphere}
Characters: {entire_story_context.characters.main_character}
Style: {entire_story_context.style.style} - {entire_story_context.style.tone}"""}
            ],
            temperature=0.6,
            max_tokens=1500,
            response_format=StoryContext
        )
        return response.choices[0].message.parsed

    def _select_art_style(self, story_context: StoryContext) -> ArtStyleSelection:
        """Step 2: Select appropriate art style based on story context"""
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You are an expert art director specializing in children's book illustration. Your task is to select the most appropriate art style for a Spanish story based on its context.

AVAILABLE ART STYLES:
- Watercolor illustration (soft, dreamy, artistic)
- Digital children's book style (clean, colorful, modern)
- Traditional children's book illustration (classic, warm, detailed)
- Minimalist illustration (simple, clean, modern)
- Folk art style (traditional, cultural, handcrafted)
- Realistic illustration (detailed, lifelike, photographic)
- Cartoon/animated style (fun, playful, expressive)
- Mixed media collage (textured, layered, artistic)

SELECTION CRITERIA:
- Match the story's mood and tone
- Appeal to the target audience
- Complement cultural elements
- Support visual themes
- Ensure consistency across all illustrations

Provide:
1. Selected art style with specific details
2. Clear justification for the choice
3. Notes on maintaining visual consistency

Choose the style that will best serve the story and its readers."""},
                {"role": "user", "content": f"""STORY CONTEXT:
Summary: {story_context.story_summary}
Key Moments: {', '.join(story_context.key_moments)}
Cultural Elements: {', '.join(story_context.cultural_elements)}
Target Audience: {story_context.target_audience}
Mood and Tone: {story_context.mood_and_tone}
Visual Themes: {', '.join(story_context.visual_themes)}"""}
            ],
            temperature=0.7,
            max_tokens=800,
            response_format=ArtStyleSelection
        )
        return response.choices[0].message.parsed

    def _generate_image_prompts(self, story_data: str, story_context: StoryContext, art_style: ArtStyleSelection, entire_story_context: EntireStoreContext) -> StoryAnalysis:
        """Step 3: Generate detailed image prompts using selected art style"""
        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""You are an expert visual storytelling specialist with deep expertise in Spanish language and culture, children's literature illustration, and AI image generation. Your role is to create compelling, culturally-appropriate image prompts using the pre-selected art style.

SELECTED ART STYLE: {art_style.selected_style}
STYLE JUSTIFICATION: {art_style.style_justification}
VISUAL CONSISTENCY NOTES: {art_style.visual_consistency_notes}

TASK:
1. Use the key moments from the story analysis
2. Create detailed image prompts for each moment using the selected art style
3. Determine optimal insertion points in the story for each image
4. Create descriptive captions for each image
5. Ensure cultural authenticity and visual consistency

REQUIREMENTS FOR IMAGE PROMPTS:
- Use the selected art style consistently across all prompts
- Capture pivotal moments in the story's progression
- Include specific visual details: character appearance, setting elements, lighting, mood
- Reflect authentic Spanish/Latin American cultural contexts when relevant
- Use clear, descriptive English for optimal AI interpretation
- Maintain visual consistency across all prompts (character appearance, art style)

INSERTION POINT REQUIREMENTS:
- Identify specific sentences or paragraphs where each image should be placed
- Choose moments that enhance comprehension and engagement
- Distribute images evenly throughout the story (beginning, middle, end)
- Select points that show key actions, settings, or emotional moments

IMAGE DESCRIPTION REQUIREMENTS:
- Write brief, engaging descriptions in English (2-3 sentences)
- Focus on what the image shows and why it's important to the story
- Use language appropriate for language learners
- Highlight cultural elements or key story moments

PROMPT STRUCTURE:
Each prompt should include:
- The selected art style specification
- Scene description with specific details
- Character details (appearance, clothing, expression, action)
- Setting and background elements
- Lighting and atmosphere
- Mood and emotional tone

Generate 3-5 image prompts that tell the story visually when viewed in sequence, with specific insertion points and descriptive captions."""},
                {"role": "user", "content": f"""STORY TO ANALYZE:
{story_data}

STORY CONTEXT:
Summary: {story_context.story_summary}
Key Moments: {', '.join(story_context.key_moments)}
Cultural Elements: {', '.join(story_context.cultural_elements)}
Target Audience: {story_context.target_audience}
Mood and Tone: {story_context.mood_and_tone}
Visual Themes: {', '.join(story_context.visual_themes)}

ORIGINAL STORY CONTEXT:
Title: {entire_story_context.title}
World: {entire_story_context.world.world_description}
Characters: {entire_story_context.characters.main_character}
Style: {entire_story_context.style.style} - {entire_story_context.style.tone}"""}
            ],
            temperature=0.6,
            max_tokens=2000,
            response_format=StoryAnalysis
        )
        return response.choices[0].message.parsed

    def _generate_images(self, analysis: StoryAnalysis, images_dir: str, story_id: str) -> IllustrationResults:
        """Generate images using DALL-E 3 API"""
        image_prompts: list[ImagePrompt] = analysis.selected_moments
        art_style: str = analysis.art_style
        image_results = []
        successful_count = 0
        failed_count = 0

        for i, prompt_data in enumerate(image_prompts, 1):
            print(f"Generating image {i}/{len(image_prompts)}...")
            
            try:
                # Generate image using DALL-E 3
                image_url = self._call_dalle_api(prompt_data.prompt)
                
                if image_url:
                    # Download and save image
                    file_path = f"{images_dir}/image-{i}.png"
                    success = self._download_image(image_url, file_path)
                    
                    if success:
                        image_results.append(ImageGenerationResult(
                            image_number=i,
                            prompt=prompt_data.prompt,
                            image_url=image_url,
                            file_path=file_path,
                            status="success",
                            insertion_point=prompt_data.insertion_point,
                            image_description=prompt_data.image_description
                        ))
                        successful_count += 1
                        print(f"✓ Image {i} generated and saved successfully")
                    else:
                        image_results.append(ImageGenerationResult(
                            image_number=i,
                            prompt=prompt_data.prompt,
                            image_url=image_url,
                            status="failed",
                            error_message="Failed to download image",
                            insertion_point=prompt_data.insertion_point,
                            image_description=prompt_data.image_description
                        ))
                        failed_count += 1
                        print(f"✗ Image {i} download failed")
                else:
                    image_results.append(ImageGenerationResult(
                        image_number=i,
                        prompt=prompt_data.prompt,
                        status="failed",
                        error_message="Failed to generate image URL",
                        insertion_point=prompt_data.insertion_point,
                        image_description=prompt_data.image_description
                    ))
                    failed_count += 1
                    print(f"✗ Image {i} generation failed")
                    
            except Exception as e:
                image_results.append(ImageGenerationResult(
                    image_number=i,
                    prompt=prompt_data.prompt,
                    status="failed",
                    error_message=str(e),
                    insertion_point=prompt_data.insertion_point,
                    image_description=prompt_data.image_description
                ))
                failed_count += 1
                print(f"✗ Image {i} failed with error: {str(e)}")

        return IllustrationResults(
            story_id=story_id,
            total_images=len(image_prompts),
            successful_images=successful_count,
            failed_images=failed_count,
            image_results=image_results,
            summary=""
        )

    def _call_dalle_api(self, prompt: str) -> Optional[str]:
        """Call DALL-E 3 API to generate image"""
        try:
            response = self.llm.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                response_format="url",
                n=1
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
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Verify file was created and has content
            return os.path.exists(file_path) and os.path.getsize(file_path) > 0
        except Exception as e:
            print(f"Download error: {str(e)}")
            return False

    def _create_summary(self, analysis: StoryAnalysis, results: IllustrationResults) -> str:
        """Create comprehensive summary of illustration process"""
        summary_parts = [
            f"## Story Illustration Summary",
            f"**Story**: {analysis.story_summary}",
            f"**Total Images Generated**: {results.total_images}",
            f"**Successful**: {results.successful_images}",
            f"**Failed**: {results.failed_images}",
            f"**Art Style**: {analysis.art_style}",
            f"**Target Audience**: {analysis.target_audience}",
            "",
            "## Image Generation Results:"
        ]
        
        for result in results.image_results:
            status_icon = "✓" if result.status == "success" else "✗"
            summary_parts.append(f"**Image {result.image_number}**: {result.file_path or 'Failed'}")
            summary_parts.append(f"- Status: {status_icon} {result.status}")
            if result.status == "success":
                summary_parts.append(f"- Prompt: {result.prompt[:100]}...")
            elif result.error_message:
                summary_parts.append(f"- Error: {result.error_message}")
            summary_parts.append("")
        
        summary_parts.extend([
            "## Cultural Considerations:",
            f"- {', '.join(analysis.cultural_elements)}",
            "",
            "## Notes:",
            "All images generated using DALL-E 3 with culturally-appropriate prompts",
            "Images saved in 1024x1024 resolution for optimal story display"
        ])
        
        return "\n".join(summary_parts)

    def create_illustrated_story(self, story_path: str, illustration_results: IllustrationResults) -> str:
        """Create a story with images inserted at optimal points"""
        # Read the original story
        with open(story_path, "r", encoding="utf-8") as f:
            story_text = f.read()
        
        # Split story into paragraphs
        paragraphs = [p.strip() for p in story_text.strip().split("\n\n") if p.strip()]
        
        # Calculate insertion points - distribute images evenly
        total_paragraphs = len(paragraphs)
        successful_images = [r for r in illustration_results.image_results if r.status == "success"]
        
        if not successful_images:
            return story_text
        
        # Calculate insertion points (after every nth paragraph)
        insertion_interval = max(1, total_paragraphs // len(successful_images))
        insertion_points = [i * insertion_interval for i in range(1, len(successful_images) + 1)]
        
        # Create illustrated story with images
        illustrated_story_parts = []
        image_index = 0
        
        for i, paragraph in enumerate(paragraphs):
            illustrated_story_parts.append(paragraph)
            
            # Check if we should insert an image after this paragraph
            if i + 1 in insertion_points and image_index < len(successful_images):
                result = successful_images[image_index]
                # Insert image placeholder and description
                image_placeholder = f"\n\n[IMAGE: {result.file_path}]\n{result.image_description}\n"
                illustrated_story_parts.append(image_placeholder)
                image_index += 1
        
        return "\n\n".join(illustrated_story_parts)