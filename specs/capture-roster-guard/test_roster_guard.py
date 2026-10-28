"""Disposable controls; no private packet or maintained owner is executed."""

import ast
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
import roster_guard as guard

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor contract")


@pytest.fixture
def tree(tmp_path):
    root = tmp_path.resolve()
    names = [
        "tests/test_one.py",
        "tests/fixtures/formalism_catalogue_155_reviewed_deltas.json",
        "tests/_support/resources/example.py.txt",
    ]
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"disposable fixture\n")
    return root, dict.fromkeys(names, "0" * 64), sorted(names)


def stages(root, names):
    absolute = tuple(sorted(str(root / name) for name in names))
    return [
        SimpleNamespace(
            name=name, inputs=absolute, input_rosters=((str(root / "tests"), absolute),)
        )
        for name in ("native", "python")
    ]


def test_full_resources_and_explicit_fixture_membership(tree):
    root, frozen, names = tree
    assert guard.require_tests_roster(root, frozen, names) == names
    assert (
        guard.require_planned_tests_roster(root, frozen, names, stages(root, names))
        == names
    )
    narrowed = dict(frozen)
    del narrowed["tests/fixtures/formalism_catalogue_155_reviewed_deltas.json"]
    with pytest.raises(ValueError, match="additions=.*reviewed_deltas"):
        guard.require_tests_roster(root, narrowed)


@pytest.mark.parametrize("change", ["addition", "deletion"])
def test_unapproved_membership_fails(tree, change):
    root, frozen, names = tree
    if change == "addition":
        (root / "tests/unapproved.json").write_bytes(b"unknown resource")
    else:
        (root / names[0]).unlink()
    with pytest.raises(ValueError, match="complete approved tests membership differs"):
        guard.require_tests_roster(root, frozen, names)


@pytest.mark.parametrize(
    "change", ["addition", "deletion", "missing-roster", "duplicate-stage"]
)
def test_planner_cannot_baseline_different_tests(tree, change):
    root, frozen, names = tree
    planned = stages(root, names)
    if change == "addition":
        planned[0].inputs += (str(root / "tests/not-approved.py"),)
    elif change == "deletion":
        planned[1].inputs = planned[1].inputs[:-1]
    elif change == "missing-roster":
        planned[0].input_rosters = ()
    else:
        planned.append(planned[0])
    with pytest.raises(ValueError, match="planned tests"):
        guard.require_planned_tests_roster(root, frozen, names, planned)


@pytest.mark.parametrize("name", sorted(guard.TESTS_EXCLUDED_DIRECTORIES))
def test_exact_case_insensitive_cache_exclusions(tree, name):
    root, frozen, names = tree
    cache = root / "tests" / name.upper()
    cache.mkdir()
    (cache / "not-an-input.py").write_text("excluded")
    assert guard.require_tests_roster(root, frozen, names) == names


@pytest.mark.parametrize("suffix", [".pyc", ".pyo", ".PYC", ".PYO"])
def test_exact_bytecode_exclusions(tree, suffix):
    root, frozen, names = tree
    (root / "tests" / ("cached" + suffix)).write_bytes(b"excluded")
    assert guard.require_tests_roster(root, frozen, names) == names


@pytest.mark.parametrize(
    "kind", ["file-link", "directory-link", "fifo", "ancestor-link"]
)
def test_symlinks_and_special_files_fail_without_following_or_blocking(tree, kind):
    root, frozen, names = tree
    if kind == "file-link":
        (root / "tests/link").symlink_to(root / names[0])
    elif kind == "directory-link":
        (root / "tests/link").symlink_to(
            root / "tests/fixtures", target_is_directory=True
        )
    elif kind == "fifo":
        os.mkfifo(root / "tests/pipe")
    else:
        link = root.parent / (root.name + "-link")
        link.symlink_to(root, target_is_directory=True)
        root = link
    with pytest.raises(ValueError, match="nonregular|symlink|ancestry"):
        guard.require_tests_roster(root, frozen, names)


def test_directory_replacement_during_enumeration_fails(tree, monkeypatch):
    root, frozen, names = tree
    original = guard.os.listdir
    moved = False

    def replace(fd):
        nonlocal moved
        entries = original(fd)
        if "test_one.py" in entries and not moved:
            moved = True
            (root / "tests").rename(root / "tests-moved")
            (root / "tests").mkdir()
        return entries

    monkeypatch.setattr(guard.os, "listdir", replace)
    with pytest.raises(
        ValueError, match="ancestry replaced|changed during enumeration"
    ):
        guard.require_tests_roster(root, frozen, names)


