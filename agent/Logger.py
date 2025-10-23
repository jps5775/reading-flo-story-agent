from datetime import datetime
import time


class Logger:
    def __init__(self):
        self.start_time = datetime.now()
        self.stats = {
            "start_time": self.start_time,
            "agent_times": {},
            "audio_success": False,
        }
        self.current_agent = None
        self.agent_start_time = None

    def start_agent(self, agent_name: str):
        """Start timing an agent"""
        if self.current_agent:
            self.end_agent()

        self.current_agent = agent_name
        self.agent_start_time = time.time()
        print(f"Starting {agent_name}...")

    def end_agent(self):
        """End timing the current agent"""
        if self.current_agent and self.agent_start_time:
            duration = time.time() - self.agent_start_time
            self.stats["agent_times"][self.current_agent] = duration
            print(
                f"{self.current_agent} completed in {self._format_duration(duration)}"
            )

        self.current_agent = None
        self.agent_start_time = None

    def log_story_generation(self, topic: str, level: str, story_path: str):
        """Log story generation completion"""
        print(f"Generating story: {topic} (Level: {level})")
        print(f"Story generated and saved to file: {story_path}")

    def log_story_review(self, story_path: str):
        """Log story review completion"""
        print(f"Story reviewed and saved to file: {story_path}")

    def log_illustration_results(self, story_id: str):
        """Log illustration completion"""
        print(f"Story illustrated successfully for story ID: {story_id}")
        print(f"Images saved to: agent-generated-stories/{story_id}/imgs/")
        print("Story-revised.txt updated with image placeholders")

    def log_illustrated_story(self, story_path: str):
        """Log illustrated story creation"""
        print(f"Illustrated story saved to: {story_path}")

    def log_audio_results(self, audio_result):
        """Log audio generation results"""
        if audio_result.success:
            print("Audio created successfully:")
            print(f"- Generated {len(audio_result.voice_results)} voice configurations")
            for voice_result in audio_result.voice_results:
                print(
                    f"  • {voice_result.language_code} {voice_result.gender} ({voice_result.voice_name})"
                )
                print(f"    Audio: {voice_result.audio_file_path}")
                print(f"    Timing: {voice_result.timing_file_path}")
                print(f"    Size: {voice_result.file_size_mb:.2f} MB")
        else:
            print(f"Audio generation failed: {audio_result.error_message}")

    def log_html_preview(self, html_path: str):
        """Log HTML preview creation"""
        print(f"HTML preview created at {html_path}")

    def set_audio_success(self, success: bool):
        """Set audio generation success status"""
        self.stats["audio_success"] = success

    def print_final_stats(self):
        """Print final timing statistics"""
        self.end_agent()  # End any running agent

        end_time = datetime.now()
        self.stats["end_time"] = end_time
        self.stats["total_duration"] = (end_time - self.start_time).total_seconds()

        print("\n" + "=" * 60)
        print("📊 STORY GENERATION PERFORMANCE STATS")
        print("=" * 60)

        total_time = self.stats["total_duration"]
        print(f"🕒 Total Generation Time: {self._format_duration(total_time)}")
        print(f"📅 Started: {self.stats['start_time'].strftime('%H:%M:%S')}")
        print(f"📅 Completed: {self.stats['end_time'].strftime('%H:%M:%S')}")

        print("\n📋 Agent Performance Breakdown:")
        print("-" * 40)

        for agent_name, duration in self.stats["agent_times"].items():
            percentage = (duration / total_time) * 100
            print(
                f"  {agent_name:<20} {self._format_duration(duration):<10} ({percentage:.1f}%)"
            )

        print("\n📈 Performance Insights:")
        fastest_agent = min(self.stats["agent_times"].items(), key=lambda x: x[1])
        slowest_agent = max(self.stats["agent_times"].items(), key=lambda x: x[1])

        print(
            f"  ⚡ Fastest: {fastest_agent[0]} ({self._format_duration(fastest_agent[1])})"
        )
        print(
            f"  🐌 Slowest: {slowest_agent[0]} ({self._format_duration(slowest_agent[1])})"
        )

        if self.stats.get("audio_success"):
            print("  🎵 Audio: Generated successfully")
        else:
            print("  🎵 Audio: Not generated")

        print("=" * 60)

    def _format_duration(self, seconds: float) -> str:
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
