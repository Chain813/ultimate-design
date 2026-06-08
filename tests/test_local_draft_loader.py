# -*- coding: utf-8 -*-
import os
from src.engines.local_draft_loader import load_thesis_from_draft, get_combined_references

def test_load_thesis_from_draft():
    draft_path = r"C:\Users\23902\Desktop\陈礼冲 毕设\毕业设计答辩稿_陈礼冲_202111003.docx"
    if not os.path.exists(draft_path):
        # Skip if the file doesn't exist on the environment (e.g. CI)
        return
        
    chapters, metadata = load_thesis_from_draft()
    assert isinstance(chapters, dict)
    assert len(chapters) > 0
    assert "1.1" in chapters
    assert "5.3" in chapters
    
    assert "abstract_cn" in metadata
    assert "keywords_cn" in metadata
    assert "abstract_en" in metadata
    assert "keywords_en" in metadata
    assert "acknowledgments" in metadata
    assert "references" in metadata

def test_get_combined_references():
    draft_refs = "[1] Test ref 1\n[2] Test ref 2"
    combined = get_combined_references(draft_refs)
    assert isinstance(combined, str)
    # Even if references folder doesn't exist, combined should contain the draft references
    assert "Test ref 1" in combined
    assert "Test ref 2" in combined
