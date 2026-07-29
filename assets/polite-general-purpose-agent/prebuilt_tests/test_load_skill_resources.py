"""Tests for load_skill_resources.py"""

import os
import pytest


def _make_skill(tmp_path, folder_name: str, content: str) -> None:
    skill_dir = tmp_path / folder_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")


@pytest.mark.structure
class TestValidateAndParseFrontmatter:
    def test_valid_frontmatter_returns_name_and_description(self, add_agent_to_path):
        from load_skill_resources import _validate_and_parse_frontmatter
        name, desc = _validate_and_parse_frontmatter("---\nname: my-skill\ndescription: Does something\n---\n# Body")
        assert name == "my-skill"
        assert desc == "Does something"

    def test_invalid_frontmatter_missing_opening_fence(self, add_agent_to_path):
        from load_skill_resources import _validate_and_parse_frontmatter
        with pytest.raises(ValueError):
            _validate_and_parse_frontmatter("name: my-skill")

    def test_actual_skills_load_without_error(self, add_agent_to_path):
        import load_skill_resources
        tools = load_skill_resources.get_load_skill_resource_tool()
        assert isinstance(tools, list)
