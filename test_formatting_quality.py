#!/usr/bin/env python3
"""
Comprehensive formatting quality diagnostic script.

Analyzes input PDFs and produces a detailed report of:
- Page structure (tables, lists, links, images, alignment)
- Span-level formatting details
- Potential problems the current pipeline would create
- Before/after translation comparison (single page per doc)

Usage:
    python3 test_formatting_quality.py [--translate] [--page N]
    
    --translate: Also run translation on page 0 and save output
    --page N: Process only page N (default: 0)
"""
import sys
import os
import re
import logging
import argparse
from pathlib import Path

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pymupdf

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output/formatting_test")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def analyze_page_structure(page: pymupdf.Page, page_num: int) -> dict:
    """Analyze a single page's structure and return diagnostic info."""
    rect = page.rect
    pw, ph = rect.width, rect.height
    
    report = {
        "page_num": page_num,
        "size": f"{pw:.0f}x{ph:.0f}",
        "rotation": page.rotation,
        "tables": [],
        "links": [],
        "images": [],
        "blocks": [],
        "lists_detected": [],
        "alignment_info": [],
        "formatting_issues": [],
    }
    
    # ── Tables ──
    try:
        tables = page.find_tables()
        for i, tab in enumerate(tables.tables):
            cells_data = tab.extract()
            report["tables"].append({
                "index": i,
                "bbox": tuple(round(x, 1) for x in tab.bbox),
                "rows": tab.row_count,
                "cols": tab.col_count,
                "sample": cells_data[0] if cells_data else [],
            })
    except Exception as e:
        report["formatting_issues"].append(f"Table detection failed: {e}")
    
    # ── Links ──
    links = page.get_links()
    for link in links:
        report["links"].append({
            "kind": link.get("kind"),
            "from": tuple(round(x, 1) for x in link.get("from", (0,0,0,0))),
            "uri": link.get("uri", "")[:80],
            "page": link.get("page", -1),
        })
    
    # ── Images ──
    images = page.get_images(full=True)
    for img in images:
        xref = img[0]
        try:
            rects = page.get_image_rects(xref)
            for r in rects:
                coverage = (r.width * r.height) / (pw * ph) if pw * ph > 0 else 0
                report["images"].append({
                    "xref": xref,
                    "bbox": tuple(round(x, 1) for x in r),
                    "coverage": f"{coverage:.1%}",
                })
        except Exception:
            pass
    
    # ── Text block analysis ──
    text_dict = page.get_text("dict", sort=True)
    all_sizes = []
    all_x0s = []
    
    for block in text_dict.get("blocks", []):
        if "lines" not in block:
            continue
        
        block_bbox = block.get("bbox", (0, 0, 0, 0))
        block_info = {
            "bbox": tuple(round(x, 1) for x in block_bbox),
            "lines": [],
            "is_table_area": False,
        }
        
        # Check if block overlaps a detected table
        for tab in report["tables"]:
            tb = tab["bbox"]
            # Check overlap
            if (block_bbox[0] < tb[2] and block_bbox[2] > tb[0] and
                block_bbox[1] < tb[3] and block_bbox[3] > tb[1]):
                block_info["is_table_area"] = True
                break
        
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            
            line_text = "".join(s.get("text", "") for s in spans)
            if not line_text.strip():
                continue
            
            # Collect sizes for page-level stats
            for s in spans:
                all_sizes.append(s.get("size", 11))
            
            line_x0 = line.get("bbox", (0,))[0]
            all_x0s.append(line_x0)
            
            line_info = {
                "text": line_text[:80],
                "x0": round(line_x0, 1),
                "y0": round(line.get("bbox", (0, 0))[1], 1),
                "size": round(spans[0].get("size", 11), 1),
                "font": spans[0].get("font", ""),
                "bold": bool(spans[0].get("flags", 0) & 16) or "Bold" in spans[0].get("font", ""),
                "italic": bool(spans[0].get("flags", 0) & 2) or "Italic" in spans[0].get("font", ""),
                "color": spans[0].get("color", 0),
                "num_spans": len(spans),
            }
            
            # Detect bullet/list patterns
            stripped = line_text.strip()
            bullet_patterns = [
                (r'^[•●○◦▪▸▹–—-]\s', "bullet"),
                (r'^\d+[.)]\s', "numbered"),
                (r'^[a-z][.)]\s', "lettered"),
                (r'^[ivxlcdm]+[.)]\s', "roman"),
                (r'^[A-Z][.)]\s', "cap-lettered"),
            ]
            for pat, kind in bullet_patterns:
                if re.match(pat, stripped):
                    report["lists_detected"].append({
                        "kind": kind,
                        "text": stripped[:60],
                        "x0": line_info["x0"],
                        "y0": line_info["y0"],
                    })
                    break
            
            block_info["lines"].append(line_info)
        
        if block_info["lines"]:
            report["blocks"].append(block_info)
    
    # ── Alignment detection ──
    if all_x0s and all_sizes:
        avg_size = sum(all_sizes) / len(all_sizes)
        # Find the most common x0 (left margin)
        x0_rounded = [round(x, 0) for x in all_x0s]
        if x0_rounded:
            from collections import Counter
            x0_counts = Counter(x0_rounded)
            most_common_x0 = x0_counts.most_common(1)[0][0]
            
            # Check right alignment
            right_edges = []
            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                for line in block.get("lines", []):
                    bbox = line.get("bbox", (0, 0, 0, 0))
                    right_edges.append(round(bbox[2], 0))
            
            if right_edges:
                right_counts = Counter(right_edges)
                most_common_right = right_counts.most_common(1)[0][0]
                
                # If right edges are consistent → justified text
                right_std = (sum((r - most_common_right)**2 for r in right_edges) / len(right_edges)) ** 0.5
                
                if right_std < 10:
                    alignment = "justified"
                elif right_std < 30:
                    alignment = "likely_justified"
                else:
                    alignment = "left_aligned"
                
                report["alignment_info"] = {
                    "detected": alignment,
                    "left_margin": most_common_x0,
                    "right_margin": most_common_right,
                    "right_edge_stddev": round(right_std, 1),
                    "page_width": round(pw, 1),
                    "avg_font_size": round(avg_size, 1),
                    "unique_x0_positions": len(x0_counts),
                }
    
    # ── Typographic characters check ──
    full_text = page.get_text("text")
    typo_chars = {
        "guillemets «»": len(re.findall(r'[«»]', full_text)),
        "curly quotes ""''": len(re.findall(r'[""'']', full_text)),
        "en-dash –": full_text.count('–'),
        "em-dash —": full_text.count('—'),
        "ellipsis …": full_text.count('…'),
        "non-breaking space": full_text.count('\u00a0'),
    }
    report["typographic_chars"] = {k: v for k, v in typo_chars.items() if v > 0}
    
    return report


