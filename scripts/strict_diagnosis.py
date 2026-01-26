
import sys
import tempfile
import shutil
from pathlib import Path
from bs4 import BeautifulSoup

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from metricas_lattes.batch_full_profile import (
    extract_production_sections_from_html,
    parse_section_html
)
from metricas_lattes.exports.validation_pack import _sorted_items, _group_by_production_type

def get_ground_truth_titles(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    titles = []
    # Logic similar to parser but simplified to just get text order
    # Artigos pattern: layout-cell-11 containing span.transform
    # We'll just grab all span.transform inside layout-cell-11 to be sure of DOM order
    cells = soup.find_all('div', class_='layout-cell-11')
    for cell in cells:
        span = cell.find('span', class_='transform')
        if span:
            # simple cleanup
            text = span.get_text(separator=' ').strip()
            # extract title part (rough heuristic for ID)
            # just take first 50 chars
            titles.append(text[:50])
    return titles

def run_diagnosis():
    fixture_path = project_root / 'tests/fixtures/lattes/full_profile/full_profile_leonardo_fraceto.html'
    print(f"DIAGNOSIS TARGET: {fixture_path.name}")

    # 1. EXTRACT SECTIONS (DOM ORDER)
    sections = extract_production_sections_from_html(fixture_path)
    
    # Find "Produções"
    target_section = None
    for s in sections:
        if "Produções" in s['section_title']:
            target_section = s
            break
            
    if not target_section:
        print("CRITICAL: Section 'Produções' not found")
        return

    print(f"\n[STAGE 1] HTML Extraction")
    print(f"Section: {target_section['section_title']}")
    
    # Ground truth from BS4 directly on this section's HTML
    truth_titles = get_ground_truth_titles(target_section['html_content'])
    print(f"Ground Truth Items (DOM): {len(truth_titles)}")
    for i, t in enumerate(truth_titles[:3]):
        print(f"  {i}: {t}...")

    # 2. PARSER OUTPUT
    print(f"\n[STAGE 2] Parser Output (parse_section_html)")
    temp_dir = Path(tempfile.mkdtemp())
    try:
        parsed = parse_section_html(target_section['html_content'], target_section['section_title'], temp_dir)
        items = parsed['items']
        
        print(f"Parsed Items: {len(items)}")
        divergence = False
        for i, item in enumerate(items[:5]):
            raw_start = item.get('raw', '')[:50]
            # Compare with ground truth (fuzzy match because parser cleans text)
            # but order should be aligned
            print(f"  {i}: [Num {item.get('numero_item')}] {raw_start}...")
            
            # Simple check against truth if index exists
            if i < len(truth_titles):
                truth = truth_titles[i]
                # Check if roughly same
                # normalize spaces
                import re
                t1 = re.sub(r'\s+', '', truth).lower()
                t2 = re.sub(r'\s+', '', raw_start).lower()
                # t2 is from parser, might be cleaner. t1 is raw soup.
                # Check if t2 is contained in t1 or vice versa or overlap
                # Actually, just visual check for report is enough as requested.
                pass

        # 3. BATCH (Single Section Simulation)
        print(f"\n[STAGE 3] Batch Aggregation")
        # In batch, items are just appended. 
        # If we only have one section, nothing changes.
        # But if we have duplicates (common in tests/bugs), let's see.
        # For strict diagnosis of ONE path, we assume batch just holds this list.
        batch_items = items  # No change for single section
        print(f"Batch Items: {len(batch_items)}")
        
        # 4. EXPORT (Validation Pack)
        print(f"\n[STAGE 4] Export (_sorted_items)")
        
        # Validation pack groups by production_type.
        # For this file, it's 'artigos-completos-publicados-em-periodicos'
        grouped = _group_by_production_type(batch_items)
        # Should be one group
        if not grouped:
            print("No groups found?")
            return
            
        first_group_key = list(grouped.keys())[0]
        group_list = grouped[first_group_key]
        
        # PRE-SORT STATE
        print(f"Group: {first_group_key}")
        print("Pre-Sort Top 3:")
        for i, item in enumerate(group_list[:3]):
            print(f"  {i}: [Num {item.get('numero_item')}] {item.get('raw', '')[:50]}...")
            
        # APPLY SORT
        sorted_list = _sorted_items(group_list)
        
        print("Post-Sort Top 3:")
        order_changed = False
        for i, item in enumerate(sorted_list[:3]):
            print(f"  {i}: [Num {item.get('numero_item')}] {item.get('raw', '')[:50]}...")
            if item.get('raw') != group_list[i].get('raw'):
                order_changed = True
                
        if order_changed:
            print("\n!!! ORDER CHANGED IN EXPORT !!!")
        else:
            print("\nOrder preserved in Export (for single section case).")
            
        # 5. MULTI-SECTION SIMULATION (The real killer)
        print(f"\n[STAGE 5] Multi-Section Collision Test")
        # Create 2 fake items with SAME numero_item but different content order
        fake_items = [
            {'numero_item': 1, 'raw': 'Section A - Item 1', 'source': {'production_type': 'artigos'}},
            {'numero_item': 2, 'raw': 'Section A - Item 2', 'source': {'production_type': 'artigos'}},
            {'numero_item': 1, 'raw': 'Section B - Item 1', 'source': {'production_type': 'artigos'}},
            {'numero_item': 2, 'raw': 'Section B - Item 2', 'source': {'production_type': 'artigos'}},
        ]
        print("Input (Batch Order):")
        for x in fake_items: print(f"  Num {x['numero_item']} | {x['raw']}")
        
        sorted_fake = _sorted_items(fake_items)
        print("Output (Export Sort):")
        for x in sorted_fake: print(f"  Num {x['numero_item']} | {x['raw']}")
        
        if sorted_fake[1]['raw'] == 'Section B - Item 1':
             print("!!! INTERLEAVING DETECTED !!!")

    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    run_diagnosis()
