"""Pane tree management for the compositor."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from yaml import safe_dump, safe_load


@dataclass
class Pane:
    """Leaf pane model."""

    pane_id: str
    working_dir: str = "."
    is_active: bool = True
    is_leaf: bool = True


@dataclass
class PaneNode:
    """A node in the pane tree."""

    pane_id: str
    is_leaf: bool = True
    direction: str | None = None
    pane: Pane | None = None
    children: list[PaneNode] = field(default_factory=list)
    parent: PaneNode | None = None

    def __post_init__(self) -> None:
        if self.pane is None and self.is_leaf:
            self.pane = Pane(self.pane_id)
        if not self.is_leaf:
            self.pane = None

    def leaves(self) -> list[PaneNode]:
        """Return all leaf nodes."""
        if self.is_leaf:
            return [self]
        out: list[PaneNode] = []
        for child in self.children:
            out.extend(child.leaves())
        return out


class PaneManager:
    """Tree manager used for splitter-aware pane operations."""

    def __init__(self) -> None:
        self.root: PaneNode = PaneNode("root")
        self.focus_pane_id: str = "root"
        self._next_pane_index = 1

    def _new_pane_id(self) -> str:
        pane_id = f"pane-{self._next_pane_index}"
        self._next_pane_index += 1
        return pane_id

    def _new_branch_id(self, pane_id: str) -> str:
        branch_id = f"branch-{pane_id}-{self._next_pane_index}"
        self._next_pane_index += 1
        return branch_id

    def _find_node(self, node_id: str, node: PaneNode | None = None) -> PaneNode | None:
        if node is None:
            node = self.root
        if node.pane_id == node_id:
            return node
        for child in node.children:
            result = self._find_node(node_id, child)
            if result is not None:
                return result
        return None

    def _leaf_nodes(self) -> list[PaneNode]:
        return self.root.leaves()

    def _first_leaf(self, node: PaneNode | None = None) -> PaneNode | None:
        leaves = (node or self.root).leaves()
        return leaves[0] if leaves else None

    def _set_focus_to_first_leaf(self, node: PaneNode | None = None) -> None:
        leaf = self._first_leaf(node)
        self.focus_pane_id = leaf.pane_id if leaf is not None else "root"

    def _attach_children(self, parent: PaneNode, children: list[PaneNode]) -> None:
        parent.children = children
        for child in children:
            child.parent = parent

    def _replace_child(self, parent: PaneNode, old: PaneNode, new: PaneNode) -> None:
        idx = parent.children.index(old)
        parent.children[idx] = new
        new.parent = parent

    def _collapse_from(self, node: PaneNode) -> None:
        while not node.is_leaf:
            if len(node.children) > 1:
                break
            only = node.children[0] if node.children else PaneNode(self._new_pane_id())
            if node is self.root:
                only.parent = None
                self.root = only
                break
            parent = node.parent
            if parent is None:
                break
            self._replace_child(parent, node, only)
            node = parent

    def _track_id(self, pane_id: str) -> None:
        for number in re.findall(r"\d+", pane_id):
            self._next_pane_index = max(self._next_pane_index, int(number) + 1)

    def get_focused_pane(self) -> PaneNode:
        focused = self._find_node(self.focus_pane_id)
        if focused is None or not focused.is_leaf:
            focused = self._first_leaf()
            if focused is not None:
                self.focus_pane_id = focused.pane_id
        if focused is None:
            raise RuntimeError("no panes")
        return focused

    def get_pane_count(self) -> int:
        return len(self._leaf_nodes())

    def get_all_panes(self) -> list[Pane]:
        return [leaf.pane for leaf in self._leaf_nodes() if leaf.pane is not None]

    def get_pane_by_id(self, pane_id: str) -> PaneNode | None:
        node = self._find_node(pane_id)
        if node is None or not node.is_leaf:
            return None
        return node

    def create_root_pane(self, pane_id: str) -> PaneNode:
        self.root = PaneNode(pane_id)
        self.focus_pane_id = pane_id
        return self.root

    def split_pane(self, direction: str) -> PaneNode:
        direction = direction.upper()
        if direction not in {"H", "V"}:
            raise ValueError("direction must be H or V")

        focused = self.get_focused_pane()
        if not focused.parent:
            return self._split_root(focused, direction)

        parent = focused.parent
        new_node = PaneNode(self._new_pane_id())
        new_node.parent = parent
        old_direction = parent.direction or "V"
        if old_direction != ("V" if direction == "V" else "H"):
            return self._split_mixed(parent, focused, new_node, direction)
        parent.children = [*parent.children, new_node]
        self.focus_pane_id = new_node.pane_id
        return new_node

    def _split_root(self, old_root: PaneNode, direction: str) -> PaneNode:
        new_node = PaneNode(self._new_pane_id())
        branch = PaneNode(
            pane_id=self._new_branch_id(old_root.pane_id),
            is_leaf=False,
            direction="V" if direction == "V" else "H",
        )
        self._attach_children(branch, [old_root, new_node])
        self.root = branch
        self.focus_pane_id = new_node.pane_id
        return new_node

    def _split_mixed(
        self,
        parent: PaneNode,
        focused: PaneNode,
        new_node: PaneNode,
        direction: str,
    ) -> PaneNode:
        branch = PaneNode(
            pane_id=self._new_branch_id(focused.pane_id),
            is_leaf=False,
            direction=("V" if direction == "V" else "H"),
        )
        self._attach_children(branch, [focused, new_node])
        self._replace_child(parent, focused, branch)
        self.focus_pane_id = new_node.pane_id
        return new_node

    def close_pane(self, pane_id: str | None = None) -> bool:
        if pane_id is None:
            pane_id = self.focus_pane_id

        leaves = self._leaf_nodes()
        if len(leaves) <= 1:
            return False

        target = self._find_node(pane_id)
        if target is None or target.is_leaf is False:
            return False
        parent = target.parent
        if parent is None:
            return False

        parent.children = [child for child in parent.children if child.pane_id != target.pane_id]
        self._collapse_from(parent)
        self._set_focus_to_first_leaf()
        return True

    def focus_next(self) -> bool:
        leaves = self._leaf_nodes()
        if not leaves:
            return False
        ids = [leaf.pane_id for leaf in leaves]
        if self.focus_pane_id not in ids:
            self.focus_pane_id = ids[0]
            return True
        current = ids.index(self.focus_pane_id)
        self.focus_pane_id = ids[(current + 1) % len(ids)]
        return True

    def save_layout(self) -> dict[str, Any]:
        def serialize(node: PaneNode) -> dict[str, Any]:
            if node.is_leaf or node.pane is not None:
                return {
                    "type": "pane",
                    "id": node.pane_id,
                    "working_dir": node.pane.working_dir if node.pane else ".",
                }
            return {
                "type": "branch",
                "id": node.pane_id,
                "direction": node.direction or "H",
                "children": [serialize(child) for child in node.children],
            }

        return serialize(self.root)

    def restore_layout(self, layout: dict[str, Any] | None) -> bool:
        if not isinstance(layout, dict) or "type" not in layout:
            return False
        try:
            self.root = self._build_restored_node(layout)
        except Exception:
            return False
        self.root.parent = None
        self._set_focus_to_first_leaf()
        return True

    def _build_restored_node(
        self,
        data: dict[str, Any],
        parent: PaneNode | None = None,
    ) -> PaneNode:
        node_type = data.get("type")
        if node_type == "pane":
            return self._build_restored_pane(data, parent)
        if node_type == "branch":
            return self._build_restored_branch(data, parent)
        raise ValueError("invalid node type")

    def _build_restored_pane(
        self,
        data: dict[str, Any],
        parent: PaneNode | None,
    ) -> PaneNode:
        pane_id = str(data.get("id") or self._new_pane_id())
        if not pane_id:
            pane_id = self._new_pane_id()
        self._track_id(pane_id)
        node = PaneNode(pane_id, is_leaf=True)
        node.pane = Pane(node.pane_id, working_dir=data.get("working_dir", "."))
        node.parent = parent
        return node

    def _build_restored_branch(
        self,
        data: dict[str, Any],
        parent: PaneNode | None,
    ) -> PaneNode:
        branch_id = str(data.get("id") or self._new_branch_id("restored"))
        self._track_id(branch_id)
        node = PaneNode(
            pane_id=branch_id,
            is_leaf=False,
            direction=data.get("direction", "H"),
        )
        children = [self._build_restored_node(child, node) for child in data.get("children", [])]
        self._attach_children(node, children or [PaneNode(self._new_pane_id())])
        node.parent = parent
        return node

    def _to_yaml(self) -> str:
        return safe_dump(self.save_layout())


__all__ = ["PaneManager"]