def format_report(report: dict) -> str:
    """Format a page report as readable text."""
    lines = []
    lines.append(f"  Page {report['page_num']+1} ({report['size']}, rotation={report['rotation']})")
    
    # Tables
    if report["tables"]:
        lines.append(f"    📊 TABLES: {len(report['tables'])}")
        for t in report["tables"]:
            lines.append(f"       Table {t['index']}: {t['rows']}x{t['cols']} at {t['bbox']}")
    
    # Links
    if report["links"]:
        lines.append(f"    🔗 LINKS: {len(report['links'])}")
        for l in report["links"][:5]:
            lines.append(f"       kind={l['kind']} uri={l['uri'][:50]}")
        if len(report["links"]) > 5:
            lines.append(f"       ... and {len(report['links'])-5} more")
    
    # Images
    if report["images"]:
        lines.append(f"    🖼️  IMAGES: {len(report['images'])}")
        for img in report["images"][:3]:
            lines.append(f"       xref={img['xref']} coverage={img['coverage']} bbox={img['bbox']}")
    
    # Lists
    if report["lists_detected"]:
        lines.append(f"    📝 LISTS DETECTED: {len(report['lists_detected'])}")
        kinds = set(l["kind"] for l in report["lists_detected"])
        lines.append(f"       Types: {', '.join(kinds)}")
        for l in report["lists_detected"][:3]:
            lines.append(f"       [{l['kind']}] {l['text'][:50]}")
    
    # Alignment
    if report["alignment_info"]:
        ai = report["alignment_info"]
        lines.append(f"    📐 ALIGNMENT: {ai['detected']} (right-edge σ={ai['right_edge_stddev']})")
        lines.append(f"       Left margin: {ai['left_margin']}, Right margin: {ai['right_margin']}")
        lines.append(f"       Avg font: {ai['avg_font_size']}pt, {ai['unique_x0_positions']} unique x0 positions")
    
    # Typographic chars
    if report.get("typographic_chars"):
        lines.append(f"    ✏️  TYPOGRAPHIC CHARS:")
        for k, v in report["typographic_chars"].items():
            lines.append(f"       {k}: {v}")
    
    # Block summary
    lines.append(f"    📄 BLOCKS: {len(report['blocks'])}")
    table_blocks = sum(1 for b in report["blocks"] if b["is_table_area"])
    if table_blocks:
        lines.append(f"       ⚠️  {table_blocks} blocks overlap table areas (would be mangled!)")
    
    # Formatting issues
    if report["formatting_issues"]:
        lines.append(f"    ⚠️  ISSUES:")
        for issue in report["formatting_issues"]:
            lines.append(f"       - {issue}")
    
    return "\n".join(lines)


