#!/usr/bin/env python3
"""
Example driver script for batch processing multiple lectures.

This demonstrates how to orchestrate the pdf-voiceover-video tool
for complex course structures with shared and subject-specific content.
"""

import sys
import subprocess
from pathlib import Path


class CourseBuilder:
    """Builds videos for a course with shared and subject-specific lectures."""
    
    def __init__(self, base_dir, voice="my_voice"):
        self.base_dir = Path(base_dir)
        self.voice = voice
        self.tool = "python src/main.py generate"
    
    def build_lecture(self, lecture_dir, output_dir=None):
        """Build a single lecture video.
        
        Args:
            lecture_dir: Path to lecture folder with slides.md and transcript.txt
            output_dir: Optional output directory (default: lecture_dir)
        """
        lecture_dir = Path(lecture_dir)
        
        if output_dir is None:
            output_dir = lecture_dir
        else:
            output_dir = Path(output_dir)
        
        slides = lecture_dir / "slides.md"
        transcript = lecture_dir / "transcript.txt"
        output = output_dir / "lecture.mp4"
        
        if not slides.exists() or not transcript.exists():
            print(f"⚠️  Skipping {lecture_dir.name}: missing files")
            return False
        
        print(f"🎬 Building {lecture_dir.name}...")
        
        cmd = [
            "python", "src/main.py", "generate",
            str(slides),
            str(transcript),
            str(output),
            "--voice", self.voice
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"   ✓ Completed: {output}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Failed: {e.stderr}")
            return False
    
    def build_subject(self, subject_name, lecture_numbers, shared_lectures=None):
        """Build all lectures for a subject.
        
        Args:
            subject_name: Name of subject (e.g., "structural_steel")
            lecture_numbers: List of subject-specific lecture numbers
            shared_lectures: List of shared lecture numbers (default: [])
        """
        if shared_lectures is None:
            shared_lectures = []
        
        subject_dir = self.base_dir / "subjects" / subject_name
        shared_dir = self.base_dir / "shared"
        output_base = self.base_dir / "output" / subject_name
        
        print(f"\n{'='*60}")
        print(f"Building subject: {subject_name}")
        print(f"{'='*60}")
        
        success_count = 0
        total_count = 0
        
        # Build shared lectures
        for num in shared_lectures:
            lecture_dir = shared_dir / f"lecture_{num:02d}"
            output_dir = output_base / f"lecture_{num:02d}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if self.build_lecture(lecture_dir, output_dir):
                success_count += 1
            total_count += 1
        
        # Build subject-specific lectures
        for num in lecture_numbers:
            lecture_dir = subject_dir / f"lecture_{num:02d}"
            output_dir = output_base / f"lecture_{num:02d}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if self.build_lecture(lecture_dir, output_dir):
                success_count += 1
            total_count += 1
        
        print(f"\n{subject_name}: {success_count}/{total_count} lectures built successfully")
        
        return success_count, total_count
    
    def build_all(self, course_structure):
        """Build all subjects according to course structure.
        
        Args:
            course_structure: Dict mapping subject names to lecture configurations
                Example:
                {
                    'structural_steel': {
                        'shared': [1, 2, 3, 4, 5],
                        'specific': [51, 52, 53]
                    },
                    'reinforced_concrete': {
                        'shared': [1, 2, 3, 4, 5],
                        'specific': [61, 62, 63]
                    }
                }
        """
        total_success = 0
        total_count = 0
        
        for subject, config in course_structure.items():
            success, count = self.build_subject(
                subject,
                config.get('specific', []),
                config.get('shared', [])
            )
            total_success += success
            total_count += count
        
        print(f"\n{'='*60}")
        print(f"OVERALL: {total_success}/{total_count} lectures built successfully")
        print(f"{'='*60}")


def main():
    """Example usage of the course builder."""
    
    # Example course structure: 75% shared, 25% subject-specific
    course_structure = {
        'structural_steel': {
            'shared': [1, 2, 3, 4, 5],  # First 5 lectures shared
            'specific': [51, 52, 53]    # Subject-specific lectures
        },
        'reinforced_concrete': {
            'shared': [1, 2, 3, 4, 5],  # Same shared lectures
            'specific': [61, 62, 63]    # Different subject-specific lectures
        }
    }
    
    # Initialize builder
    builder = CourseBuilder(
        base_dir="./lectures",
        voice="my_voice"
    )
    
    # Build all subjects
    builder.build_all(course_structure)


if __name__ == "__main__":
    main()
