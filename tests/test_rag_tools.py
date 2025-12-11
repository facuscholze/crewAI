"""
Test suite for RAG tools: ServiceCatalogTool, TreatmentInfoTool, and RagRetrieverTool.
Run with: pytest tests/test_rag_tools.py -v
"""

import sys
import os

# Removed ServiceCatalogTool and TreatmentInfoTool imports

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


 # ServiceCatalogTool and TreatmentInfoTool were removed; tests updated accordingly
from integrado.tools.rag_tool import RagRetrieverTool


def test_service_catalog_tool_removed():
    print("\nℹ️ ServiceCatalogTool removed; skipping catalog inline generation test")
    assert True


def test_treatment_info_tool_removed_price():
    print("\nℹ️ TreatmentInfoTool removed; skipping price-specific test")
    assert True


def test_treatment_info_tool_removed_duration():
    print("\nℹ️ TreatmentInfoTool removed; skipping duration-specific test")
    assert True


def test_treatment_info_tool_removed_all():
    print("\nℹ️ TreatmentInfoTool removed; skipping full info test")
    assert True


def test_rag_retriever_tool():
    """Test that RagRetrieverTool retrieves relevant chunks."""
    tool = RagRetrieverTool()
    result = tool._run("precio sesión evaluación", top_k=2)
    print(f"\n🔍 RagRetrieverTool (precio sesión evaluación):\n{result}\n")
    
    # Should return something
    assert result is not None and len(result) > 0, "RAG returned empty result"
    
    # Should contain source reference
    assert "[Source:" in result, "Missing source reference in RAG output"
    
    # Should contain relevant info
    assert any(word in result for word in ["Evaluación", "Evaluacion", "precio", "Precio", "$1.800", "1800"]), \
        "Expected content not found in RAG result"


def test_rag_docs_loaded():
    """Test that RAG loads documents from knowledge folder."""
    tool = RagRetrieverTool()
    docs = tool._load_documents()
    print(f"\n📚 RAG loaded {len(docs)} document chunks\n")
    
    assert len(docs) > 0, "No documents loaded from knowledge folder"
    assert len(docs) >= 10, f"Expected at least 10 chunks, got {len(docs)}"
    
    # Check that docs have required fields
    for doc in docs[:3]:
        assert 'source' in doc, "Document missing 'source' field"
        assert 'text' in doc, "Document missing 'text' field"
        assert len(doc['text']) > 0, "Document has empty text"


if __name__ == "__main__":
    print("=" * 60)
    print("Testing RAG Tools")
    print("=" * 60)
    
    try:
        test_rag_docs_loaded()
        print("✅ test_rag_docs_loaded PASSED\n")
    except AssertionError as e:
        print(f"❌ test_rag_docs_loaded FAILED: {e}\n")
    
    try:
        test_service_catalog_tool_removed()
        print("✅ test_service_catalog_tool_removed PASSED\n")
    except AssertionError as e:
        print(f"❌ test_service_catalog_tool_removed FAILED: {e}\n")
    
    try:
        test_treatment_info_tool_removed_price()
        print("✅ test_treatment_info_tool_removed_price PASSED\n")
    except AssertionError as e:
        print(f"❌ test_treatment_info_tool_removed_price FAILED: {e}\n")
    
    try:
        test_treatment_info_tool_removed_duration()
        print("✅ test_treatment_info_tool_removed_duration PASSED\n")
    except AssertionError as e:
        print(f"❌ test_treatment_info_tool_removed_duration FAILED: {e}\n")
    
    try:
        test_treatment_info_tool_removed_all()
        print("✅ test_treatment_info_tool_removed_all PASSED\n")
    except AssertionError as e:
        print(f"❌ test_treatment_info_tool_removed_all FAILED: {e}\n")
    
    try:
        test_rag_retriever_tool()
        print("✅ test_rag_retriever_tool PASSED\n")
    except AssertionError as e:
        print(f"❌ test_rag_retriever_tool FAILED: {e}\n")
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
