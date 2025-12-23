import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader, random_split
import os
import time

# --- CONFIGURATION ---
DATA_DIR = "dataset"        # Looks for the folder you just made
MODEL_SAVE_PATH = "models/plant_doctor_vision.pth" # Will create 'models' folder if missing
BATCH_SIZE = 8              
EPOCHS = 15                  
LEARNING_RATE = 0.001
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def train_model():
    print(f"🚀 Starting Vision Training on {DEVICE}...")
    
    # 1. Define Image Transformations (Resize & Normalize)
    data_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(), 
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # 2. Load Data
    if not os.path.exists(DATA_DIR):
        print(f"❌ Error: Dataset folder '{DATA_DIR}' not found!")
        print("Please create a 'dataset' folder with subfolders (e.g., 'healthy', 'sick') inside.")
        return

    full_dataset = datasets.ImageFolder(DATA_DIR, transform=data_transforms)
    class_names = full_dataset.classes
    print(f"✅ Found {len(full_dataset)} images belonging to {len(class_names)} classes: {class_names}")

    # Safety Check: Need at least one image per class
    if len(full_dataset) == 0:
        print("❌ Error: No images found. Please add images to dataset/healthy, etc.")
        return

    # Split: 80% Training, 20% Validation
    total_count = len(full_dataset)
    # If dataset is tiny (for testing), use all for training
    if total_count < 10:
        print("⚠️  Dataset is small. Using 100% for training (Prototype Mode).")
        train_dataset = full_dataset
        val_dataset = full_dataset
        train_size = total_count
    else:
        train_size = int(0.8 * total_count)
        val_size = total_count - train_size
        train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    # 3. Load Pre-trained MobileNetV2
    print("🧠 Loading MobileNetV2 (Pre-trained)...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)

    # 4. Modify the Classifier Layer
    num_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_features, len(class_names))

    model = model.to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # 5. Training Loop
    print("🏋️ Training started...")
    start_time = time.time()

    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0
        corrects = 0

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)

            optimizer.zero_grad()

            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            corrects += torch.sum(preds == labels.data)

        epoch_loss = running_loss / train_size
        epoch_acc = corrects.double() / train_size

        print(f"   Epoch {epoch+1}/{EPOCHS} | Loss: {epoch_loss:.4f} | Acc: {epoch_acc:.4f}")

    time_elapsed = time.time() - start_time
    print(f"✅ Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s")

    # 6. Save the Model
    os.makedirs("models", exist_ok=True) # Creates 'models' folder automatically
    torch.save(model, MODEL_SAVE_PATH)
    
    # Save class names text file
    class_file = MODEL_SAVE_PATH.replace(".pth", "_classes.txt")
    with open(class_file, "w") as f:
        f.write("\n".join(class_names))
        
    print(f"💾 Model saved to: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_model()