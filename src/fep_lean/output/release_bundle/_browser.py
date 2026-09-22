"""Browser-acceptance receipt validation for the release bundle."""

import re
import struct
import zlib
from pathlib import Path

from fep_lean.output import release_bundle as bundle
from fep_lean.output.browser_capture import (
    BROWSER_ASSET_ROOT,
    BROWSER_RECEIPT,
    BrowserCaptureError,
    canonical_browser_observations,
    canonical_browser_render_configuration,
    resolve_browser_executable,
)
from fep_lean.output.browser_capture import (
    CANONICAL_BROWSER_PROJECTIONS as _CANONICAL_BROWSER_PROJECTIONS,
)
from fep_lean.output.browser_capture import (
    CANONICAL_BROWSER_SCREENSHOTS as _CANONICAL_BROWSER_SCREENSHOTS,
)
from fep_lean.output.browser_capture import (
    REQUIRED_BROWSER_INTERACTIONS as _REQUIRED_BROWSER_INTERACTIONS,
)
from fep_lean.output.formalism_presentation import (
    RELEASE_CAPABILITIES,
    RELEASE_FAMILIES,
    RELEASE_RELATIONS,
    RELEASE_TOPICS,
    RELEASE_WITNESSES,
    FormalismPresentation,
)
from fep_lean.output.fsutil import sha256_bytes
from fep_lean.output.release_bundle._constants import (
    _SHA256_RE,
)
from fep_lean.output.release_bundle._core import (
    ReleaseBundleError,
    _json_object,
    _relative_file_bytes,
    _safe_member_name,
)