def test_addition_during_enumeration_fails(tree, monkeypatch):
    root, frozen, names = tree
    original = guard.os.listdir
    added = False

    def add(fd):
        nonlocal added
        entries = original(fd)
        if "test_one.py" in entries and not added:
            added = True
            (root / "tests/during-read.py").write_text("unapproved")
        return entries

    monkeypatch.setattr(guard.os, "listdir", add)
    with pytest.raises(ValueError, match="changed during enumeration"):
        guard.require_tests_roster(root, frozen, names)


def test_original_deadline_callback_is_enforced(tree):
    root, frozen, names = tree

    def expired():
        raise TimeoutError("original owner deadline")

    with pytest.raises(TimeoutError, match="original owner deadline"):
        guard.require_tests_roster(root, frozen, names, budget=expired)


@pytest.mark.parametrize(
    "bad", ["tests/../escape", "tests//a", "tests/./a", "tests/a\\b"]
)
def test_noncanonical_frozen_members_fail(tree, bad):
    root, frozen, names = tree
    frozen[bad] = "0" * 64
    with pytest.raises(ValueError, match="noncanonical"):
        guard.require_tests_roster(root, frozen, names)


def test_recorded_roster_cannot_narrow_or_reorder_map(tree):
    root, frozen, names = tree
    for altered in (names[:-1], names[::-1], names + names[:1]):
        with pytest.raises(ValueError, match="recorded tests roster differs"):
            guard.require_tests_roster(root, frozen, altered)


def test_exclusions_match_actual_maintained_planner_source():
    owner = (
        Path(__file__).resolve().parents[2]
        / "src/fep_formal/output/release_bundle/_core.py"
    )
    source = ast.parse(owner.read_text())
    assignment = next(
        node
        for node in source.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "_CAPTURE_EXCLUDED_DIRECTORIES"
            for target in node.targets
        )
    )
    assert isinstance(assignment.value, ast.Call)
    assert (
        frozenset(ast.literal_eval(assignment.value.args[0]))
        == guard.TESTS_EXCLUDED_DIRECTORIES
    )
    function = next(
        node
        for node in source.body
        if isinstance(node, ast.FunctionDef) and node.name == "_capture_directory_paths"
    )
    suffixes = next(
        ast.literal_eval(node)
        for node in ast.walk(function)
        if isinstance(node, ast.Set)
        and all(isinstance(item, ast.Constant) for item in node.elts)
    )
    assert frozenset(suffixes) == guard.TESTS_EXCLUDED_SUFFIXES


def test_hidden_noncache_resource_is_an_input(tree):
    root, frozen, names = tree
    (root / "tests/.extra-resource").write_text("unapproved")
    with pytest.raises(ValueError, match="additions=.*extra-resource"):
        guard.require_tests_roster(root, frozen, names)


def test_missing_tests_directory_is_rejected(tree):
    root, frozen, names = tree
    (root / "tests").rename(root / "tests-missing")
    with pytest.raises(FileNotFoundError):
        guard.require_tests_roster(root, frozen, names)


def test_planner_guard_obeys_original_deadline(tree):
    root, frozen, names = tree

    def expired():
        raise TimeoutError("original planning deadline")

    with pytest.raises(TimeoutError, match="original planning deadline"):
        guard.require_planned_tests_roster(
            root, frozen, names, stages(root, names), budget=expired
        )


@pytest.mark.parametrize("root_listing", [2, 3])
@pytest.mark.parametrize("mutation", ["late-addition", "child-replacement"])
def test_closed_child_is_rechecked_after_final_root_listing(
    tree, monkeypatch, mutation, root_listing
):
    root, frozen, names = tree
    original = guard.os.listdir
    calls = 0

    def mutate(fd):
        nonlocal calls
        entries = original(fd)
        if "test_one.py" in entries:
            calls += 1
            if calls == root_listing:
                fixtures = root / "tests/fixtures"
                if mutation == "late-addition":
                    (fixtures / "unapproved.json").write_text("late")
                else:
                    fixtures.rename(root / "tests/fixtures-moved")
                    fixtures.mkdir()
        return entries

    monkeypatch.setattr(guard.os, "listdir", mutate)
    with pytest.raises(
        ValueError,
        match="full scan closure|ancestry replaced|changed during enumeration",
    ):
        guard.require_tests_roster(root, frozen, names)
    assert calls >= root_listing


