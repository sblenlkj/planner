from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AgentSkill:
    skill_id: str
    title: str
    description: str
    body: str


def load_agent_skills() -> list[AgentSkill]:
    skills_dir = Path(__file__).parent

    skill_files = [
        skills_dir / "course_planning.md",
        skills_dir / "user_memory.md",
    ]

    return [_load_skill(path) for path in skill_files if path.exists()]


def get_agent_skill(skill_id: str) -> AgentSkill:
    normalized_id = skill_id.strip()

    for skill in load_agent_skills():
        if skill.skill_id == normalized_id:
            return skill

    available = ", ".join(skill.skill_id for skill in load_agent_skills())

    raise ValueError(
        f"Unknown skill_id: {skill_id!r}. Available skills: {available}"
    )


def render_skill_catalog(skills: list[AgentSkill]) -> str:
    if not skills:
        return "- skills are not available"

    return "\n".join(
        (
            f"- skill_id={skill.skill_id}; "
            f"title={skill.title}; "
            f"description={skill.description}"
        )
        for skill in skills
    )


def _load_skill(path: Path) -> AgentSkill:
    text = path.read_text(encoding="utf-8").strip()

    if not text.startswith("---"):
        return AgentSkill(
            skill_id=path.stem,
            title=path.stem,
            description="",
            body=text,
        )

    _, metadata_text, body = text.split("---", 2)
    metadata = _parse_metadata(metadata_text)

    return AgentSkill(
        skill_id=metadata.get("skill_id", path.stem),
        title=metadata.get("title", path.stem),
        description=metadata.get("description", ""),
        body=body.strip(),
    )


def _parse_metadata(value: str) -> dict[str, str]:
    result: dict[str, str] = {}

    for line in value.splitlines():
        if ":" not in line:
            continue

        key, raw_value = line.split(":", 1)
        result[key.strip()] = raw_value.strip()

    return result