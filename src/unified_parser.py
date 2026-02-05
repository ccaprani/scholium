"""Unified parser for markdown slides with embedded :::notes::: blocks.

Supports:
- YAML frontmatter with title_notes for title slide narration
- ::: notes ::: blocks for slide narration
- :: prefix for metadata (not narrated)
- HTML comments for metadata
- Timing directives: [DUR 5s] [PRE 2s] [POST 3s] [MIN 10s] [PAUSE 2s]
- Paragraph-based splitting for incremental reveals (>- lists)
"""

import re
import yaml
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Slide:
    """Represents a slide with content and narration."""
    index: int
    markdown_content: str
    narration_segments: List[str]
    metadata: Dict[str, any] = field(default_factory=dict)
    
    # Timing parameters extracted from metadata
    fixed_duration: Optional[float] = None
    min_duration: Optional[float] = None
    pre_delay: float = 0.0
    post_delay: float = 0.0
    
    @property
    def is_title_slide(self) -> bool:
        """Check if this is the title slide."""
        return self.metadata.get('is_title_slide', False)
    
    @property
    def is_incremental(self) -> bool:
        """Check if this slide has incremental reveals (>- bullets)."""
        return '>-' in self.markdown_content
    
    @property
    def has_narration(self) -> bool:
        """Check if this slide has narration."""
        return any(seg.strip() for seg in self.narration_segments)


def parse_time_spec(time_str: str) -> float:
    """Parse time specification like '5s', '2.5s', '500ms' to seconds."""
    time_str = time_str.strip().lower()
    
    if time_str.endswith('ms'):
        return float(time_str[:-2]) / 1000.0
    elif time_str.endswith('s'):
        return float(time_str[:-1])
    else:
        # Assume seconds if no unit
        return float(time_str)