def test_resource_observations_include_directory_and_file_identity(tree):
    root, frozen, names = tree
    observations = {}
    guard.require_tests_roster(root, frozen, names, observations=observations)
    assert set(names) <= observations.keys()
    assert "tests/fixtures" in observations
    assert observations["tests"] == guard._tests_identity((root / "tests").stat())


@pytest.mark.parametrize("kind", ["symlink", "fifo", "oversize"])
def test_bounded_reader_rejects_special_inputs_without_reading(tree, monkeypatch, kind):
    root, _, names = tree
    path = root / names[0]
    path.unlink()
    if kind == "symlink":
        path.symlink_to(root / names[1])
    elif kind == "fifo":
        os.mkfifo(path)
    else:
        path.write_bytes(b"x" * 33)

    def forbidden(*args):
        pytest.fail("nonregular/oversized input must never be read")

    monkeypatch.setattr(guard.os, "read", forbidden)
    with pytest.raises(ValueError, match="bounded regular"):
        guard.read_regular_nofollow(path, max_bytes=32)


@pytest.mark.parametrize("substitution", ["symlink", "fifo"])
def test_reader_leaf_replacement_between_stat_and_open(tree, monkeypatch, substitution):
    root, _, names = tree
    path = root / names[0]
    original = guard.os.open

    def substitute(name, flags, *args, **kwargs):
        if name == path.name and kwargs.get("dir_fd") is not None:
            path.unlink()
            if substitution == "symlink":
                path.symlink_to(root / names[1])
            else:
                os.mkfifo(path)
            assert flags & os.O_NOFOLLOW and flags & os.O_NONBLOCK
        return original(name, flags, *args, **kwargs)

    monkeypatch.setattr(guard.os, "open", substitute)
    with pytest.raises((ValueError, OSError)):
        guard.read_regular_nofollow(path)


@pytest.mark.parametrize("restore", [False, True])
def test_reader_ancestor_symlink_substitution_never_returns_outside_bytes(
    tree, monkeypatch, restore
):
    root, _, names = tree
    owner = root / "tests/fixtures"
    path = root / names[1]
    outside = root / "outside"
    outside.mkdir()
    (outside / path.name).write_bytes(b"outside secret")
    original = guard.os.read
    returned = []
    replaced = False

    def substitute(fd, size):
        nonlocal replaced
        if not replaced:
            replaced = True
            owner.rename(root / "retained-fixtures")
            owner.symlink_to(outside, target_is_directory=True)
            returned.append(original(fd, size))
            if restore:
                owner.unlink()
                (root / "retained-fixtures").rename(owner)
            return returned[-1]
        return original(fd, size)

    monkeypatch.setattr(guard.os, "read", substitute)
    with pytest.raises(ValueError, match="ancestry changed"):
        guard.read_regular_nofollow(path)
    assert returned == [b"disposable fixture\n"]


def test_reader_deadline_and_finite_size_growth(tree, monkeypatch):
    root, _, names = tree
    path = root / names[0]
    original = guard.os.read
    total = 0

    def grow(fd, size):
        nonlocal total
        with path.open("ab") as stream:
            stream.write(b"more bytes")
        data = original(fd, size)
        total += len(data)
        return data

    monkeypatch.setattr(guard.os, "read", grow)
    initial = path.stat().st_size
    with pytest.raises(ValueError, match="identity/length changed"):
        guard.read_regular_nofollow(path)
    assert total <= initial + 1

    def expired():
        raise TimeoutError("caller deadline")

    with pytest.raises(TimeoutError, match="caller deadline"):
        guard.read_regular_nofollow(path, budget=expired)


def test_reader_keeps_declared_owner_boundary_during_unrelated_ancestor_writes(
    tree, monkeypatch
):
    root, _, names = tree
    path = root / names[0]
    original = guard.os.read
    touched = False

    def read(fd, size):
        nonlocal touched
        if not touched:
            touched = True
            (root.parent / (root.name + "-unrelated")).write_bytes(b"unrelated")
        return original(fd, size)

    monkeypatch.setattr(guard.os, "read", read)
    assert guard.read_regular_nofollow(path, owner=root) == b"disposable fixture\n"
    with pytest.raises(ValueError, match="canonical absolute"):
        guard.read_regular_nofollow(path, owner=root / "outside")
