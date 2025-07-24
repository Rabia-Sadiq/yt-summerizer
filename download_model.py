from transformers import BartForConditionalGeneration, BartTokenizer

print("Downloading BART model...")
model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")

model.save_pretrained("./bart_model")
tokenizer.save_pretrained("./bart_model")
print("[✓] Saved locally in ./bart_model")