class MemoryStore:

    @staticmethod
    def create_memory(story):
        """ Create a new story memory for this story"""
        # TODO: 1. `story` should be the story object that has all the context of the story
        # TODO: 2. Use a llm call to generate a story summary
        # TODO: 3. Save the story summary and story object to a JSON file in the respective story_id directory
        pass 

    @staticmethod
    def get_memories(story_id: str):
        """ Get the all story memories for this story"""
        # TODO: Retrieve the story summary and story object from the JSON file in the respective story_id directory
        pass

    @staticmethod
    def update_memory(story_id: str, memory: str):
        # TODO: Need to think about how to update memories for a story
        pass