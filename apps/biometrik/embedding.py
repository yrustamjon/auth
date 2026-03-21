from deepface import DeepFace
import numpy as np

def extract_embedding(image_path):

    result = DeepFace.represent(
        img_path=image_path,
        model_name="Facenet",
        enforce_detection=True
    )

    embedding = np.array(result[0]["embedding"])

    return embedding.tobytes()