from dotenv import load_dotenv
from openai import OpenAI
import os
import uuid
import time
from datetime import datetime
from agent.AgentAudioMaker import AgentAudioMaker
from agent.AgentIllustrator import AgentIllustrator, IllustrationResults
from agent.AgentWriter import AgentWriter, EntireStoreContext
from agent.AgentReviewer import AgentReviewer
from agent.AgentPreviewer import AgentPreviewer
from agent.FirestoreUploader import FirestoreUploader
from agent.S3Uploder import S3Uploder
from agent.AgentAudioMaker import AudioGenerationResult, VoiceAudioResult

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours}h {minutes}m {remaining_seconds:.1f}s"

def print_timing_stats(stats):
    """Print formatted timing statistics"""
    print("\n" + "="*60)
    print("📊 STORY GENERATION PERFORMANCE STATS")
    print("="*60)
    
    total_time = stats['total_duration']
    print(f"🕒 Total Generation Time: {format_duration(total_time)}")
    print(f"📅 Started: {stats['start_time'].strftime('%H:%M:%S')}")
    print(f"📅 Completed: {stats['end_time'].strftime('%H:%M:%S')}")
    
    print(f"\n📋 Agent Performance Breakdown:")
    print("-" * 40)
    
    for agent_name, duration in stats['agent_times'].items():
        percentage = (duration / total_time) * 100
        print(f"  {agent_name:<20} {format_duration(duration):<10} ({percentage:.1f}%)")
    
    print(f"\n📈 Performance Insights:")
    fastest_agent = min(stats['agent_times'].items(), key=lambda x: x[1])
    slowest_agent = max(stats['agent_times'].items(), key=lambda x: x[1])
    
    print(f"  ⚡ Fastest: {fastest_agent[0]} ({format_duration(fastest_agent[1])})")
    print(f"  🐌 Slowest: {slowest_agent[0]} ({format_duration(slowest_agent[1])})")
    
    if stats.get('audio_success'):
        print(f"  🎵 Audio: Generated successfully")
    else:
        print(f"  🎵 Audio: Not generated")
    
    print("="*60)

def main():
    
    load_dotenv()
    llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Initialize timing stats
    start_time = datetime.now()
    stats = {
        'start_time': start_time,
        'agent_times': {},
        'audio_success': False
    }
    audio_result = None

    # topic = input("Enter a topic: ")
    # level = input("Enter CEFR level (A1, A2, B1, etc.): ")
    topic = "Create me a story about a secret agent needs to complete a mission in Spain about recovering a stolen jewel from an evil villain."
    level = "C1"
    story_id = str(uuid.uuid4())
    directory_path = "./agent-generated-stories"
    
    # Create initial story
    print(f"Generating story: {topic} (Level: {level})")
    writer_start = time.time()
    writer: AgentWriter = AgentWriter(llm)
    entire_story_context: EntireStoreContext = writer.generate_story(topic, level, story_id, directory_path)
    writer_duration = time.time() - writer_start
    stats['agent_times']['AgentWriter'] = writer_duration
    initial_story_path = f"{directory_path}/{story_id}/story.txt"
    print(f"Story generated and saved to file: {initial_story_path} (took {format_duration(writer_duration)})")
    
    # Review story
    print("Reviewing story...")
    reviewer_start = time.time()
    reviewer: AgentReviewer = AgentReviewer(llm)
    reviewer.review_story(initial_story_path, level, story_id)
    reviewer_duration = time.time() - reviewer_start
    stats['agent_times']['AgentReviewer'] = reviewer_duration
    final_story_path = f"agent-generated-stories/{story_id}/story-revised.txt"
    print(f"Story reviewed and saved to file: {final_story_path} (took {format_duration(reviewer_duration)})")
    
    # Illustrate story
    print("Illustrating story...")
    illustrator_start = time.time()
    illustrator: AgentIllustrator = AgentIllustrator(llm)
    illustration_results: IllustrationResults = illustrator.illustrate_story(final_story_path, entire_story_context, story_id)
    illustrator_duration = time.time() - illustrator_start
    stats['agent_times']['AgentIllustrator'] = illustrator_duration
    print(f"Story illustration completed (took {format_duration(illustrator_duration)}):")
    print(f"- Total images: {illustration_results.total_images}")
    print(f"- Successful: {illustration_results.successful_images}")
    print(f"- Failed: {illustration_results.failed_images}")
    print(f"- Summary: {illustration_results.summary}")
    print(f"Images saved to: agent-generated-stories/{story_id}/imgs/")

    # Create illustrated story text file
    print("Creating illustrated story...")
    illustrated_story_start = time.time()
    illustrated_story: str = illustrator.create_illustrated_story(final_story_path, illustration_results)
    illustrated_story_path = f"agent-generated-stories/{story_id}/story-illustrated.txt"
    with open(illustrated_story_path, "w", encoding="utf-8") as f:
        f.write(illustrated_story)
    illustrated_story_duration = time.time() - illustrated_story_start
    stats['agent_times']['CreateIllustratedStory'] = illustrated_story_duration
    print(f"Illustrated story saved to: {illustrated_story_path} (took {format_duration(illustrated_story_duration)})")

    # Create audio for story
    print("Creating audio for story...")
    audio_start = time.time()
    audio_maker: AgentAudioMaker = AgentAudioMaker()
    audio_result = audio_maker.create_audio(final_story_path, story_id, directory_path)
    audio_duration = time.time() - audio_start
    stats['agent_times']['AgentAudioMaker'] = audio_duration
    stats['audio_success'] = audio_result.success
    
    if audio_result.success:
        print(f"Audio created successfully (took {format_duration(audio_duration)}):")
        print(f"- Generated {len(audio_result.voice_results)} voice configurations")
        for voice_result in audio_result.voice_results:
            print(f"  • {voice_result.language_code} {voice_result.gender} ({voice_result.voice_name})")
            print(f"    Audio: {voice_result.audio_file_path}")
            print(f"    Timing: {voice_result.timing_file_path}")
            print(f"    Size: {voice_result.file_size_mb:.2f} MB")
    else:
        print(f"Audio generation failed (took {format_duration(audio_duration)}): {audio_result.error_message}")

    # Create HTML preview
    print("Creating HTML preview...")
    previewer = AgentPreviewer()
    html_path = previewer.create_html_preview(entire_story_context.title, final_story_path, level, story_id, illustration_results, audio_result)
    print(f"HTML preview created at {html_path}")

    # Calculate final stats and print
    end_time = datetime.now()
    stats['end_time'] = end_time
    stats['total_duration'] = (end_time - start_time).total_seconds()
    
    print_timing_stats(stats)

    if(False):
        # Upload to contents to S3
        print("Uploading to S3...")
        s3_uploader: S3Uploder = S3Uploder()
        s3_uploader.upload(html_path)
        print(f"Uploaded to S3")

        # Upload metadata to Firestore
        print("Uploading to Firestore...")
        firestore_uploader: FirestoreUploader = FirestoreUploader()
        firestore_uploader.upload(html_path)
        print(f"Uploaded to Firestore")

if __name__ == "__main__":
    main()
