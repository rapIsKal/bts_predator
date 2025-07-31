from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

model_path = "./rubert-spam-filter"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

model.eval()

def predict(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        predicted_class = torch.argmax(logits, dim=1).item()
        confidence = torch.softmax(logits, dim=1)[0][predicted_class].item()

    return predicted_class, confidence


if __name__ == "__main__":
    example_text = "Работа без вложений, пиши в лс"
    label, score = predict(example_text)

    print(f"Input: {example_text}")
    print(f"Predicted label: {label} ({'SPAM' if label == 1 else 'NOT SPAM'})")
    print(f"Confidence: {score:.2f}")
