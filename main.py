from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from contextlib import asynccontextmanager
from models import Component, DocSection, get_async_session, create_db_and_tables
from pydantic import BaseModel
from fastapi_mcp import FastApiMCP


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_db_and_tables()
    yield
    # Shutdown - properly close async engine
    from models import async_engine

    await async_engine.dispose()


app = FastAPI(
    title="Reflex MCP Server",
    description="MCP server for Reflex documentation",
    lifespan=lifespan,
)


# Response models
class ComponentResponse(BaseModel):
    id: int
    name: str
    category: str
    content: str
    description: Optional[str] = None


class DocSectionResponse(BaseModel):
    id: int
    name: str
    section: str
    content: str
    description: Optional[str] = None


class ComponentListItem(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None


class DocSectionListItem(BaseModel):
    id: int
    name: str
    section: str
    description: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Reflex MCP Server is running"}


@app.get("/categories", response_model=List[str])
async def get_categories(session: AsyncSession = Depends(get_async_session)):
    """Get all available component categories."""
    statement = select(Component.category).distinct()
    result = await session.execute(statement)
    categories = result.scalars().all()
    return sorted(categories)


@app.get("/sections", response_model=List[str])
async def get_sections(session: AsyncSession = Depends(get_async_session)):
    """Get all available documentation sections."""
    statement = select(DocSection.section).distinct()
    result = await session.execute(statement)
    sections = result.scalars().all()
    return sorted(sections)


@app.get("/get_component_doc", response_model=ComponentResponse)
async def get_component_doc(
    name: str = Query(..., description="Exact component name"),
    session: AsyncSession = Depends(get_async_session),
):
    """Get complete documentation and source code for a specific Reflex component."""
    statement = select(Component).where(Component.name == name)
    result = await session.execute(statement)
    component = result.scalar_one_or_none()

    if not component:
        raise HTTPException(status_code=404, detail=f"Component '{name}' not found")

    return ComponentResponse(
        id=component.id,
        name=component.name,
        category=component.category,
        content=component.content,
        description=component.description,
    )


@app.get("/list_components", response_model=List[str])
async def list_components(
    category: Optional[str] = Query(None, description="Filter by category"),
    session: AsyncSession = Depends(get_async_session),
):
    """Browse all available Reflex component names by category."""
    statement = select(Component)

    if category:
        statement = statement.where(Component.category.ilike(f"%{category}%"))

    result = await session.execute(statement)
    components = result.scalars().all()

    return [comp.name for comp in sorted(components, key=lambda x: x.name)]


@app.get("/list_doc_sections", response_model=List[str])
async def list_doc_sections(
    section: Optional[str] = Query(None, description="Filter by section"),
    session: AsyncSession = Depends(get_async_session),
):
    """Explore available documentation names by section."""
    statement = select(DocSection)

    if section:
        statement = statement.where(DocSection.section.ilike(f"%{section}%"))

    result = await session.execute(statement)
    docs = result.scalars().all()

    return [doc.name for doc in sorted(docs, key=lambda x: x.name)]


@app.get("/get_doc", response_model=DocSectionResponse)
async def get_doc(
    name: str = Query(..., description="Exact documentation name"),
    session: AsyncSession = Depends(get_async_session),
):
    """Read a specific documentation file."""
    statement = select(DocSection).where(DocSection.name == name)
    result = await session.execute(statement)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail=f"Documentation '{name}' not found")

    return DocSectionResponse(
        id=doc.id,
        name=doc.name,
        section=doc.section,
        content=doc.content,
        description=doc.description,
    )


mcp = FastApiMCP(
    app,
    name="reflex docs mcp server",
    description="MCP server for reflex docs",
    describe_full_response_schema=True,  # Describe the full response JSON-schema instead of just a response example
    describe_all_responses=True,  # Describe all the possible responses instead of just the success (2XX) response
)

mcp.mount()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
