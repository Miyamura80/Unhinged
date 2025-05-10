import dspy
from typing import Optional
from src.models.profile import Profile, DatingStyle, Lifestyle, Education, PhotoAnalysis
from src.agent.react_agent import ReactAgent
from datetime import datetime
from PIL import Image
import glob
import os
import asyncio
from langfuse.decorators import observe

class InferPhotoFeatures(dspy.Signature):
    """Analyze a single profile photo and extract features."""
    system_prompt: str = dspy.InputField(desc="System prompt for the agent")
    image: dspy.Image = dspy.InputField(desc="Single PIL Image to analyze")
    
    # Physical attributes
    has_freckles: Optional[bool] = dspy.OutputField(desc="Whether the person has freckles")
    hair_color: Optional[str] = dspy.OutputField(desc="Hair color")
    has_piercings: Optional[bool] = dspy.OutputField(desc="Whether the person has piercings")
    makeup_level: Optional[int] = dspy.OutputField(desc="Level of makeup (1-5 scale, 1 being minimal, 5 being heavy)")
    
    # Photo context
    activities: Optional[list[str]] = dspy.OutputField(desc="Activities or actions shown in the photo")
    location_type: Optional[str] = dspy.OutputField(desc="Type of location (indoor, outdoor, social, etc.)")
    style: Optional[str] = dspy.OutputField(desc="Style of the photo (casual, formal, sporty, etc.)")
    
    # Inferred profile information
    bio: Optional[str] = dspy.OutputField(desc="Inferred bio or description based on the photo")
    age: Optional[int] = dspy.OutputField(desc="Estimated age range")
    interests: Optional[list[str]] = dspy.OutputField(desc="Inferred interests from the photo")
    personality_traits: Optional[list[str]] = dspy.OutputField(desc="Inferred personality traits from the photo")


class InferProfileFeatures(dspy.Signature):
    """Aggregate features from all photos and infer overall profile characteristics."""
    system_prompt: str = dspy.InputField(desc="System prompt for the agent")
    photo_analyses: list[dict] = dspy.InputField(desc="List of photo analysis results")
    
    # Aggregated profile information
    bio: Optional[str] = dspy.OutputField(desc="Combined bio based on all photos")
    age: Optional[int] = dspy.OutputField(desc="Most likely age based on all photos")
    location: Optional[str] = dspy.OutputField(desc="Inferred location or city")
    job: Optional[str] = dspy.OutputField(desc="Inferred occupation or job")
    
    # Education
    education: Optional[list[dict]] = dspy.OutputField(desc="Inferred education details")
    
    # Lifestyle and preferences
    party_frequency: Optional[int] = dspy.OutputField(desc="Party frequency (1-5 scale)")
    drug_usage: Optional[int] = dspy.OutputField(desc="Drug usage level (1-5 scale)")
    dating_style: Optional[str] = dspy.OutputField(desc="Dating style (traditional, casual, adventurous)")
    lifestyle: Optional[str] = dspy.OutputField(desc="Lifestyle (active, relaxed, party, intellectual)")
    
    # Inferred attributes
    inferred_interests: Optional[list[str]] = dspy.OutputField(desc="Combined list of inferred interests")
    inferred_personality_traits: Optional[list[str]] = dspy.OutputField(desc="Combined list of inferred personality traits")


def load_prompt(prompt_type: str) -> str:
    """Load the appropriate prompt from the prompts file."""
    prompt_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "feature_extractor.txt")
    with open(prompt_file, 'r') as f:
        content = f.read()
    
    if prompt_type == "photo":
        return content.split("# Profile Aggregation Prompt")[0].split("# Individual Photo Analysis Prompt")[1].strip()
    else:
        return content.split("# Profile Aggregation Prompt")[1].strip()

