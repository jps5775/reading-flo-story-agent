import os
import json
from typing import Optional
from agent.AgentAudioMaker import AudioGenerationResult


class AgentPreviewer:
    def __init__(self):
        pass

    def create_html_preview(
        self,
        title: str,
        story_path: str,
        level: str,
        story_id: str,
        audio_result: Optional[AudioGenerationResult] = None,
    ) -> str:
        """
        Create an HTML preview of the story with optional illustrations and audio
        """
        # Read story from file
        with open(story_path, "r", encoding="utf-8") as f:
            story = f.read()

        # Split story into paragraphs and process image placeholders
        paragraphs = [p.strip() for p in story.strip().split("\n\n") if p.strip()]

        # Create paragraph HTML with dialogue, images, and word highlighting
        story_paragraphs = ""

        for raw_paragraph in paragraphs:
            # Check if this paragraph contains an image placeholder
            if raw_paragraph.startswith("[IMAGE:"):
                # Extract image path and description from placeholder
                content = raw_paragraph.replace("[IMAGE:", "").replace("]", "").strip()

                # Check if description is included
                if " | DESCRIPTION: " in content:
                    image_path, image_description = content.split(" | DESCRIPTION: ", 1)
                else:
                    image_path = content
                    image_description = "Story illustration"

                # Convert to relative path for HTML
                relative_image_path = image_path.replace(
                    "agent-generated-stories/" + story_id + "/", ""
                )
                story_paragraphs += f'''
        <div class="story-image">
            <img src="{relative_image_path}" alt="{image_description}" class="img-fluid rounded">
            <div class="image-caption">{image_description}</div>
        </div>
        '''
            elif raw_paragraph.startswith('"') or '"' in raw_paragraph:
                # Handle dialogue
                parts = raw_paragraph.split('"')
                formatted_parts = []
                for j, part in enumerate(parts):
                    if part.strip():
                        highlighted = self._process_paragraph_for_highlighting(part)
                        if j % 2 == 1:
                            formatted_parts.append(
                                f'<span class="dialogue">"{highlighted}"</span>'
                            )
                        else:
                            formatted_parts.append(highlighted)
                story_paragraphs += f"<p>{''.join(formatted_parts)}</p>\n"
            else:
                # Regular paragraph
                highlighted = self._process_paragraph_for_highlighting(raw_paragraph)
                story_paragraphs += f"<p>{highlighted}</p>\n"

        # Create audio player HTML if audio is available
        audio_player_html = ""
        timing_data_js = ""
        if audio_result and audio_result.success:
            voice_options = ""
            for i, voice_result in enumerate(audio_result.voice_results):
                selected = "selected" if i == 0 else ""
                voice_options += f'<option value="{i}" {selected}>{voice_result.language_code} {voice_result.gender} ({voice_result.voice_name})</option>'

            first_voice = audio_result.voice_results[0]
            timing_data = self._load_timing_data(first_voice.timing_file_path)
            timing_data_js = f"window.timingData = {json.dumps(timing_data)};"

            audio_player_html = f"""
        <div class="audio-player-container mb-4">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">
                        <i class="bi bi-volume-up"></i> Narración en Audio
                    </h5>
                    
                    <div class="mb-3">
                        <label for="voice-select" class="form-label">Seleccionar Voz:</label>
                        <select id="voice-select" class="form-select">
                            {voice_options}
                        </select>
                    </div>
                    
                    <audio controls class="w-100" preload="metadata" id="story-audio">
                        <source src="{first_voice.audio_file_path.replace("agent-generated-stories/" + story_id + "/", "")}" type="audio/mpeg">
                        Tu navegador no soporta el elemento de audio.
                    </audio>
                    
                    <p class="card-text text-muted mt-2">
                        <small>Escucha la historia mientras lees para mejorar tu pronunciación y comprensión.</small>
                    </p>
                </div>
            </div>
        </div>"""

        # Build HTML content step by step to avoid f-string issues
        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Reading Flo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
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
        .audio-player-container {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            padding: 1rem;
        }}
        .audio-player-container .card {{
            border: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .audio-player-container .card-title {{
            color: #2c3e50;
            margin-bottom: 1rem;
        }}
        .audio-player-container audio {{
            border-radius: 5px;
        }}
        .word {{
            cursor: pointer;
            transition: all 0.3s ease;
            padding: 2px 1px;
            border-radius: 3px;
        }}
        .word:hover {{
            background-color: rgba(0, 123, 255, 0.1);
        }}
        .word.active {{
            background-color: #ffeb3b;
            font-weight: bold;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .word.highlighted {{
            background-color: rgba(255, 193, 7, 0.3);
        }}
        .form-select {{
            border-radius: 5px;
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

        {audio_player_html}

        <section class="story-content">
            {story_paragraphs}
        </section>
    </article>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        {timing_data_js}
        
        document.addEventListener('DOMContentLoaded', function() {{
            const audio = document.getElementById('story-audio');
            const voiceSelect = document.getElementById('voice-select');
            
            const voiceData = {
            json.dumps(
                [
                    {
                        "audio_path": vr.audio_file_path.replace(
                            "agent-generated-stories/" + story_id + "/", ""
                        ),
                        "timing_path": vr.timing_file_path.replace(
                            "agent-generated-stories/" + story_id + "/", ""
                        ),
                        "language_code": vr.language_code,
                        "gender": vr.gender,
                        "voice_name": vr.voice_name,
                    }
                    for vr in audio_result.voice_results
                ]
            )
            if audio_result and audio_result.success
            else "[]"
        };
            
            function loadTimingData(voiceIndex) {{
                if (voiceData[voiceIndex]) {{
                    fetch(voiceData[voiceIndex].timing_path)
                        .then(response => response.json())
                        .then(data => {{
                            window.timingData = data;
                            console.log('Timing data loaded:', data.length, 'words');
                        }})
                        .catch(error => {{
                            console.error('Error loading timing data:', error);
                        }});
                }}
            }}
            
            if (voiceSelect) {{
                voiceSelect.addEventListener('change', function() {{
                    const selectedIndex = parseInt(this.value);
                    const selectedVoice = voiceData[selectedIndex];
                    
                    if (selectedVoice) {{
                        const source = audio.querySelector('source');
                        source.src = selectedVoice.audio_path;
                        audio.load();
                        loadTimingData(selectedIndex);
                    }}
                }});
            }}
            
            if (audio) {{
                audio.addEventListener('timeupdate', function() {{
                    if (window.timingData) {{
                        const currentTime = audio.currentTime;
                        const words = document.querySelectorAll('.word');
                        
                        let currentWordIndex = -1;
                        for (let i = 0; i < window.timingData.length; i++) {{
                            if (window.timingData[i].time_seconds <= currentTime) {{
                                currentWordIndex = i;
                            }} else {{
                                break;
                            }}
                        }}
                        
                        words.forEach(w => w.classList.remove('active'));
                        if (currentWordIndex >= 0 && words[currentWordIndex]) {{
                            words[currentWordIndex].classList.add('active');
                        }}
                    }}
                }});
                
                audio.addEventListener('play', function() {{
                    document.body.classList.add('audio-playing');
                }});
                audio.addEventListener('pause', function() {{
                    document.body.classList.remove('audio-playing');
                }});
            }}
        }});
    </script>
</body>
</html>"""

        story_dir = f"agent-generated-stories/{story_id}"
        os.makedirs(story_dir, exist_ok=True)

        html_path = f"{story_dir}/story-preview.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path

    def _process_paragraph_for_highlighting(self, paragraph: str) -> str:
        """Process paragraph text to wrap words in spans for highlighting"""
        import re
        import html

        tokens = re.findall(r"\w+|[^\w\s]|\s+", paragraph, re.UNICODE)
        processed_tokens = []

        for token in tokens:
            if token.isspace():
                processed_tokens.append(token)
            elif re.match(r"\w+", token):
                escaped = html.escape(token)
                span = f'<span class="word" data-word="{escaped}">{escaped}</span>'
                processed_tokens.append(span)
            else:
                processed_tokens.append(html.escape(token))

        return "".join(processed_tokens)

    def _load_timing_data(self, timing_file_path: str) -> list:
        """Load timing data from JSON file"""
        try:
            with open(timing_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading timing data: {e}")
            return []
