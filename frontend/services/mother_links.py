from typing import Iterable, List, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.animal import Animal


def link_mother_to_calves_by_tags(
    db: Session,
    *,
    mother: Animal,
    calf_tags: Iterable[str],
) -> Tuple[int, List[str]]:
    """
    Attempts to link a mother to calves by tag numbers.
    - Ignores tags that are falsy or equal to 'unknown' (case-insensitive).
    - Sets Animal.mother_id for each matching calf.
    - Returns (linked_count, unresolved_tags)

    NOTE: This only links existing animals; it does not create new calf records.
    """
    if not mother or not calf_tags:
        return 0, []

    tags = [
        (t or "").strip()
        for t in calf_tags
        if (t or "").strip() and (t or "").strip().lower() != "unknown"
    ]
    if not tags:
        return 0, []

    rows = db.execute(select(Animal).where(Animal.tag_number.in_(tags))).scalars().all()
    found_by_tag = {a.tag_number: a for a in rows if a.tag_number}

    linked = 0
    unresolved: List[str] = []
    for tag in tags:
        calf = found_by_tag.get(tag)
        if not calf:
            unresolved.append(tag)
            continue
        if calf.id == mother.id:
            # avoid self-linking if tag numbers collide
            unresolved.append(tag)
            continue
        calf.mother_id = mother.id
        calf.touch()
        linked += 1

    return linked, unresolved


def clear_mother_links_for_mother(db: Session, mother_id: int) -> int:
    """
    Clears mother_id for all calves that point to a given mother_id.
    Returns the number of rows affected.
    """
    rows = db.execute(select(Animal).where(Animal.mother_id == mother_id)).scalars().all()
    for calf in rows:
        calf.mother_id = None
        calf.touch()
    return len(rows)
