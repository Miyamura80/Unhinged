import dspy
from PIL import Image


class CountPeopleSignature(dspy.Signature):
    """Count the number of people in an image."""

    image: list[dspy.Image] = dspy.InputField(desc="The images to count people in")
    count: int = dspy.OutputField(desc="Number of people in the image")


# 2. Create the module using dspy.Predict
count_people_module = dspy.Predict(CountPeopleSignature)

# 3. Set up the Gemini model
lm = dspy.LM(model="gemini/gemini-2.0-flash")
dspy.settings.configure(lm=lm)

# 4. Load the images (as PIL Images)
image_paths = [
    "profile_photos/photo_1.png",
    "profile_photos/photo_2.png",
    "profile_photos/photo_3.png",
]
image = [Image.open(path) for path in image_paths] # 'image' is now a list of PIL.Image objects

# 5. Run inference
result = count_people_module(image=image)

print("Number girls detected:", result.count)