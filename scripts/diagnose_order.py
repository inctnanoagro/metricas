import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
import json
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from metricas_lattes.batch_full_profile import (
    extract_production_sections_from_html,
    parse_section_html
)
from metricas_lattes.exports.validation_pack import _sorted_items, _group_by_production_type

def trace_order():
    fixture_path = project_root / 'tests/fixtures/lattes/full_profile/full_profile_leonardo_fraceto.html'
    print(f"Tracing order for: {fixture_path}")
    
    # Create a temp dir for the parser
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # 1. GROUND TRUTH (DOM Order)
        print("\n--- STAGE 1: HTML DOM Order (Ground Truth) ---")
        sections = extract_production_sections_from_html(fixture_path)
        
        global_items = []
        
        for section in sections:
            print(f"Checking section: {section['section_title']} (Items: {section['item_count']})")
            
            # Use ANY section that has items for the test
            if section['item_count'] > 0:
                print(f"  -> Using this section for test.")
                
                # Parse using the actual pipeline
                # Note: parse_section_html uses the title to name the temp file, which determines the parser!
                # If title is "Produções", it might use GenericParser.
                # Let's force a name that triggers Artigos parser if possible, or just see what happens.
                # Actually, let's just let it run naturally.
                
                parsed = parse_section_html(section['html_content'], section['section_title'], temp_dir)
                items = parsed['items']
                
                print(f"  -> Parser returned {len(items)} items.")
                
                if items:
                    # Store with original index from the parser list
                    for idx, item in enumerate(items):
                        item['_debug_original_index'] = idx
                        item['_debug_section'] = section['section_title']
                        # Inject fake source.production_type for grouping later
                        # We use a fixed type to ensure they group together
                        item['source'] = {'production_type': 'teste_reorder'} 
                        global_items.append(item)
                        
                        if idx < 3: 
                            print(f"    [{idx}] Num: {item.get('numero_item')} - {item.get('titulo', 'No Title')[:40]}...")
                    
                    # We only need one good section to prove the point
                    break

        if not global_items:
            print("\nWARNING: No items found to test! Exiting.")
            return

        # 2. BATCH AGGREGATION SIMULATION
        print("\n--- STAGE 2: Batch Aggregation (Simulation) ---")
        merged_items = []
        
        # Block A (Original items)
        for item in global_items:
            new_item = item.copy()
            new_item['_debug_block'] = 'A'
            merged_items.append(new_item)
            
        # Block B (Duplicated items to simulate a second block of same type)
        for item in global_items:
            new_item = item.copy()
            new_item['_debug_block'] = 'B'
            merged_items.append(new_item)
            
        print(f"Merged list size: {len(merged_items)}")
        print("Sequence in merged list (First 4):")
        for i in range(min(4, len(merged_items))):
            item = merged_items[i]
            print(f"  Idx {i}: Block {item['_debug_block']} | Num {item['numero_item']} | {item['titulo'][:30]}")
            
        print("Sequence in merged list (Transition A->B):")
        mid = len(global_items)
        if len(merged_items) > mid:
            for i in range(max(0, mid-2), min(len(merged_items), mid+2)):
                item = merged_items[i]
                print(f"  Idx {i}: Block {item['_debug_block']} | Num {item['numero_item']} | {item['titulo'][:30]}")

        # 3. EXPORT / VALIDATION PACK
        print("\n--- STAGE 3: Export (Validation Pack Sort) ---")
        
        # The export process groups by type first
        grouped = _group_by_production_type(merged_items)
        key = list(grouped.keys())[0]
        group_items = grouped[key]
        
        print(f"Grouped by '{key}'. Count: {len(group_items)}")
        
        # APPLY THE SUSPECT FUNCTION
        sorted_output = _sorted_items(group_items)
        
        print("Sequence AFTER _sorted_items (First 6):")
        reorder_detected = False
        for i in range(min(6, len(sorted_output))):
            item = sorted_output[i]
            print(f"  Idx {i}: Block {item['_debug_block']} | Num {item['numero_item']} | {item['titulo'][:30]}")
            
            # Check for interleaving: A1, B1, A2, B2
            if i == 1 and item['_debug_block'] == 'B':
                reorder_detected = True
                
        if reorder_detected:
            print("\n>>> REORDER DETECTED! <<<")
            print("The list was interleaved. Block A and Block B are mixed based on 'numero_item'.")
            print("Cause: validation_pack.py -> _sorted_items() uses 'numero_item' as key.")
        else:
             print("\nNo reorder detected in top items.")

    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    trace_order()