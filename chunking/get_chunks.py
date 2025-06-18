from typing import List

# Get source data
import requests
import re

# Split the text into units (words, in this case)
def word_splitter(source_text: str) -> List[str]:
    source_text = re.sub("\s+", " ", source_text)  # Replace multiple whitespces
    return re.split("\s", source_text)  # Split by single whitespace

def get_chunks_fixed_size_with_overlap(text: str, chunk_size: int, overlap_fraction: float) -> List[str]:
    text_words = word_splitter(text)
    overlap_int = int(chunk_size * overlap_fraction)
    chunks = []
    for i in range(0, len(text_words), chunk_size):
        chunk_words = text_words[max(i - overlap_int, 0): i + chunk_size]
        chunk = " ".join(chunk_words)
        chunks.append(chunk)
    return chunks

async def getFixedSizeChunks(sourceText: str, chunkSize: int) -> List[str]:
    # Chunk text by number of words
    chunks = get_chunks_fixed_size_with_overlap(sourceText, chunkSize, overlap_fraction=0.2)
    # Print outputs to screen
    print(f"{len(chunks)} chunks returned.")
    for i in range(3):
        print(f"Chunk {i+1}: {chunks[i]}")
    return chunks

async def getVariableSizeChunks(sourceText: str, marker: str) -> List[str]:
    # Chunk text by marker
    chunks = sourceText.split(marker)
    # Print outputs to screen
    print(f"{len(chunks)} chunks returned.")
    for i in range(3):
        print(f"Chunk {i+1}: {chunks[i]}")
    return chunks

async def getVariableSizeSubChunks(parentChunks: List[str], submarker: str) -> List[str]:
    # Chunk text by marker
    chunks = []
    for parentChunk in parentChunks:
        subChunks = parentChunk.split(submarker)
        chunks.extend(subChunks)
    # Print outputs to screen
    print(f"{len(chunks)} chunks returned.")
    for i in range(3):
        print(f"Chunk {i+1}: {chunks[i]}")
    return chunks

async def getFamilyChunks(sourceText: str, marker: str, submarker: str, minLength: int) -> List[str]:
    # Chunk text by marker and submarker
    newChunks = list()
    buffer = ""
    
    chunks = sourceText.split(marker)
    for chunk in chunks:
        subChunks = chunk.split(submarker)
        for subChunk in subChunks:
            newBuffer = buffer + subChunk
            newBufferWords = word_splitter(newBuffer)
            
            if len(newBufferWords) < minLength:
                buffer = newBuffer
            else:
                newChunks.append(newBuffer)
                buffer = ""
        
    if len(buffer) > 0:
        newChunks.append(buffer)
    return newChunks

async def getMixedChunks(sourceText: str, marker: str, submarker: str, minLength: int) -> List[str]:
    # Chunk text by marker
    newChunks = list()
    buffer = ""
    
    chunks = sourceText.split(marker)
    for chunk in chunks:
        newBuffer = buffer + chunk
        newBufferWords = word_splitter(newBuffer)
        
        if len(newBufferWords) < minLength:
            buffer = newBuffer
        else:
            newChunks.append(newBuffer)
            buffer = ""
        
    if len(buffer) > 0:
        newChunks.append(buffer)
    return newChunks

