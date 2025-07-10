import os
import re
from pathlib import Path
from typing import Tuple
from sqlmodel import Session, select
from models import Component, DocSection, sync_engine, create_db_and_tables_sync


def extract_component_info(content: str, file_path: str) -> Tuple[str, str]:
    """Extract component name and description from markdown content"""
    name = None
    description = None

    # Try to extract from frontmatter
    frontmatter_match = re.search(r"---\s*\n(.*?)\n---", content, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        # Look for components field
        components_match = re.search(r"components:\s*\n\s*-\s*([^\n]+)", frontmatter)
        if components_match:
            name = components_match.group(1).strip()

    # If not found in frontmatter, try to extract from first heading
    if not name:
        heading_match = re.search(r"^#\s+(.+?)$", content, re.MULTILINE)
        if heading_match:
            name = heading_match.group(1).strip()

    # Extract description from first paragraph after heading
    if name:
        # Look for description after the heading
        pattern = rf"#\s+{re.escape(name)}\s*\n\s*(.+?)(?:\n\n|\n#|$)"
        desc_match = re.search(pattern, content, re.DOTALL)
        if desc_match:
            description = desc_match.group(1).strip()

    # Fallback: use filename as name
    if not name:
        name = Path(file_path).stem.replace("_", " ").title()

    return name, description or ""


def get_category_from_path(file_path: str) -> str:
    """Extract category from file path"""
    path_parts = Path(file_path).parts
    if "library" in path_parts:
        library_idx = path_parts.index("library")
        if library_idx + 1 < len(path_parts):
            return (
                path_parts[library_idx + 1].replace("_", " ").replace("-", " ").title()
            )
    return "Other"


def get_section_from_path(file_path: str) -> str:
    """Extract section from file path"""
    path_parts = Path(file_path).parts
    if "reflex_docs" in path_parts:
        docs_idx = path_parts.index("reflex_docs")
        if docs_idx + 1 < len(path_parts):
            return path_parts[docs_idx + 1].replace("_", " ").replace("-", " ").title()
    return "Other"


def populate_database():
    """Populate the database with content from markdown files"""
    # Create database and tables
    create_db_and_tables_sync()

    docs_path = "reflex_docs"

    with Session(sync_engine) as session:
        # Clear existing data by deleting all records
        for component in session.exec(select(Component)).all():
            session.delete(component)
        for doc_section in session.exec(select(DocSection)).all():
            session.delete(doc_section)
        session.commit()

        # Process components (library directory)
        library_path = os.path.join(docs_path, "library")
        if os.path.exists(library_path):
            for root, dirs, files in os.walk(library_path):
                for file in files:
                    if file.endswith(".md"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()

                            name, description = extract_component_info(
                                content, file_path
                            )
                            category = get_category_from_path(file_path)

                            # Check if component already exists
                            existing = session.exec(
                                select(Component).where(Component.name == name)
                            ).first()
                            if existing:
                                name = f"{name}_{category}"  # Make name unique

                            # Create component
                            component = Component(
                                name=name,
                                category=category,
                                file_path=file_path,
                                content=content,
                                description=description,
                            )
                            session.add(component)
                            print(f"Added component: {name}_{category}")

                        except Exception as e:
                            print(f"Error processing {file_path}: {e}")

        # Process other documentation
        for root, dirs, files in os.walk(docs_path):
            # Skip library directory as it's already processed
            if "library" in root:
                continue

            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Extract title from first heading or filename
                        title_match = re.search(r"^#\s+(.+?)$", content, re.MULTILINE)
                        if title_match:
                            name = title_match.group(1).strip()
                        else:
                            name = (
                                Path(file_path)
                                .stem.replace("_", " ")
                                .replace("-", " ")
                                .title()
                            )

                        section = get_section_from_path(file_path)
                        # Check if doc section already exists
                        existing = session.exec(
                            select(DocSection).where(DocSection.name == name)
                        ).first()
                        if existing:
                            name = f"{name}_{section}"  # Make name unique

                        # Extract first paragraph as description
                        desc_match = re.search(
                            r"#\s+.+?\n\s*(.+?)(?:\n\n|\n#|$)", content, re.DOTALL
                        )
                        description = desc_match.group(1).strip() if desc_match else ""

                        # Create doc section
                        doc_section = DocSection(
                            name=name,
                            section=section,
                            file_path=file_path,
                            content=content,
                            description=description,
                        )
                        session.add(doc_section)
                        print(f"Added doc: {name}_{section}")

                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")

        session.commit()
        print("Database populated successfully!")


if __name__ == "__main__":
    populate_database()
