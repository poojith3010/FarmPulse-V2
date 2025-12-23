import pypdf
import pathlib

# Define the path to your knowledge base folder
KB_PATH = pathlib.Path("knowledge_base")

def convert_pdfs_to_text():
    """
    Looks in the KB_PATH, finds all .pdf files, and saves
    a new .txt file with the extracted text.
    """
    print("Starting PDF conversion...")
    
    # Loop through all files in the knowledge_base folder
    for pdf_file in KB_PATH.glob("*.pdf"):
        
        # 1. Open the PDF file
        print(f"--- Processing: {pdf_file.name}")
        pdf_reader = pypdf.PdfReader(pdf_file)
        
        # 2. Extract text from all pages
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text() + "\n"
        
        # 3. Define the new .txt output filename
        # This changes "MyFile.pdf" to "MyFile.txt"
        txt_file_path = pdf_file.with_suffix(".txt")
        
        # 4. Save the extracted text to the new .txt file
        with open(txt_file_path, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"--- Saved: {txt_file_path.name}")

    print("Conversion complete!")

if __name__ == "__main__":
    convert_pdfs_to_text()