class UnifiedParser:
    """Parse markdown with embedded :::notes::: sections."""
    
    def parse(self, markdown_path: str) -> List[Slide]:
        """Parse unified markdown into Slide objects.
        
        Args:
            markdown_path: Path to markdown file
            
        Returns:
            List of Slide objects with content + notes
        """
        markdown_path = Path(markdown_path)
        
        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split frontmatter and body
        frontmatter, body = self._split_frontmatter(content)
        
        slides = []
        
        # Check for title_notes in frontmatter (title slide)
        if 'title_notes' in frontmatter:
            title_narration, title_metadata = self._parse_notes_text(
                frontmatter['title_notes']
            )
            
            title_slide = Slide(
                index=0,
                markdown_content="",  # Title content comes from frontmatter
                narration_segments=[title_narration] if title_narration else [],
                metadata={
                    'is_title_slide': True,
                    **title_metadata
                },
                fixed_duration=title_metadata.get('fixed_duration'),
                min_duration=title_metadata.get('min_duration'),
                pre_delay=title_metadata.get('pre_delay', 0.0),
                post_delay=title_metadata.get('post_delay', 0.0)
            )
            slides.append(title_slide)
        
        # Parse body slides
        body_slides = self._parse_body_slides(body, start_index=len(slides))
        slides.extend(body_slides)
        
        return slides
    
    def _split_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Split YAML frontmatter from markdown body.
        
        Returns:
            (frontmatter_dict, body_text)
        """
        # Match YAML frontmatter between --- markers
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        
        if match:
            frontmatter_text = match.group(1)
            body = match.group(2)
            
            try:
                frontmatter = yaml.safe_load(frontmatter_text) or {}
            except yaml.YAMLError:
                frontmatter = {}
            
            return frontmatter, body
        
        return {}, content
    
    def _parse_body_slides(self, body: str, start_index: int = 0) -> List[Slide]:
        """Parse slides from markdown body.
        
        Args:
            body: Markdown body (without frontmatter)
            start_index: Starting slide index
            
        Returns:
            List of Slide objects
        """
        slides = []
        
        # Split on level-1 headings (# only, not ##)
        heading_pattern = r'^# [^#].+$'
        parts = re.split(f'({heading_pattern})', body, flags=re.MULTILINE)
        
        # Combine heading + content pairs
        slide_texts = []
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                slide_text = parts[i] + '\n' + parts[i + 1]
            else:
                slide_text = parts[i]
            slide_texts.append(slide_text)
        
        # Parse each slide
        for i, slide_text in enumerate(slide_texts):
            slide_text = slide_text.strip()
            if not slide_text:
                continue
            
            # Extract notes block
            content, notes = self._extract_notes_block(slide_text)
            
            # Parse notes into narration segments and metadata
            narration_segments, metadata = self._parse_notes_block(notes, content)
            
            slide = Slide(
                index=start_index + i,
                markdown_content=content.strip(),
                narration_segments=narration_segments,
                metadata=metadata,
                fixed_duration=metadata.get('fixed_duration'),
                min_duration=metadata.get('min_duration'),
                pre_delay=metadata.get('pre_delay', 0.0),
                post_delay=metadata.get('post_delay', 0.0)
            )
            slides.append(slide)
        
        return slides
    
    def _extract_notes_block(self, slide_text: str) -> Tuple[str, str]:
        """Extract ::: notes ::: block from slide markdown.
        
        Returns:
            (slide_content, notes_text)
        """
        # Match ::: notes ... :::
        # More flexible pattern that handles newlines properly
        pattern = r'::: notes\s*\n(.*?)\n:::'
        match = re.search(pattern, slide_text, re.DOTALL | re.IGNORECASE)
        
        if match:
            notes = match.group(1).strip()
            # Remove notes block from content
            content = slide_text[:match.start()] + slide_text[match.end():]
            return content.strip(), notes
        
        return slide_text.strip(), ""
    
    def _parse_notes_block(self, notes: str, slide_content: str) -> Tuple[List[str], Dict]:
        """Parse notes block into narration segments and metadata.
        
        Args:
            notes: Raw notes text
            slide_content: Slide markdown (to detect incremental bullets)
            
        Returns:
            (narration_segments, metadata_dict)
        """
        if not notes:
            return [], {}
        
        # Parse notes text
        narration_text, metadata = self._parse_notes_text(notes)
        
        # Split narration into segments for incremental reveals
        segments = self._split_narration_segments(narration_text, slide_content)
        
        return segments, metadata
    
    def _parse_notes_text(self, notes: str) -> Tuple[str, Dict]:
        """Parse notes text, extracting metadata and timing directives.
        
        Returns:
            (clean_narration_text, metadata_dict)
        """
        lines = notes.split('\n')
        narration_lines = []
        metadata = {}
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines (preserve for paragraph detection)
            if not stripped:
                narration_lines.append('')
                continue
            
            # HTML comments â†’ skip
            if stripped.startswith('<!--') or stripped.endswith('-->'):
                self._parse_metadata_from_comment(stripped, metadata)
                continue
            
            # :: prefix â†’ metadata
            if stripped.startswith('::'):
                self._parse_metadata_line(stripped[2:].strip(), metadata)
                continue
            
            # Everything else â†’ narration
            narration_lines.append(line)
        
        # Join narration text
        narration_text = '\n'.join(narration_lines).strip()
        
        # Extract timing directives from narration text
        narration_text = self._extract_timing_directives(narration_text, metadata)
        
        return narration_text, metadata
    
    def _parse_metadata_line(self, line: str, metadata: Dict):
        """Parse a metadata line (after :: prefix).
        
        Metadata lines are for author notes/references only.
        Timing directives should be in the narration text itself.
        """
        # Check for key: value format
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            # Store as metadata (don't parse Timing here - it's just a note)
            metadata[key] = value
        else:
            # Store as generic note
            if 'notes' not in metadata:
                metadata['notes'] = []
            metadata['notes'].append(line)
    
    def _parse_metadata_from_comment(self, comment: str, metadata: Dict):
        """Parse metadata from HTML comment."""
        # Remove comment markers
        comment = re.sub(r'<!--|-->', '', comment).strip()
        self._parse_metadata_line(comment, metadata)
    
    def _extract_timing_directives(self, text: str, metadata: Dict) -> str:
        """Extract timing directives from narration text.
        
        Directives: [DUR 5s] [PRE 2s] [POST 3s] [MIN 10s]
        [PAUSE 2s] remains in text (for TTS to handle)
        
        Returns:
            Text with slide-level timing directives removed (DUR/PRE/POST/MIN)
            but [PAUSE] preserved for mid-narration pauses
        """
        # Extract DUR, PRE, POST, MIN directives
        timing_pattern = r'\[(DUR|PRE|POST|MIN)\s+([\d.]+)s?\]'
        
        directives = re.findall(timing_pattern, text, re.IGNORECASE)
        
        for directive, value in directives:
            directive = directive.upper()
            time_value = float(value)
            
            if directive == 'DUR':
                metadata['fixed_duration'] = time_value
            elif directive == 'PRE':
                metadata['pre_delay'] = time_value
            elif directive == 'POST':
                metadata['post_delay'] = time_value
            elif directive == 'MIN':
                metadata['min_duration'] = time_value
        
        # Remove only DUR/PRE/POST/MIN from text (keep PAUSE)
        clean_text = re.sub(timing_pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace that may result from removing directives
        # BUT preserve paragraph breaks (double newlines)
        # First, normalize multiple newlines to double newlines
        clean_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_text)
        # Then clean up spaces within lines (but not newlines)
        clean_text = re.sub(r'[ \t]+', ' ', clean_text)
        # Clean up spaces around newlines
        clean_text = re.sub(r' *\n *', '\n', clean_text)
        
        return clean_text.strip()
    
    def _split_narration_segments(self, text: str, slide_content: str) -> List[str]:
        """Split narration into segments for incremental reveals and PAUSE directives.
        
        IMPORTANT: Pandoc with >- bullets creates N pages for N bullets:
        - Page 1: Title + bullet 1
        - Page 2: Title + bullets 1-2
        - Page 3: Title + bullets 1-2-3
        - etc.
        
        The first bullet ALWAYS shows (no title-only page).
        
        Also handles [PAUSE Xs] directives by splitting text around them.
        Each [PAUSE Xs] becomes its own segment for silent audio.
        
        Args:
            text: Narration text
            slide_content: Slide markdown content
            
        Returns:
            List of narration segments (including pause segments)
        """
        if not text:
            return []
        
        # First, split on [PAUSE] directives
        segments = self._split_on_pause_directives(text)
        
        # Check if slide has incremental bullets
        has_incremental = '>-' in slide_content
        
        if has_incremental:
            # For incremental slides with PAUSEs, this gets complex
            # We need bullet_count segments, but PAUSEs create extras
            # 
            # Strategy: Count text segments (non-PAUSE) and match to bullets
            # Keep pause segments as-is
            
            bullet_count = slide_content.count('>-')
            
            # If we only have one segment and it's not a pause, split on paragraphs
            if len(segments) == 1 and not segments[0].startswith('[SILENT'):
                # Split on blank lines (paragraphs)
                paragraphs = [s.strip() for s in segments[0].split('\n\n') if s.strip()]
                
                if len(paragraphs) == bullet_count:
                    return paragraphs
                elif len(paragraphs) > bullet_count:
                    # Combine extras
                    result = paragraphs[:bullet_count - 1]
                    result.append('\n\n'.join(paragraphs[bullet_count - 1:]))
                    print(f"Warning: {bullet_count} bullets but {len(paragraphs)} paragraphs. "
                          f"Combining extras.")
                    return result
                else:
                    # Pad with empty
                    print(f"Warning: {bullet_count} bullets but only {len(paragraphs)} paragraphs. "
                          f"Padding with silent.")
                    while len(paragraphs) < bullet_count:
                        paragraphs.append("")
                    return paragraphs
            
            # Multiple segments (includes pauses)
            # Just return as-is - user must structure their narration correctly
            return segments
        
        # Non-incremental: return segments as-is (includes pause segments)
        return segments
    
    def _split_on_pause_directives(self, text: str) -> List[str]:
        """Split text on [PAUSE Xs] directives, keeping them as separate segments.
        
        Example:
            Input: "First sentence. [PAUSE 2s] Second sentence. [PAUSE 1s] Third."
            Output: ["First sentence.", "[PAUSE 2s]", "Second sentence.", "[PAUSE 1s]", "Third."]
        
        Args:
            text: Narration text possibly containing [PAUSE] directives
            
        Returns:
            List of segments where pause directives are preserved as segments
        """
        # Pattern to match [PAUSE 2s] or [PAUSE 2.5s]
        pause_pattern = r'\[PAUSE\s+([\d.]+)s?\]'
        
        # Find all pause directives with their positions
        matches = list(re.finditer(pause_pattern, text, re.IGNORECASE))
        
        if not matches:
            # No pauses - return text as single segment
            return [text.strip()] if text.strip() else []
        
        segments = []
        last_end = 0
        
        for match in matches:
            # Add text before this pause
            before_text = text[last_end:match.start()].strip()
            if before_text:
                segments.append(before_text)
            
            # Keep the pause marker as-is
            pause_duration = match.group(1)
            segments.append(f"[PAUSE {pause_duration}s]")
            
            last_end = match.end()
        
        # Add remaining text after last pause
        after_text = text[last_end:].strip()
        if after_text:
            segments.append(after_text)
        
        return segments



def validate_slides(slides: List[Slide], num_pdf_pages: int) -> List[str]:
    """Validate parsed slides against expected number of PDF pages.
    
    Args:
        slides: List of parsed slides
        num_pdf_pages: Number of pages in generated PDF
        
    Returns:
        List of warning messages (empty if no issues)
    """
    warnings = []
    
    # Count expected pages (considering incremental reveals)
    expected_pages = 0
    for slide in slides:
        if slide.is_incremental:
            # Count >- bullets - each bullet creates one page
            bullet_count = slide.markdown_content.count('>-')
            expected_pages += bullet_count
        else:
            expected_pages += 1
    
    if expected_pages != num_pdf_pages:
        warnings.append(
            f"Expected {expected_pages} PDF pages but got {num_pdf_pages}. "
            f"This may affect narration sync."
        )
    
    # Check for slides without narration
    for slide in slides:
        if not slide.has_narration and not slide.is_title_slide:
            warnings.append(
                f"Slide {slide.index} has no narration"
            )
    
    # Check for incremental slides with mismatched narration segments
    for slide in slides:
        if slide.is_incremental:
            bullet_count = slide.markdown_content.count('>-')
            seg_count = len(slide.narration_segments)
            
            if seg_count != bullet_count:
                warnings.append(
                    f"Slide {slide.index}: {bullet_count} incremental bullets "
                    f"but {seg_count} narration segments"
                )
    
    return warnings
