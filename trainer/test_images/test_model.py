import torch
from torchvision import models, transforms
import torch.nn as nn
from PIL import Image

model = models.efficientnet_v2_s(weights=None)
model.classifier[1] = nn.Linear(model.classifier[1].in_features, 120)
model.load_state_dict(torch.load("d:/Projects/DogFinder/dog_model.pth", weights_only=False))
feature_extractor = torch.nn.Sequential(*list(model.children())[:-1])
feature_extractor.eval()

transform = transforms.Compose([
    transforms.Resize((384, 384)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

def get_embedding(img_path):
    image = Image.open(img_path).convert("RGB")
    tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        embedding = feature_extractor(tensor)
    return embedding.squeeze()

jade1   = get_embedding("d:/Projects/DogFinder/test_images/jade1.jpg")
jade2   = get_embedding("d:/Projects/DogFinder/test_images/jade2.jpg")
other   = get_embedding("d:/Projects/DogFinder/test_images/other_dog_close.png")

sim_same  = torch.nn.functional.cosine_similarity(jade1.unsqueeze(0), jade2.unsqueeze(0))
sim_other = torch.nn.functional.cosine_similarity(jade1.unsqueeze(0), other.unsqueeze(0))
gap       = sim_same.item() - sim_other.item()

print(f"Jade vs Jade (same dog):       {sim_same.item():.4f}")
print(f"Jade vs Black Lab (diff dog):  {sim_other.item():.4f}")
print(f"Gap:                           {gap:.4f}")

if gap > 0.2:
    print("MATCHING ALGORITHM WORKS - Gap is large enough to reliably distinguish dogs")
elif gap > 0.1:
    print("MARGINAL - Works but threshold tuning needed")
else:
    print("WEAK - Model struggles to distinguish these two dogs")