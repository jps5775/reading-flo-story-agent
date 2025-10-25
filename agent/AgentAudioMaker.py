import os
import json
import html
from typing import Optional
from pydantic import BaseModel
from google.cloud import texttospeech_v1beta1 as tts
from google.oauth2 import service_account
import tempfile
import subprocess
import os
import tempfile


class VoiceAudioResult(BaseModel):
    language_code: str
    gender: str
    voice_name: str
    audio_file_path: str
    timing_file_path: str
    file_size_mb: float


class AudioGenerationResult(BaseModel):
    success: bool
    story_id: str
    voice_results: list[VoiceAudioResult] = []
    error_message: Optional[str] = None


class TimingPoint(BaseModel):
    mark_name: str
    time_seconds: float


class AgentAudioMaker:
    def __init__(self):
        # Google TTS setup
        credentials_dict = json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict
        )
        self.tts_client = tts.TextToSpeechClient(credentials=credentials)

        # Voice configurations
        self.voice_configs = {
            "es-ES": {
                "male": {
                    "language_code": "es-ES",
                    "voice_name": "es-ES-Neural2-G",
                    "gender": tts.SsmlVoiceGender.MALE,
                },
                "female": {
                    "language_code": "es-ES",
                    "voice_name": "es-ES-Neural2-H",
                    "gender": tts.SsmlVoiceGender.FEMALE,
                },
            },
            "es-US": {
                "male": {
                    "language_code": "es-US",
                    "voice_name": "es-US-Neural2-C",
                    "gender": tts.SsmlVoiceGender.MALE,
                },
                "female": {
                    "language_code": "es-US",
                    "voice_name": "es-US-Neural2-A",
                    "gender": tts.SsmlVoiceGender.FEMALE,
                },
            },
        }

    def create_audio(
        self, story_path: str, story_id: str, directory_path: str
    ) -> AudioGenerationResult:
        """
        Main method to generate audio narration for all voice configurations
        """
        print(f"Starting audio generation for story: {story_id}")

        try:
            # Step 1: Read and prepare story text
            print("Step 1: Reading and preparing story text...")
            story_text = self._read_and_prepare_story(story_path)
            print(f"Prepared story text: {len(story_text)} characters")

            # Step 2: Generate SSML with timing marks
            print("Step 2: Creating SSML with timing marks...")
            ssml_text = self._create_ssml_with_timing(story_text)

            # Step 3: Generate audio for all voice configurations
            print("Step 3: Generating audio for all voice configurations...")
            voice_results = []

            for language_code in self.voice_configs:
                for gender in self.voice_configs[language_code]:
                    print(f"  Generating {language_code} {gender} voice...")
                    voice_result = self._generate_voice_audio(
                        ssml_text, story_id, directory_path, language_code, gender
                    )
                    if voice_result:
                        voice_results.append(voice_result)
                        print(f"    ✓ Generated {voice_result.voice_name}")
                    else:
                        print(f"    ✗ Failed to generate {language_code} {gender}")

            print(
                f"✓ Audio generation completed: {len(voice_results)}/4 voices generated"
            )
            return AudioGenerationResult(
                success=len(voice_results) > 0,
                story_id=story_id,
                voice_results=voice_results,
            )

        except Exception as e:
            print(f"✗ Audio generation failed: {str(e)}")
            return AudioGenerationResult(
                success=False, story_id=story_id, error_message=str(e)
            )

    def _read_and_prepare_story(self, story_path: str) -> str:
        """Read story from file and prepare text for audio generation"""
        with open(story_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Filter out image references and descriptions
        filtered_lines = []
        skip_next_line = False

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip lines that start with [IMAGE: - these are image references
            if line.startswith("[IMAGE:"):
                skip_next_line = True
                continue

            # Skip the line after an image reference (usually the image description)
            if skip_next_line:
                skip_next_line = False
                continue

            # Add the line if it's not an image reference or description
            filtered_lines.append(line)

        # Join lines and clean up formatting
        story_text = " ".join(filtered_lines)

        # Remove extra whitespace and normalize
        story_text = " ".join(story_text.split())

        return story_text

    def _create_ssml_with_timing(self, story_text: str) -> str:
        """Create SSML with timing marks for each word"""
        words = story_text.split()
        ssml_text = "<speak>"

        for i, word in enumerate(words):
            clean_word = word.strip()
            # Only mark words with letters/numbers
            if any(c.isalnum() for c in clean_word):
                ssml_text += f"<mark name='w{i}'/>{html.escape(clean_word)} "
            else:
                ssml_text += f"{html.escape(clean_word)} "

        ssml_text += "</speak>"
        return ssml_text

    def _split_ssml_into_chunks(self, ssml: str, max_bytes: int = 4500) -> list[str]:
        """Split the SSML into smaller <speak> chunks within byte limit"""
        import re

        # Extract words with their marks using regex
        pattern = r"<mark name='w\d+'/>[^<\s]+|[^<\s]+"
        parts = re.findall(pattern, ssml.replace("<speak>", "").replace("</speak>", ""))

        chunks = []
        current = "<speak>"
        for part in parts:
            next_piece = f"{part} "
            if len((current + next_piece + "</speak>").encode("utf-8")) > max_bytes:
                current += "</speak>"
                chunks.append(current)
                current = "<speak>" + next_piece
            else:
                current += next_piece

        current += "</speak>"
        chunks.append(current)
        return chunks

    def _generate_voice_audio(
        self,
        ssml_text: str,
        story_id: str,
        directory_path: str,
        language_code: str,
        gender: str,
    ) -> Optional[VoiceAudioResult]:
        try:
            voice_config = self.voice_configs[language_code][gender]
            chunks = self._split_ssml_into_chunks(ssml_text, max_bytes=4500)
            chunk_files = []
            all_timepoints = []
            mark_index_offset = 0

            temp_dir = tempfile.mkdtemp()

            for idx, chunk in enumerate(chunks):
                request = tts.SynthesizeSpeechRequest(
                    input=tts.SynthesisInput(ssml=chunk),
                    voice=tts.VoiceSelectionParams(
                        language_code=voice_config["language_code"],
                        name=voice_config["voice_name"],
                        ssml_gender=voice_config["gender"],
                    ),
                    audio_config=tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3),
                    enable_time_pointing=[
                        tts.SynthesizeSpeechRequest.TimepointType.SSML_MARK
                    ],
                )

                response = self.tts_client.synthesize_speech(request=request)
                chunk_path = os.path.join(temp_dir, f"chunk_{idx}.mp3")

                with open(chunk_path, "wb") as f:
                    f.write(response.audio_content)
                chunk_files.append(chunk_path)

                all_timepoints.extend(
                    [
                        {
                            "mark_name": f"w{mark_index_offset + int(tp.mark_name[1:])}",
                            "time_seconds": tp.time_seconds,  # Adjust this later with offsets if needed
                        }
                        for tp in response.timepoints
                    ]
                )
                mark_index_offset += len(response.timepoints)

            concat_file = os.path.join(temp_dir, "concat_list.txt")
            with open(concat_file, "w") as f:
                for file_path in chunk_files:
                    f.write(f"file '{file_path}'\n")

            output_dir = f"{directory_path}/{story_id}/audio/{language_code}/{gender}"
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, "audio.mp3")

            subprocess.run(
                [
                    "ffmpeg",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    concat_file,
                    "-c",
                    "copy",
                    output_file,
                ],
                check=True,
            )

            timing_file_path = os.path.join(output_dir, "timings.json")
            with open(timing_file_path, "w", encoding="utf-8") as f:
                json.dump(all_timepoints, f, indent=2, ensure_ascii=False)

            file_size_mb = os.path.getsize(output_file) / (1024 * 1024)

            return VoiceAudioResult(
                language_code=language_code,
                gender=gender,
                voice_name=voice_config["voice_name"],
                audio_file_path=output_file,
                timing_file_path=timing_file_path,
                file_size_mb=file_size_mb,
            )

        except Exception as e:
            print(f"Error generating {language_code} {gender}: {str(e)}")
            return None
