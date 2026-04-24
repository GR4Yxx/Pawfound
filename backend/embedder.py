import os
import io

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_DIM = 1280
_MODEL_PATH = os.getenv("MODEL_PATH", "/trainer/dog_model.pth")

_transform = transforms.Compose([
    transforms.Resize((384, 384)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

_model = None       # embedding model (features only)
_classifier = None  # full model with classification head
_device = None

_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "trainer", "data", "Images")

def _get_breed_labels() -> list[str]:
    """Derive breed labels from the dataset folder names in the same order ImageFolder uses (sorted)."""
    if not os.path.isdir(_IMAGES_DIR):
        return []
    folders = sorted(os.listdir(_IMAGES_DIR))
    labels = []
    for folder in folders:
        # e.g. "n02085620-Chihuahua" -> "Chihuahua"
        # e.g. "n02099601-golden_retriever" -> "Golden Retriever"
        name = folder.split("-", 1)[-1].replace("_", " ").title()
        labels.append(name)
    return labels


def _load_model():
    global _model, _device
    if _model is not None:
        return

    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    base = models.efficientnet_v2_s(weights=None)
    base.classifier[1] = nn.Linear(base.classifier[1].in_features, 120)

    state_dict = torch.load(
        _MODEL_PATH,
        map_location=_device,
        weights_only=True,
    )
    base.load_state_dict(state_dict)

    # Strip the classification head — keep features + adaptive pool only
    _model = nn.Sequential(base.features, base.avgpool, nn.Flatten())
    _model.to(_device)
    _model.eval()


def _load_classifier():
    global _classifier, _device
    if _classifier is not None:
        return

    if _device is None:
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    base = models.efficientnet_v2_s(weights=None)
    base.classifier[1] = nn.Linear(base.classifier[1].in_features, 120)

    state_dict = torch.load(
        _MODEL_PATH,
        map_location=_device,
        weights_only=True,
    )
    base.load_state_dict(state_dict)
    _classifier = base
    _classifier.to(_device)
    _classifier.eval()


def get_embedding(image_bytes: bytes) -> list[float]:
    """Return a 1280-dim embedding vector for the given raw image bytes."""
    _load_model()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(image).unsqueeze(0).to(_device)
    with torch.no_grad():
        embedding = _model(tensor)
    return embedding.squeeze().cpu().tolist()


def predict_breed(image_bytes: bytes, top_k: int = 3) -> list[dict]:
    """Return top-k breed predictions with confidence scores."""
    _load_classifier()
    labels = _get_breed_labels()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(image).unsqueeze(0).to(_device)
    with torch.no_grad():
        logits = _classifier(tensor)
        probs = torch.softmax(logits, dim=1).squeeze()
    top = torch.topk(probs, top_k)
    return [
        {"breed": labels[idx] if idx < len(labels) else f"Class {idx}", "confidence": round(float(probs[idx]), 4)}
        for idx in top.indices.tolist()
    ]
