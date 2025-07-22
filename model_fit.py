from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

import torch

# Step 1: Load your CSV dataset
dataset = load_dataset('csv', data_files='spam_data.csv')
dataset = dataset['train'].train_test_split(test_size=0.2)

model_checkpoint = 'DeepPavlov/rubert-base-cased'
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)

def preprocess(example):
    return tokenizer(example['text'], truncation=True, padding='max_length', max_length=128)

encoded_dataset = dataset.map(preprocess, batched=True)
encoded_dataset = encoded_dataset.rename_column("label", "labels")
encoded_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'labels'])


model = AutoModelForSequenceClassification.from_pretrained(model_checkpoint, num_labels=2)


training_args = TrainingArguments(
    output_dir="./results",
    save_strategy="epoch",
    num_train_epochs=3,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    logging_dir="./logs",
    logging_steps=10,
    evaluation_strategy='epoch'
)


def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)  # or use pred.predictions > 0.5 if output logits/probs

    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='binary')
    acc = accuracy_score(labels, preds)
    return {
        'accuracy': acc,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


# Step 5: Trainer setup
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=encoded_dataset['train'],
    eval_dataset=encoded_dataset['test'],
    compute_metrics=compute_metrics
)

# Step 6: Fine-tune
trainer.train()
trainer.save_model("./rubert-spam-filter")
tokenizer.save_pretrained("./rubert-spam-filter")

#eval_results = trainer.evaluate()
#print(eval_results)

eval_output = trainer.predict(encoded_dataset['test'])
print("Labels:", eval_output.label_ids)
print("Preds logits:", eval_output.predictions[:5])

#inputs = tokenizer("Заработок на дому 10000₽ в день!", return_tensors="pt")
#outputs = model(**inputs)
#pred = torch.argmax(outputs.logits, dim=-1)
#print(pred)  # Should output 0 or 1


