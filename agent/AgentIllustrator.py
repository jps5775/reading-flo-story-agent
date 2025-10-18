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
        Main method to generate images for a Spanish story
        """
        print(f"Starting illustration process for story: {story_id}")
        
        # Read story from file
        story_data = self._read_story(story_path)
        
        # Analyze story and generate prompts
        analysis = self._analyze_story(story_data, entire_story_context)
        print(f"Generated {len(analysis.selected_moments)} image prompts")
        
        # Create images directory
        images_dir = f"agent-generated-stories/{story_id}/imgs"
        os.makedirs(images_dir, exist_ok=True)
        
        # Generate images
        results = self._generate_images(analysis.selected_moments, images_dir, story_id)
        
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

    def _analyze_story(self, story_data: str, entire_story_context: EntireStoreContext) -> StoryAnalysis:
        """Analyze story and generate image prompts using structured output"""
        prompt = f"""
        You are an expert visual storytelling specialist with deep expertise in Spanish language and culture, children's literature illustration, and AI image generation. Your role is to analyze this Spanish story and create compelling, culturally-appropriate image prompts.

        STORY TO ANALYZE:
        {story_data}

        STORY CONTEXT:
        Title: {entire_story_context.title}
        World: {entire_story_context.world.world_description}
        Cultural Elements: {', '.join(entire_story_context.world.cultural_elements)}
        Atmosphere: {entire_story_context.world.atmosphere}
        Characters: {entire_story_context.characters.main_character}
        Style: {entire_story_context.style.style} - {entire_story_context.style.tone}

        TASK:
        1. Analyze the complete Spanish story
        2. Identify 3-5 key narrative moments that would benefit from illustration
        3. Create detailed image prompts for each moment
        4. Determine optimal insertion points in the story for each image
        5. Create descriptive captions for each image
        6. Ensure cultural authenticity and visual consistency

        REQUIREMENTS FOR IMAGE PROMPTS:
        - Capture pivotal moments in the story's progression
        - Include specific visual details: character appearance, setting elements, lighting, mood
        - Reflect authentic Spanish/Latin American cultural contexts when relevant
        - Use clear, descriptive English for optimal AI interpretation
        - Maintain visual consistency across all prompts (character appearance, art style)
        - Include art style specification (e.g., "watercolor illustration", "children's book style")

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
        - Art style specification
        - Scene description with specific details
        - Character details (appearance, clothing, expression, action)
        - Setting and background elements
        - Lighting and atmosphere
        - Mood and emotional tone

        EXAMPLE PROMPT FORMAT:
        "Watercolor illustration of a young Spanish girl with dark curly hair and a yellow dress, discovering a hidden garden gate covered in purple bougainvillea in a sunny Madrid courtyard. Warm afternoon light, sense of wonder and curiosity, soft pastel colors, whimsical children's book style."

        Generate 3-5 image prompts that tell the story visually when viewed in sequence, with specific insertion points and descriptive captions.
        """

        response = self.llm.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=2000,
            response_format=StoryAnalysis
        )

        return response.choices[0].message.parsed

    def _generate_images(self, image_prompts: list[ImagePrompt], images_dir: str, story_id: str) -> IllustrationResults:
        """Generate images using DALL-E 3 API"""
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