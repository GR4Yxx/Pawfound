import torch
from torchvision import models, transforms
from PIL import Image
import os

# Load model, strip the classification head
model = models.efficientnet_v2_s(weights="IMAGENET1K_V1")
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

# Two Chihuahuas vs one Maltese
chihuahua_dir = "d:/Projects/DogFinder/data/Images/n02085620-Chihuahua"
maltese_dir = "d:/Projects/DogFinder/data/Images/n02085936-Maltese_dog"

chihuahua_imgs = os.listdir(chihuahua_dir)
maltese_imgs = os.listdir(maltese_dir)

emb_chi_1 = get_embedding(f"{chihuahua_dir}/{chihuahua_imgs[0]}")
emb_chi_2 = get_embedding(f"{chihuahua_dir}/{chihuahua_imgs[1]}")
emb_maltese = get_embedding(f"{maltese_dir}/{maltese_imgs[0]}")

sim_same_breed = torch.nn.functional.cosine_similarity(
    emb_chi_1.unsqueeze(0), emb_chi_2.unsqueeze(0)
)
sim_diff_breed = torch.nn.functional.cosine_similarity(
    emb_chi_1.unsqueeze(0), emb_maltese.unsqueeze(0)
)

print(f"Embedding shape: {emb_chi_1.shape}")
print(f"Chihuahua vs Chihuahua similarity: {sim_same_breed.item():.4f}")
print(f"Chihuahua vs Maltese similarity:   {sim_diff_breed.item():.4f}")
print()
if sim_same_breed > sim_diff_breed:
    print("✅ Model correctly scores same breed HIGHER than different breed")
else:
    print("⚠️ Scores unexpected - may need fine tuning")