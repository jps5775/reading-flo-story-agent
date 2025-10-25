from pydantic import BaseModel


class StoryIdea(BaseModel):
    title: str
    description: str


class StoryIdeaList(BaseModel):
    all_ideas: list[StoryIdea]


class StoryDetails(BaseModel):
    theme: str
    time_period: str
    location: str
    main_character: str
    conflict: str
    resolution: str


class StoryStructureItem(BaseModel):
    section_title: str
    section_description: str


class StoryStructureList(BaseModel):
    all_sections: list[StoryStructureItem]


class StoryWorld(BaseModel):
    world_description: str
    time_period_description: str
    struggles_and_challenges: str
    cultural_elements: str
    atmosphere: str


class CharacterProfile(BaseModel):
    name: str
    personality: str
    background: str
    motivations: str
    appearance: str


class CharacterRelationship(BaseModel):
    character1_name: str
    character2_name: str
    relationship_type: str
    relationship_description: str


class StoryCharacters(BaseModel):
    main_character: CharacterProfile
    villain: CharacterProfile
    supporting_characters: list[CharacterProfile]
    character_relationships: list[CharacterRelationship]


class WritingStyle(BaseModel):
    style: str
    tone: str
    narrative_voice: str


class PlotPoint(BaseModel):
    section_title: str
    section_plot_points: list[str]


class PlotPoints(BaseModel):
    all_plot_points: list[PlotPoint]


class SubSectionPoint(BaseModel):
    sub_section_point: str
    deep_sub_section_points: list[str]


class OutlineItem(BaseModel):
    main_section_title: str
    sub_section_points: list[SubSectionPoint]


class StoryOutline(BaseModel):
    outline: list[OutlineItem]


class StoryDraft(BaseModel):
    title: str
    story: str


class FullStoryContext(BaseModel):
    story_idea: StoryIdea
    story_details: StoryDetails
    structure: StoryStructureList
    world: StoryWorld
    characters: StoryCharacters
    style: WritingStyle
    plot_points: PlotPoints
    outline: StoryOutline
    level: str
    draft: StoryDraft
    draft_path: str
    revised_draft_path: str
    summary: str

    @classmethod
    def create_default(cls, level: str) -> "FullStoryContext":
        return cls(
            story_idea=StoryIdea(title="", description=""),
            story_details=StoryDetails(
                theme="",
                time_period="",
                location="",
                main_character="",
                conflict="",
                resolution="",
            ),
            structure=StoryStructureList(all_sections=[]),
            world=StoryWorld(
                world_description="",
                time_period_description="",
                struggles_and_challenges="",
                cultural_elements="",
                atmosphere="",
            ),
            characters=StoryCharacters(
                main_character=CharacterProfile(
                    name="",
                    personality="",
                    background="",
                    motivations="",
                    appearance="",
                ),
                villain=CharacterProfile(
                    name="",
                    personality="",
                    background="",
                    motivations="",
                    appearance="",
                ),
                supporting_characters=[],
                character_relationships=[],
            ),
            style=WritingStyle(style="", tone="", narrative_voice=""),
            plot_points=PlotPoints(all_plot_points=[]),
            outline=StoryOutline(outline=[]),
            level=level,
            draft=StoryDraft(title="", story=""),
            draft_path="",
            revised_draft_path="",
            summary="",
        )


class Chunk(BaseModel):
    data: str


# Plot Points Structure:
# --------------------------------
# Main Plot Point: {main_plot_point}
# Sub Plot Points:
# -{sub_plot_point_1}:
#     Deep Sub Plot Points:
#         -{deep_sub_plot_point_1}:
#         -{deep_sub_plot_point_2}:
#         -{deep_sub_plot_point_N}:
# -{sub_plot_point_2}:
#     Deep Sub Plot Points:
#         -{deep_sub_plot_point_1}:
#         -{deep_sub_plot_point_2}:
#         -{deep_sub_plot_point_N}:
# -{sub_plot_point_N}:
#     Deep Sub Plot Points:
#         -{deep_sub_plot_point_1}:
#         -{deep_sub_plot_point_2}:
#         -{deep_sub_plot_point_N}:
