import os
from pydantic import BaseModel


class Chunk(BaseModel):
    data: str


class RevisedChunk(BaseModel):
    revised_section: str
    changes_made: list[str]


class AgentReviewer:
    def __init__(self, llm):
        self.llm = llm

    def review_story(self, full_story_context, level: str, story_id: str) -> None:
        """Review and revise story using chunked approach"""
        print(f"Starting story review for level: {level}")

        # Step 1: Get the story content from full_story_context
        story_content = full_story_context.draft.story

        # Step 2: Chunk the story into sections for detailed review
        story_chunks = self._chunk_story(story_content)
        print(f"Story chunked into {len(story_chunks)} sections")

        # Step 3: Review and revise each chunk individually
        revised_chunks = []
        revisions_log = []
        for i, chunk in enumerate(story_chunks):
            print(f"Reviewing section {i + 1} of {len(story_chunks)}")
            revised_chunk = self._revise_story_chunk(chunk, level)
            revised_chunks.append(revised_chunk)

            # Log the changes made for this chunk
            revisions_log.append(
                f"Chunk {i + 1}:\n{chr(10).join(revised_chunk.changes_made)}\n"
            )

        # Step 4: Combine revised chunks into final story
        revised_story = self._combine_revised_chunks(revised_chunks)
        print("Story revisions completed")

        # Step 5: Write revised story
        self._write_revised_story(revised_story, story_id)
        print("Revised story saved")

        # Step 6: Write revisions log
        self._write_revisions_log(revisions_log, story_id)
        print("Revisions log saved")

    def _chunk_story(self, story: str) -> list[Chunk]:
        """Split the story into chunks based on paragraphs"""
        paragraphs = story.split("\n\n")
        chunks = []
        for paragraph in paragraphs:
            if paragraph.strip():
                chunks.append(Chunk(data=paragraph.strip()))
        return chunks

    def _revise_story_chunk(self, chunk: Chunk, level: str) -> RevisedChunk:
        """Revise a single story chunk for grammar, spelling, and CEFR level alignment"""

        system_prompt = """You are an expert Spanish language educator and story editor. You can review and revise Spanish story sections to ensure they are grammatically correct, properly spelled, and appropriately leveled for CEFR language learners."""
        user_prompt = f"""
        [Context]
        Story Section: {chunk.data}
        Target CEFR Level: {level}

        [Instructions]
        I want you to review and revise this story section to ensure it is grammatically correct, properly spelled, and appropriately leveled for CEFR {level} Spanish language learners.

        [Rules]
        - Write entirely in Spanish
        - Fix any grammatical errors, spelling mistakes, or awkward constructions
        - Ensure vocabulary and grammar complexity match CEFR {level} requirements
        - Maintain the original meaning and style of the section
        - Keep the same approximate length as the original
        - Make language natural and authentic for Spanish speakers

        [Output Format]
        Return the revised section and a list of specific changes made."""

        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=700,
            response_format=RevisedChunk,
        )

        return response.choices[0].message.parsed

    def _combine_revised_chunks(self, revised_chunks: list[RevisedChunk]) -> str:
        """Combine revised chunks into final story"""
        story_sections = []
        for chunk in revised_chunks:
            story_sections.append(chunk.revised_section)
        return "\n\n".join(story_sections)

    def _write_revised_story(self, revised_story: str, story_id: str) -> None:
        """Save the revised story to file"""
        story_dir = f"agent-generated-stories/{story_id}"
        os.makedirs(story_dir, exist_ok=True)

        with open(f"{story_dir}/story-revised.txt", "w", encoding="utf-8") as f:
            f.write(revised_story)

    def _write_revisions_log(self, revisions_log: list[str], story_id: str) -> None:
        """Save the revisions log to file"""
        story_dir = f"agent-generated-stories/{story_id}"
        os.makedirs(story_dir, exist_ok=True)

        with open(f"{story_dir}/revisions-made.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(revisions_log))