def translate_single_page(pdf_path: str, page_num: int = 0) -> tuple:
    """
    Translate a single page and return (original_doc_bytes, translated_doc_bytes).
    Returns (None, None) if translation fails.
    """
    try:
        from app.core.pdf_processor import PDFProcessor
        from app.core.translator import Translator
        from app.core.config import OPUS_MODEL_MAP
        
        processor = PDFProcessor(pdf_path)
        
        if page_num >= processor.page_count:
            log.warning(f"Page {page_num} out of range (max {processor.page_count-1})")
            return None, None
        
        # Initialize translator (en->it as default test)
        translator = Translator("en", "it")
        
        # Translate
        translated_doc = processor.translate_page(
            page_num,
            translator,
            text_color=(0, 0, 0),
            use_original_color=True,
            preserve_font_style=True,
            preserve_line_breaks=True,
            ocr_language="en"
        )
        
        if translated_doc:
            translated_bytes = translated_doc.tobytes()
            
            # Also get original page as separate doc for comparison
            orig_doc = pymupdf.open()
            orig_doc.insert_pdf(processor.document, from_page=page_num, to_page=page_num)
            orig_bytes = orig_doc.tobytes()
            orig_doc.close()
            
            translated_doc.close()
            processor.close()
            return orig_bytes, translated_bytes
        
        processor.close()
        return None, None
        
    except Exception as e:
        log.error(f"Translation failed: {e}", exc_info=True)
        return None, None


def compare_page_metrics(orig_bytes: bytes, trans_bytes: bytes) -> dict:
    """Compare original and translated page metrics."""
    orig_doc = pymupdf.open(stream=orig_bytes, filetype="pdf")
    trans_doc = pymupdf.open(stream=trans_bytes, filetype="pdf")
    
    orig_page = orig_doc[0]
    trans_page = trans_doc[0]
    
    # Extract text stats
    orig_dict = orig_page.get_text("dict")
    trans_dict = trans_page.get_text("dict")
    
    def get_text_stats(d):
        blocks = [b for b in d.get("blocks", []) if "lines" in b]
        total_lines = 0
        total_chars = 0
        sizes = []
        y_positions = []
        for b in blocks:
            for line in b.get("lines", []):
                total_lines += 1
                for span in line.get("spans", []):
                    total_chars += len(span.get("text", ""))
                    sizes.append(span.get("size", 11))
                    y_positions.append(span.get("bbox", (0, 0, 0, 0))[1])
        return {
            "blocks": len(blocks),
            "lines": total_lines,
            "chars": total_chars,
            "avg_size": round(sum(sizes)/len(sizes), 1) if sizes else 0,
            "min_y": round(min(y_positions), 1) if y_positions else 0,
            "max_y": round(max(y_positions), 1) if y_positions else 0,
            "y_span": round(max(y_positions) - min(y_positions), 1) if y_positions else 0,
        }
    
    orig_stats = get_text_stats(orig_dict)
    trans_stats = get_text_stats(trans_dict)
    
    # Check link preservation
    orig_links = orig_page.get_links()
    trans_links = trans_page.get_links()
    
    # Check image preservation
    orig_images = orig_page.get_images()
    trans_images = trans_page.get_images()
    
    comparison = {
        "original": orig_stats,
        "translated": trans_stats,
        "links_orig": len(orig_links),
        "links_trans": len(trans_links),
        "links_lost": len(orig_links) - len(trans_links),
        "images_orig": len(orig_images),
        "images_trans": len(trans_images),
        "y_span_ratio": round(trans_stats["y_span"] / orig_stats["y_span"], 2) if orig_stats["y_span"] > 0 else 0,
        "size_ratio": round(trans_stats["avg_size"] / orig_stats["avg_size"], 2) if orig_stats["avg_size"] > 0 else 0,
    }
    
    orig_doc.close()
    trans_doc.close()
    
    return comparison


