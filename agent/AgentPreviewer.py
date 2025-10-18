import os
from typing import Optional
from agent.AgentIllustrator import IllustrationResults

class AgentPreviewer:
    def __init__(self):
        pass

    def create_html_preview(self, title: str, story_path: str, level: str, story_id: str, illustration_results: Optional[IllustrationResults] = None) -> str:
        """
        Create an HTML preview of the story with optional illustrations
        
        Args:
            title: Story title
            story_path: Path to the story text file
            level: CEFR level (A1, A2, B1, etc.)
            story_id: Unique story identifier
            illustration_results: Optional illustration results from AgentIllustrator
            
        Returns:
            Path to the created HTML file
        """
        # Read story from file
        with open(story_path, "r", encoding="utf-8") as f:
            story = f.read()
        
        # Split story into paragraphs
        paragraphs = [p.strip() for p in story.strip().split("\n\n") if p.strip()]
        
        # Create paragraph HTML with images
        story_paragraphs = ""
        
        if illustration_results:
            # Calculate insertion points - distribute images evenly
            total_paragraphs = len(paragraphs)
            successful_images = [r for r in illustration_results.image_results if r.status == "success"]
            
            if successful_images:
                # Calculate insertion points (after every nth paragraph)
                insertion_interval = max(1, total_paragraphs // len(successful_images))
                insertion_points = [i * insertion_interval for i in range(1, len(successful_images) + 1)]
            else:
                insertion_points = []
        else:
            insertion_points = []
            successful_images = []
        
        image_index = 0
        
        for i, paragraph in enumerate(paragraphs):
            # Check if paragraph contains dialogue (simple heuristic: starts with quote or contains quotes)
            if paragraph.startswith('"') or '"' in paragraph:
                # Split dialogue and narrative
                parts = paragraph.split('"')
                formatted_parts = []
                for j, part in enumerate(parts):
                    if j % 2 == 1:  # Odd indices are dialogue
                        formatted_parts.append(f'<span class="dialogue">"{part}"</span>')
                    else:  # Even indices are narrative
                        if part.strip():
                            formatted_parts.append(part.strip())
                story_paragraphs += f'<p>{"".join(formatted_parts)}</p>\n            '
            else:
                story_paragraphs += f'<p>{paragraph}</p>\n            '
            
            # Insert image after this paragraph if it's an insertion point
            if i + 1 in insertion_points and image_index < len(successful_images):
                result = successful_images[image_index]
                # Convert relative path to web path
                image_path = result.file_path.replace("agent-generated-stories/" + story_id + "/", "")
                story_paragraphs += f'''
            <div class="story-image">
                <img src="{image_path}" alt="Story illustration {result.image_number}" class="img-fluid rounded">
                <p class="image-caption">{result.image_description}</p>
            </div>
            '''
                image_index += 1
        
        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Reading Flo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .story-content p {{
            font-size: 1.1rem;
            line-height: 1.8;
            margin-bottom: 1.2rem;
        }}
        .story-image {{
            margin: 2rem 0;
        }}
        .story-title {{
            color: #2c3e50;
            margin-bottom: 1rem;
        }}
        .level-badge {{
            font-size: 1rem;
            padding: 0.5rem 1rem;
        }}
        .dialogue {{
            font-style: italic;
            color: #495057;
        }}
        .image-caption {{
            font-size: 0.9rem;
            color: #6c757d;
            font-style: italic;
            text-align: center;
            margin-top: 0.5rem;
            padding: 0 1rem;
        }}
        .story-image {{
            text-align: center;
            margin: 2rem 0;
        }}
        .story-image img {{
            max-width: 100%;
            height: auto;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <article class="container my-5">
        <header class="mb-4 text-center">
            <h1 class="display-4 story-title">{title}</h1>
            <span class="badge bg-primary level-badge">Nivel {level}</span>
            <p class="text-muted mt-2">Una historia para aprender español</p>
        </header>


        <section class="story-content">
            {story_paragraphs}
        </section>
    </article>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
        
        # Ensure directory exists
        story_dir = f"agent-generated-stories/{story_id}"
        os.makedirs(story_dir, exist_ok=True)
        
        # Write HTML file
        html_path = f"{story_dir}/story-preview.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return html_path
