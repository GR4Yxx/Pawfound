import urllib.request
import tarfile
import os

# Create data directory
os.makedirs("d:/Projects/DogFinder/data", exist_ok=True)

# Download Stanford Dogs Dataset directly
print("Downloading images...")
urllib.request.urlretrieve(
    "http://vision.stanford.edu/aditya86/ImageNetDogs/images.tar",
    "d:/Projects/DogFinder/data/images.tar"
)

print("Downloading annotations...")
urllib.request.urlretrieve(
    "http://vision.stanford.edu/aditya86/ImageNetDogs/annotation.tar",
    "d:/Projects/DogFinder/data/annotation.tar"
)

print("Extracting...")
with tarfile.open("d:/Projects/DogFinder/data/images.tar") as tar:
    tar.extractall("d:/Projects/DogFinder/data/")

print("Done!")