def main():
    parser = argparse.ArgumentParser(description="Formatting quality diagnostic")
    parser.add_argument("--translate", action="store_true", help="Also translate page 0")
    parser.add_argument("--page", type=int, default=0, help="Page number to analyze")
    parser.add_argument("--max-pages", type=int, default=3, help="Max pages to analyze per doc")
    parser.add_argument("--file", type=str, default=None, help="Process only this file")
    args = parser.parse_args()
    
    print("=" * 80)
    print("FORMATTING QUALITY DIAGNOSTIC")
    print("=" * 80)
    
    # Collect all PDFs
    pdf_files = []
    for p in sorted(INPUT_DIR.rglob("*.pdf")):
        if args.file and args.file not in str(p):
            continue
        pdf_files.append(p)
    
    print(f"\nFound {len(pdf_files)} PDF files in {INPUT_DIR}/\n")
    
    all_issues = []
    
    for pdf_path in pdf_files:
        print(f"\n{'─' * 70}")
        print(f"📁 {pdf_path.relative_to(INPUT_DIR)}")
        print(f"{'─' * 70}")
        
        try:
            doc = pymupdf.open(str(pdf_path))
            print(f"   Pages: {doc.page_count}")
            
            # Analyze first N pages
            max_pages = min(args.max_pages, doc.page_count)
            doc_issues = []
            
            for page_idx in range(max_pages):
                page = doc[page_idx]
                report = analyze_page_structure(page, page_idx)
                print(format_report(report))
                
                # Collect issues
                if report["tables"]:
                    doc_issues.append(f"Has {len(report['tables'])} tables (page {page_idx+1})")
                if report["links"]:
                    doc_issues.append(f"Has {len(report['links'])} links (page {page_idx+1})")
                if report["lists_detected"]:
                    doc_issues.append(f"Has {len(report['lists_detected'])} list items (page {page_idx+1})")
                if report.get("typographic_chars"):
                    doc_issues.append(f"Has typographic chars (page {page_idx+1})")
                for b in report["blocks"]:
                    if b["is_table_area"]:
                        doc_issues.append(f"⚠️ Table-text overlap (page {page_idx+1})")
                        break
            
            if doc_issues:
                all_issues.append((str(pdf_path.relative_to(INPUT_DIR)), doc_issues))
            
            # Translation test
            if args.translate:
                print(f"\n    🔄 Translating page {args.page}...")
                orig_bytes, trans_bytes = translate_single_page(str(pdf_path), args.page)
                
                if orig_bytes and trans_bytes:
                    comparison = compare_page_metrics(orig_bytes, trans_bytes)
                    
                    print(f"    📊 COMPARISON:")
                    print(f"       Original:   {comparison['original']['blocks']} blocks, {comparison['original']['lines']} lines, {comparison['original']['chars']} chars")
                    print(f"       Translated: {comparison['translated']['blocks']} blocks, {comparison['translated']['lines']} lines, {comparison['translated']['chars']} chars")
                    print(f"       Font size ratio: {comparison['size_ratio']}x")
                    print(f"       Y-span ratio: {comparison['y_span_ratio']}x (1.0 = perfect)")
                    print(f"       Links: {comparison['links_orig']} → {comparison['links_trans']} (lost: {comparison['links_lost']})")
                    print(f"       Images: {comparison['images_orig']} → {comparison['images_trans']}")
                    
                    # Save output
                    stem = pdf_path.stem
                    out_orig = OUTPUT_DIR / f"{stem}_orig_p{args.page}.pdf"
                    out_trans = OUTPUT_DIR / f"{stem}_trans_p{args.page}.pdf"
                    out_orig.write_bytes(orig_bytes)
                    out_trans.write_bytes(trans_bytes)
                    print(f"    💾 Saved: {out_orig.name}, {out_trans.name}")
                else:
                    print(f"    ❌ Translation failed")
            
            doc.close()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY OF ISSUES")
    print(f"{'=' * 80}")
    
    if all_issues:
        for filename, issues in all_issues:
            print(f"\n  {filename}:")
            for issue in issues:
                print(f"    - {issue}")
    else:
        print("  No issues detected.")
    
    print()


if __name__ == "__main__":
    main()
