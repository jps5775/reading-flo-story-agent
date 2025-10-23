from enum import Enum
import pickle
from dotenv import load_dotenv
from openai import OpenAI
import os
import uuid
from agent.AgentAudioMaker import AgentAudioMaker
from agent.AgentIllustrator import AgentIllustrator
from agent.AgentWriter.AgentWriter import AgentWriter
from agent.AgentWriter.AgentWriterModels import FullStoryContext
from agent.AgentReviewer import AgentReviewer
from agent.AgentPreviewer import AgentPreviewer
from agent.FirestoreUploader import FirestoreUploader
from agent.S3Uploder import S3Uploder
from agent.Logger import Logger


def load_full_story_context(story_id: str) -> FullStoryContext:
    file_path = (
        f"./agent-generated-stories/{story_id}/pickle-data/full_story_context.pickle"
    )
    with open(file_path, "rb") as file:
        return pickle.load(file)


class RunStep(Enum):
    AgentWriter = True
    AgentReviewer = True
    AgentIllustrator = True
    AgentAudioMaker = True
    AgentPreviewer = True
    SaveFullStoryContext = True
    UploadToS3 = False
    UploadToFirestore = False

    def __bool__(self):
        return self.value


def main():
    load_dotenv()
    llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Initialize logger
    logger = Logger()

    # topic = input("Enter a topic: ")
    # level = input("Enter CEFR level (A1, A2, B1, etc.): ")
    topic = "A story about a secret agent needs to complete a mission in Spain about recovering a stolen jewel from an evil villain."
    level = "A2"
    story_id = str(uuid.uuid4())
    directory_path = "./agent-generated-stories"

    # Generate initial story
    if RunStep.AgentWriter:
        logger.start_agent("AgentWriter")
        writer: AgentWriter = AgentWriter(llm)
        full_story_context: FullStoryContext = writer.generate_story(
            topic, level, story_id, directory_path
        )
        logger.end_agent()
        initial_story_path = f"{directory_path}/{story_id}/story.txt"
        full_story_context.draft_path = initial_story_path
        logger.log_story_generation(topic, level, initial_story_path)

    # Review story
    if RunStep.AgentReviewer:
        logger.start_agent("AgentReviewer")
        reviewer: AgentReviewer = AgentReviewer(llm)
        reviewer.review_story(full_story_context, level, story_id)
        logger.end_agent()
        final_story_path = f"agent-generated-stories/{story_id}/story-revised.txt"
        full_story_context.revised_draft_path = final_story_path
        logger.log_story_review(final_story_path)

    # Illustrate story
    if RunStep.AgentIllustrator:
        logger.start_agent("AgentIllustrator")
        illustrator: AgentIllustrator = AgentIllustrator(llm)
        illustrator.illustrate_story(full_story_context, story_id)
        logger.end_agent()
        logger.log_illustration_results(story_id)

    # Create audio for story
    if RunStep.AgentAudioMaker:
        logger.start_agent("AgentAudioMaker")
        audio_maker: AgentAudioMaker = AgentAudioMaker()
        audio_result = audio_maker.create_audio(
            final_story_path, story_id, directory_path
        )
        logger.end_agent()
        logger.set_audio_success(audio_result.success)
        logger.log_audio_results(audio_result)

    # Create HTML preview
    if RunStep.AgentPreviewer:
        logger.start_agent("AgentPreviewer")
        previewer = AgentPreviewer()
        html_path = previewer.create_html_preview(
            full_story_context.story_idea.title,
            final_story_path,
            full_story_context.level,
            story_id,
            audio_result,
        )
        logger.end_agent()
        logger.log_html_preview(html_path)

    # Print final stats
    logger.print_final_stats()

    # Save full story context with pickle
    if RunStep.SaveFullStoryContext:
        # Ensure directory exists before writing
        save_dir = f"./agent-generated-stories/{story_id}/pickle-data"
        os.makedirs(save_dir, exist_ok=True)

        file_path = os.path.join(save_dir, "full_story_context.pickle")
        with open(file_path, "wb") as file:
            pickle.dump(full_story_context, file)
        print(f"Full story context saved with pickle at: {file_path}")
    else:
        print("Full story context not saved with pickle")

    if RunStep.UploadToS3:
        # Upload to contents to S3
        print("Uploading to S3...")
        s3_uploader: S3Uploder = S3Uploder()
        s3_uploader.upload(html_path)
        print("Uploaded to S3")

    if RunStep.UploadToFirestore:
        # Upload metadata to Firestore
        print("Uploading to Firestore...")
        firestore_uploader: FirestoreUploader = FirestoreUploader()
        firestore_uploader.upload(html_path)
        print("Uploaded to Firestore")


if __name__ == "__main__":
    main()