@observe()
async def analyze_profile(
    profile_images: list[str],
) -> Profile:
    """
    Analyze a Hinge profile using only the profile images.
    
    Args:
        profile_images: List of paths to profile images
    
    Returns:
        Profile object with analyzed features
    """
    # Load images as PIL Images
    images = [Image.open(path) for path in profile_images]
    
    # Initialize the ReactAgent with our InferPhotoFeatures signature for individual photo analysis
    photo_agent = ReactAgent(
        agent_signature=InferPhotoFeatures,
        model_name="gemini/gemini-2.0-flash"
    )
    
    # Analyze each photo individually
    photo_analyses = []
    for image in images:
        result = await photo_agent.run(
            user_id="",  # No user context needed
            system_prompt=load_prompt("photo"),
            image=image
        )
        photo_analyses.append(result)
    
    # Initialize the ReactAgent with our InferProfileFeatures signature for overall analysis
    profile_agent = ReactAgent(
        agent_signature=InferProfileFeatures,
        model_name="gemini/gemini-2.0-flash"
    )
    
    # Run the overall profile analysis
    profile_result = await profile_agent.run(
        user_id="",  # No user context needed
        system_prompt=load_prompt("profile"),
        photo_analyses=photo_analyses
    )
    
    # Convert photo analyses to PhotoAnalysis objects
    photo_objects = [
        PhotoAnalysis(
            has_freckles=analysis.has_freckles,
            hair_color=analysis.hair_color,
            has_piercings=analysis.has_piercings,
            makeup_level=analysis.makeup_level,
            activities=analysis.activities or [],
            location_type=analysis.location_type,
            style=analysis.style
        )
        for analysis in photo_analyses
    ]
    
    # Convert education data to Education objects
    education_objects = []
    if profile_result.education:
        for edu in profile_result.education:
            education_objects.append(Education(
                institution=edu.get('institution', ''),
                degree=edu.get('degree'),
                field=edu.get('field'),
                graduation_year=edu.get('graduation_year')
            ))
    
    # Create and return the Profile object
    return Profile(
        name="",  # Name not provided in input
        age=profile_result.age or 0,
        location=profile_result.location or "",
        bio=profile_result.bio or "",
        created_at=datetime.now(),
        photos=photo_objects,
        education=education_objects,
        party_frequency=profile_result.party_frequency,
        drug_usage=profile_result.drug_usage,
        dating_style=DatingStyle(profile_result.dating_style.lower()) if profile_result.dating_style else DatingStyle.UNKNOWN,
        lifestyle=Lifestyle(profile_result.lifestyle.lower()) if profile_result.lifestyle else Lifestyle.UNKNOWN,
        inferred_interests=profile_result.inferred_interests or [],
        inferred_personality_traits=profile_result.inferred_personality_traits or []
    )

@observe()
async def main():
    # Get all profile photos
    profile_photos = sorted(glob.glob("profile_photos/photo_*.png"))
    
    # Run analysis
    profile = await analyze_profile(profile_images=profile_photos)
    
    # Print results
    print("\nProfile Analysis Results:")
    print(f"Age: {profile.age}")
    print(f"Location: {profile.location}")
    print(f"Bio: {profile.bio}")
    
    print("\nPhoto Analysis:")
    for i, photo in enumerate(profile.photos, 1):
        print(f"\nPhoto {i}:")
        print(f"Location: {photo.location_type}")
        print(f"Style: {photo.style}")
        print(f"Activities: {', '.join(photo.activities)}")
        print(f"Physical Attributes:")
        print(f"  Has Freckles: {photo.has_freckles}")
        print(f"  Hair Color: {photo.hair_color}")
        print(f"  Has Piercings: {photo.has_piercings}")
        print(f"  Makeup Level: {photo.makeup_level}")
    
    print("\nAggregated Physical Attributes:")
    print(f"Has Freckles: {profile.has_freckles}")
    print(f"Hair Color: {profile.hair_color}")
    print(f"Has Piercings: {profile.has_piercings}")
    print(f"Makeup Level: {profile.makeup_level}")
    
    print("\nLifestyle:")
    print(f"Party Frequency: {profile.party_frequency}")
    print(f"Drug Usage: {profile.drug_usage}")
    print(f"Dating Style: {profile.dating_style}")
    print(f"Lifestyle: {profile.lifestyle}")
    
    print("\nInferred Interests: {', '.join(profile.inferred_interests)}")
    print(f"Inferred Personality Traits: {', '.join(profile.inferred_personality_traits)}")


if __name__ == "__main__":
    asyncio.run(main())