def _png_dimensions(data: bytes) -> tuple[int, int]:
    """Validate a complete PNG chunk stream and return its IHDR dimensions."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ReleaseBundleError("browser screenshot is not a PNG stream")
    offset = 8
    dimensions: tuple[int, int] | None = None
    saw_image_data = False
    saw_end = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ReleaseBundleError("browser screenshot has a truncated PNG chunk")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        payload_end = offset + 8 + length
        crc_end = payload_end + 4
        if crc_end > len(data):
            raise ReleaseBundleError("browser screenshot has a truncated PNG payload")
        payload = data[offset + 8 : payload_end]
        recorded_crc = struct.unpack(">I", data[payload_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
        if recorded_crc != actual_crc:
            raise ReleaseBundleError("browser screenshot has an invalid PNG checksum")
        if chunk_type == b"IHDR":
            if dimensions is not None or length != 13 or offset != 8:
                raise ReleaseBundleError("browser screenshot has an invalid PNG header")
            width, height = struct.unpack(">II", payload[:8])
            if width <= 0 or height <= 0:
                raise ReleaseBundleError(
                    "browser screenshot dimensions must be positive"
                )
            dimensions = (width, height)
        elif chunk_type == b"IDAT":
            saw_image_data = True
        elif chunk_type == b"IEND":
            if length != 0:
                raise ReleaseBundleError(
                    "browser screenshot has an invalid PNG terminator"
                )
            saw_end = True
            offset = crc_end
            break
        offset = crc_end
    if dimensions is None or not saw_image_data or not saw_end or offset != len(data):
        raise ReleaseBundleError("browser screenshot PNG stream is incomplete")
    return dimensions


def _live_browser_identity(name: str, executable: Path) -> tuple[str, str]:
    """Identify the exact receipt-recorded browser, never a PATH substitute."""
    resolved_path = Path(executable)
    try:
        replayable = (
            resolved_path.is_absolute()
            and not resolved_path.is_symlink()
            and resolved_path.is_file()
            and resolved_path.resolve() == resolved_path
        )
    except OSError as exc:
        raise ReleaseBundleError(
            f"browser receipt executable path is not replayable: {resolved_path}"
        ) from exc
    if not replayable:
        raise ReleaseBundleError(
            f"browser receipt executable path is not replayable: {resolved_path}"
        )
    try:
        _detected_name, _path, version, digest = resolve_browser_executable(
            browser_name=name,
            executable=resolved_path,
        )
    except BrowserCaptureError as exc:
        raise ReleaseBundleError(str(exc)) from exc
    return version, digest


def _browser_receipt_errors(
    project_root: Path,
    *,
    presentation: FormalismPresentation | None = None,
) -> tuple[str, ...]:
    root = Path(project_root).resolve()
    path = root / BROWSER_RECEIPT
    payload, error = _json_object(path, "browser receipt")
    if payload is None:
        return (error or "browser receipt is invalid",)
    errors: list[str] = []
    if payload.get("schema_version") != 4:
        errors.append("browser receipt schema_version must be 4")
    if payload.get("kind") != "browser-interaction":
        errors.append("browser receipt kind must be browser-interaction")
    if payload.get("accepted") is not True:
        errors.append("browser receipt must be accepted")
    browser = payload.get("browser")
    browser_name: str | None = None
    browser_executable: Path | None = None
    if not isinstance(browser, dict) or set(browser) != {
        "name",
        "version",
        "executable_path",
        "executable_sha256",
    }:
        errors.append("browser receipt identity is incomplete")
    else:
        name = browser.get("name")
        version = browser.get("version")
        executable_path = browser.get("executable_path")
        executable_sha256 = browser.get("executable_sha256")
        if name not in {"Google Chrome", "Chromium"}:
            errors.append("browser receipt name must identify Chrome or Chromium")
        if (
            not isinstance(version, str)
            or re.fullmatch(r"\d+\.\d+\.\d+\.\d+", version) is None
        ):
            errors.append("browser receipt version is invalid")
        if (
            not isinstance(executable_sha256, str)
            or _SHA256_RE.fullmatch(executable_sha256) is None
        ):
            errors.append("browser executable hash is invalid")
        elif executable_sha256 == "0" * 64:
            errors.append("browser executable hash cannot be the all-zero sentinel")
        if not isinstance(executable_path, str) or not executable_path:
            errors.append("browser executable path is invalid")
        elif not Path(executable_path).is_absolute():
            errors.append("browser executable path must be absolute")
        else:
            browser_executable = Path(executable_path)
        if (
            isinstance(name, str)
            and name in {"Google Chrome", "Chromium"}
            and browser_executable is not None
        ):
            browser_name = name
            try:
                live_version, live_digest = _live_browser_identity(
                    name, browser_executable
                )
            except ReleaseBundleError as exc:
                errors.append(str(exc))
            else:
                if version != live_version:
                    errors.append(
                        "browser receipt version differs from the live browser"
                    )
                if executable_sha256 != live_digest:
                    errors.append(
                        "browser executable hash differs from the live browser binary"
                    )
    render_configuration = payload.get("render_configuration")
    if render_configuration != canonical_browser_render_configuration():
        errors.append("browser render configuration is not canonical")
    render_environment = payload.get("render_environment")
    render_environment_keys = {
        "browser_locale",
        "device_pixel_ratio",
        "platform",
        "timezone",
        "webgl_renderer",
        "webgl_vendor",
    }
    if (
        not isinstance(render_environment, dict)
        or set(render_environment) != render_environment_keys
        or not all(
            isinstance(value, str) and value for value in render_environment.values()
        )
        or render_environment.get("browser_locale") != "en-US"
        or render_environment.get("device_pixel_ratio") != "1"
        or render_environment.get("timezone") != "UTC"
    ):
        errors.append("browser render environment is not canonical")
    capture = payload.get("capture")
    try:
        canonical_capture = bundle.canonical_browser_capture_provenance(root)
    except BrowserCaptureError as exc:
        errors.append(str(exc))
    else:
        if capture != canonical_capture:
            errors.append("browser capture provenance is not canonical")
    interactions = payload.get("interactions")
    if not isinstance(interactions, dict) or set(interactions) != set(
        _REQUIRED_BROWSER_INTERACTIONS
    ):
        errors.append("browser interaction roster is not canonical")
    elif any(interactions[key] is not True for key in _REQUIRED_BROWSER_INTERACTIONS):
        errors.append("browser interaction checks must all be true")
    expected = payload.get("expected")
    observed = payload.get("observed")
    if not isinstance(expected, dict) or observed != expected:
        errors.append("browser receipt observed and expected values must match exactly")
    try:
        if presentation is None:
            presentation = bundle.build_formalism_presentation(root)
        required_counts = {
            "topics": len(presentation.topics),
            "families": len(presentation.families),
            "witnesses": len(presentation.witnesses),
            "relations": len(presentation.relations),
            "capabilities": len(presentation.capabilities),
        }
    except (OSError, TypeError, ValueError) as exc:
        errors.append(f"live browser presentation cannot be loaded: {exc}")
        required_counts = {
            "topics": RELEASE_TOPICS,
            "families": RELEASE_FAMILIES,
            "witnesses": RELEASE_WITNESSES,
            "relations": RELEASE_RELATIONS,
            "capabilities": RELEASE_CAPABILITIES,
        }
    if required_counts != {
        "topics": RELEASE_TOPICS,
        "families": RELEASE_FAMILIES,
        "witnesses": RELEASE_WITNESSES,
        "relations": RELEASE_RELATIONS,
        "capabilities": RELEASE_CAPABILITIES,
    }:
        errors.append("live presentation does not match the 155-topic release seal")
    if isinstance(expected, dict):
        for key, value in required_counts.items():
            if expected.get(key) != value:
                errors.append(f"browser receipt expected.{key} is stale")
    canonical_observations = canonical_browser_observations(required_counts)
    if expected != canonical_observations or observed != canonical_observations:
        errors.append("browser receipt detailed DOM observations are not canonical")

    projections = payload.get("projections")
    if not isinstance(projections, dict) or set(projections) != set(
        _CANONICAL_BROWSER_PROJECTIONS
    ):
        errors.append("browser receipt projection roster is not canonical")
        projections = {}
    for key, canonical_path in _CANONICAL_BROWSER_PROJECTIONS.items():
        record = projections.get(key)
        if not isinstance(record, dict) or record.get("path") != canonical_path:
            errors.append(f"browser receipt projection path is invalid: {key}")
            continue
        digest = record.get("sha256")
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            errors.append(f"browser receipt projection hash is invalid: {key}")
            continue
        try:
            actual = sha256_bytes(_relative_file_bytes(root, canonical_path))
        except ReleaseBundleError as exc:
            errors.append(str(exc))
            continue
        if digest != actual:
            errors.append(f"browser receipt projection hash is stale: {key}")

    screenshots = payload.get("screenshots")
    if not isinstance(screenshots, list) or len(screenshots) != len(
        _CANONICAL_BROWSER_SCREENSHOTS
    ):
        errors.append("browser receipt screenshot roster is not canonical")
        screenshots = []
    screenshot_paths: list[str] = []
    screenshot_roles: list[str] = []
    screenshot_data_by_role: dict[str, bytes] = {}
    for index, record in enumerate(screenshots):
        if not isinstance(record, dict):
            errors.append(f"browser screenshot record {index} must be an object")
            continue
        if set(record) != {"role", "path", "sha256", "width", "height"}:
            errors.append(f"browser screenshot record fields are invalid: {index}")
        role = record.get("role")
        relative = record.get("path")
        digest = record.get("sha256")
        width = record.get("width")
        height = record.get("height")
        if (
            not isinstance(role, str)
            or role not in _CANONICAL_BROWSER_SCREENSHOTS
            or relative != _CANONICAL_BROWSER_SCREENSHOTS.get(role)
        ):
            errors.append(f"browser screenshot role/path is invalid: {role}")
            continue
        if role in screenshot_roles:
            errors.append(f"duplicate browser screenshot role: {role}")
            continue
        screenshot_roles.append(role)
        if (
            not isinstance(relative, str)
            or not relative.startswith(f"{BROWSER_ASSET_ROOT.as_posix()}/")
            or not _safe_member_name(relative)
        ):
            errors.append(f"browser screenshot path is invalid: {relative}")
            continue
        if relative in screenshot_paths:
            errors.append(f"duplicate browser screenshot path: {relative}")
            continue
        screenshot_paths.append(relative)
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            errors.append(f"browser screenshot hash is invalid: {relative}")
            continue
        try:
            screenshot_data = _relative_file_bytes(root, relative)
            actual = sha256_bytes(screenshot_data)
            actual_width, actual_height = _png_dimensions(screenshot_data)
        except ReleaseBundleError as exc:
            errors.append(str(exc))
            continue
        screenshot_data_by_role[role] = screenshot_data
        if digest != actual:
            errors.append(f"browser screenshot hash is stale: {relative}")
        if type(width) is not int or type(height) is not int:
            errors.append(f"browser screenshot dimensions are invalid: {relative}")
        elif (width, height) != (actual_width, actual_height):
            errors.append(f"browser screenshot dimensions are stale: {relative}")
        elif role.endswith("_mobile") and (width != 390 or height < 844):
            errors.append(f"browser mobile screenshot viewport is invalid: {relative}")
        elif role.endswith("_desktop") and (width < 1200 or height < 800):
            errors.append(f"browser desktop screenshot viewport is invalid: {relative}")
        elif role.endswith("_standalone") and (width < 1200 or height < 800):
            errors.append(
                f"browser standalone screenshot viewport is invalid: {relative}"
            )
    if screenshot_paths != sorted(screenshot_paths):
        errors.append("browser screenshot paths must be lexically ordered")
    if set(screenshot_roles) != set(_CANONICAL_BROWSER_SCREENSHOTS):
        errors.append("browser receipt screenshot roles are incomplete")
    if not errors and browser_name is not None and browser_executable is not None:
        try:
            replay = bundle.replay_browser_acceptance(
                root,
                browser_name=browser_name,
                executable=browser_executable,
            )
        except BrowserCaptureError as exc:
            errors.append(f"live Chrome browser replay failed: {exc}")
        else:
            if replay.browser != browser:
                errors.append(
                    "browser receipt identity differs from live Chrome replay"
                )
            if replay.render_configuration != render_configuration:
                errors.append(
                    "browser render configuration differs from live Chrome replay"
                )
            if replay.render_environment != render_environment:
                errors.append(
                    "browser render environment differs from live Chrome replay"
                )
            if replay.observations != observed:
                errors.append(
                    "browser receipt observations differ from live Chrome replay"
                )
            if replay.interactions != interactions:
                errors.append(
                    "browser receipt interactions differ from live Chrome replay"
                )
            for role, relative in _CANONICAL_BROWSER_SCREENSHOTS.items():
                if replay.screenshot_bytes.get(role) != screenshot_data_by_role.get(
                    role
                ):
                    errors.append(
                        f"browser screenshot differs from live Chrome capture: {relative}"
                    )
    return tuple(dict.fromkeys(errors))


def _browser_screenshot_paths(project_root: Path) -> tuple[str, ...]:
    payload, error = _json_object(
        Path(project_root) / BROWSER_RECEIPT, "browser receipt"
    )
    if payload is None:
        raise ReleaseBundleError(error or "browser receipt is invalid")
    screenshots = payload.get("screenshots")
    if not isinstance(screenshots, list):
        raise ReleaseBundleError("browser receipt screenshots must be a list")
    paths: list[str] = []
    for record in screenshots:
        if not isinstance(record, dict):
            raise ReleaseBundleError("browser receipt screenshot paths are invalid")
        relative = record.get("path")
        if not isinstance(relative, str):
            raise ReleaseBundleError("browser receipt screenshot paths are invalid")
        paths.append(relative)
    return tuple(paths)
