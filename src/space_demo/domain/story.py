# Story Domain Models for To Boldly Respawn

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from space_demo.domain.content_ids import validate_content_id

@dataclass(frozen=True)
class StoryChoice:
    text: str
    next_node_id: Optional[str]
    flags_set: Dict[str, Any] = field(default_factory=dict)
    flags_cleared: List[str] = field(default_factory=list)
    reward_ids: List[str] = field(default_factory=list)

    def validate(self, strict: bool = False) -> None:
        if not self.text or not isinstance(self.text, str):
            raise ValueError("Choice text must be a non-empty string.")
        if self.next_node_id is not None:
            validate_content_id(self.next_node_id)
        if not isinstance(self.flags_set, dict):
            raise ValueError("flags_set must be a dictionary.")
        for k in self.flags_set.keys():
            validate_content_id(k)
        if not isinstance(self.flags_cleared, list):
            raise ValueError("flags_cleared must be a list of strings.")
        for flag in self.flags_cleared:
            if not isinstance(flag, str):
                raise ValueError("flags_cleared entries must be strings.")
            validate_content_id(flag)
        if not isinstance(self.reward_ids, list):
            raise ValueError("reward_ids must be a list of strings.")
        for rid in self.reward_ids:
            if not isinstance(rid, str):
                raise ValueError("reward_ids entries must be strings.")
            validate_content_id(rid)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strict: bool = False) -> "StoryChoice":
        if not isinstance(data, dict):
            raise ValueError("StoryChoice input must be a dictionary.")
        expected_fields = {"text", "next_node_id", "flags_set", "flags_cleared", "reward_ids"}
        if strict:
            unknown = set(data.keys()) - expected_fields
            if unknown:
                raise ValueError(f"Unknown fields in story choice: {unknown}")
        return cls(
            text=data.get("text"),
            next_node_id=data.get("next_node_id"),
            flags_set=data.get("flags_set", {}),
            flags_cleared=data.get("flags_cleared", []),
            reward_ids=data.get("reward_ids", [])
        )

@dataclass(frozen=True)
class StoryNode:
    id: str
    speaker: str
    body: str
    map_id: Optional[str]
    wave_id: Optional[str]
    choices: List[StoryChoice]
    next_node_id: Optional[str] = None
    flags_set: Dict[str, Any] = field(default_factory=dict)
    flags_cleared: List[str] = field(default_factory=list)
    reward_ids: List[str] = field(default_factory=list)
    unlock_requirements: Dict[str, Any] = field(default_factory=dict)

    def validate(self, strict: bool = False) -> None:
        validate_content_id(self.id)
        if not isinstance(self.speaker, str):
            raise ValueError("speaker must be a string.")
        if not self.body or not isinstance(self.body, str):
            raise ValueError("body must be a non-empty string.")
        if self.map_id is not None:
            validate_content_id(self.map_id)
        if self.wave_id is not None:
            validate_content_id(self.wave_id)
            if self.map_id is None:
                raise ValueError("wave_id specified without map_id.")
        if not isinstance(self.choices, list):
            raise ValueError("choices must be a list of StoryChoice objects.")
        
        # Enforce branching constraints:
        # A node may have choices OR next_node_id defined, but not both.
        if self.choices and self.next_node_id is not None:
            raise ValueError("A story node cannot have both choices and next_node_id defined.")
        
        for c in self.choices:
            if not isinstance(c, StoryChoice):
                raise TypeError("All choices must be instances of StoryChoice.")
            c.validate(strict)

        if self.next_node_id is not None:
            validate_content_id(self.next_node_id)
        if not isinstance(self.flags_set, dict):
            raise ValueError("flags_set must be a dictionary.")
        for k in self.flags_set.keys():
            validate_content_id(k)
        if not isinstance(self.flags_cleared, list):
            raise ValueError("flags_cleared must be a list of strings.")
        for flag in self.flags_cleared:
            if not isinstance(flag, str):
                raise ValueError("flags_cleared entries must be strings.")
            validate_content_id(flag)
        if not isinstance(self.reward_ids, list):
            raise ValueError("reward_ids must be a list of strings.")
        for rid in self.reward_ids:
            if not isinstance(rid, str):
                raise ValueError("reward_ids entries must be strings.")
            validate_content_id(rid)
        if not isinstance(self.unlock_requirements, dict):
            raise ValueError("unlock_requirements must be a dictionary.")

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strict: bool = False) -> "StoryNode":
        if not isinstance(data, dict):
            raise ValueError("StoryNode input must be a dictionary.")
        expected_fields = {
            "id", "speaker", "body", "map_id", "wave_id", "choices",
            "next_node_id", "flags_set", "flags_cleared", "reward_ids", "unlock_requirements"
        }
        if strict:
            unknown = set(data.keys()) - expected_fields
            if unknown:
                raise ValueError(f"Unknown fields in story node: {unknown}")
        
        raw_choices = data.get("choices", [])
        if not isinstance(raw_choices, list):
            raise ValueError("choices field in story node must be a list.")
        for index, item in enumerate(raw_choices):
            if not isinstance(item, dict):
                raise ValueError(f"Choice at index {index} must be a dictionary object.")
        choices = [StoryChoice.from_dict(c, strict) for c in raw_choices]
        
        return cls(
            id=data.get("id"),
            speaker=data.get("speaker", ""),
            body=data.get("body"),
            map_id=data.get("map_id"),
            wave_id=data.get("wave_id"),
            choices=choices,
            next_node_id=data.get("next_node_id"),
            flags_set=data.get("flags_set", {}),
            flags_cleared=data.get("flags_cleared", []),
            reward_ids=data.get("reward_ids", []),
            unlock_requirements=data.get("unlock_requirements", {})
        )

