import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import fitz
import os
import nltk

# nltk.download('punkt_tab')

def extract_file_content(path: str, is_export_image: bool = False):
    output_dir = "output_images"
    os.makedirs(output_dir, exist_ok=True)
    text = ''
    doc = fitz.open(path)
    for page_num in range(doc.page_count):
        page = doc[page_num]

        #extract text
        text += page.get_text() + '\n'
        
        #extract image
        if (is_export_image):
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_filename = f"{output_dir}/page{page_num + 1}_img{img_index + 1}.{image_ext}"
                with open(image_filename, "wb") as f:
                    f.write(image_bytes)
    return text

def chunk_text(text, parent_max_length=500, child_max_length=200, delimiter='\n'):
    paragraphs = text.split(delimiter)
    print(paragraphs)
    parent_chunks = []
    child_chunks = []
    metadata = []

    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            continue

        
        if (len(paragraph) > parent_max_length):
            paragraph = paragraph[:parent_max_length]
        parent_chunks.append(paragraph)

        # Create child chunks (sentences)
        sentences = nltk.sent_tokenize(paragraph)
        for sentence in sentences:
            if (len(sentence) > child_max_length):
                sentence = sentence[:child_max_length]
            child_chunks.append(sentence)
            metadata.append({"parent_id": f"parent_{i}", "child_id": f"child_{len(child_chunks) - 1}"})

    return parent_chunks, child_chunks, metadata




    
        
# print(text)
# path = "/home/suga/Desktop/Work/faq/santa/Script_CSKH_training_AI.pdf"
# text = extract_file_content(path, False)
# parent_chunks, child_chunks, metadata = chunk_text(text, delimiter="\n\n")
# # print(parent_chunks)
# for i, child_chunk in enumerate(child_chunks):
#     print(f"==== Child chunk {metadata[i]}: ====\n{child_chunk}\n")
# print(len(metadata))