@dataclass(frozen=True)
class StoryDef:
    id: str
    display_name: str
    description: str
    nodes: List[StoryNode]

    def validate(self, strict: bool = False) -> None:
        validate_content_id(self.id)
        if not self.display_name or not isinstance(self.display_name, str):
            raise ValueError("display_name must be a non-empty string.")
        if not isinstance(self.description, str):
            raise ValueError("description must be a string.")
        if not isinstance(self.nodes, list) or not self.nodes:
            raise ValueError("nodes must be a non-empty list of StoryNode objects.")
        
        node_ids = set()
        for node in self.nodes:
            if not isinstance(node, StoryNode):
                raise TypeError("All nodes must be instances of StoryNode.")
            node.validate(strict)
            if node.id in node_ids:
                raise ValueError(f"Duplicate node ID '{node.id}' in story '{self.id}'.")
            node_ids.add(node.id)

        # Validate branching: choice next_node_id or node next_node_id must point to existing node
        for node in self.nodes:
            if node.next_node_id is not None:
                if node.next_node_id not in node_ids:
                    raise ValueError(
                        f"Node '{node.id}' references non-existent next_node_id '{node.next_node_id}'."
                    )
            for c in node.choices:
                if c.next_node_id is not None:
                    if c.next_node_id not in node_ids:
                        raise ValueError(
                            f"Node '{node.id}' choice references non-existent next_node_id '{c.next_node_id}'."
                        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strict: bool = False) -> "StoryDef":
        if not isinstance(data, dict):
            raise ValueError("StoryDef input must be a dictionary.")
        expected_fields = {"id", "display_name", "description", "nodes"}
        if strict:
            unknown = set(data.keys()) - expected_fields
            if unknown:
                raise ValueError(f"Unknown fields in story definition: {unknown}")
        
        raw_nodes = data.get("nodes", [])
        if not isinstance(raw_nodes, list):
            raise ValueError("nodes field in story definition must be a list.")
        for index, item in enumerate(raw_nodes):
            if not isinstance(item, dict):
                raise ValueError(f"Node at index {index} must be a dictionary object.")
        nodes = [StoryNode.from_dict(n, strict) for n in raw_nodes]
        
        return cls(
            id=data.get("id"),
            display_name=data.get("display_name"),
            description=data.get("description", ""),
            nodes=nodes
        )
