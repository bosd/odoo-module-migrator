# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import subprocess
import re
import re._constants as sre_constants
import re._parser as sre_parse
import pathlib

from .config import _AVAILABLE_MIGRATION_STEPS
from .log import logger


def _get_available_init_version_names():
    return [x["init_version_name"] for x in _AVAILABLE_MIGRATION_STEPS]


def _get_available_target_version_names():
    return [x["target_version_name"] for x in _AVAILABLE_MIGRATION_STEPS]


def _get_latest_version_name():
    return _AVAILABLE_MIGRATION_STEPS[-1]["target_version_name"]


def _get_latest_version_code():
    return _AVAILABLE_MIGRATION_STEPS[-1]["target_version_code"]


def _execute_shell(shell_command, path=False, raise_error=True):
    if path:
        shell_command = "cd '%s' && %s" % (str(path.resolve()), shell_command)
    logger.debug("Execute Shell:\n%s" % (shell_command))
    if raise_error:
        return subprocess.check_output(shell_command, shell=True)
    else:
        return subprocess.run(shell_command, shell=True)


def _read_content(file_path):
    f = open(file_path, "r")
    text = f.read()
    f.close()
    return text


def _write_content(file_path, content):
    f = open(file_path, "w")
    f.write(content)
    f.close()


def _required_literals(pattern):
    """Return a tuple of strings, one of which is part of any match of the
    regular expression `pattern` (a compiled pattern or a string), or None
    when no such strings can be determined.

    `any(x in text for x in literals)` is a cheap and exact prefilter:
    when it is False, the pattern can not match the text.
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    if pattern.flags & re.IGNORECASE or not isinstance(pattern.pattern, str):
        return None
    try:
        literals = _required_literals_of(
            sre_parse.parse(pattern.pattern, pattern.flags)
        )
    except Exception:
        return None
    return tuple(sorted(literals)) if literals else None


def _required_literals_of(parsed):
    # Candidates are sets of strings, one of which must appear in a match.
    # Keep the most selective one: the one whose shortest string is longest.
    candidates = []
    run = ""
    for op, av in parsed:
        if op is sre_constants.LITERAL:
            run += chr(av)
            continue
        if run:
            candidates.append({run})
            run = ""
        if op is sre_constants.SUBPATTERN:
            _group, add_flags, _del_flags, subpattern = av
            if not add_flags & re.IGNORECASE:
                candidates.append(_required_literals_of(subpattern))
        elif op is sre_constants.BRANCH:
            alternatives = [_required_literals_of(branch) for branch in av[1]]
            if all(alternatives):
                candidates.append(set().union(*alternatives))
        elif op in (sre_constants.MAX_REPEAT, sre_constants.MIN_REPEAT):
            minimum, _maximum, subpattern = av
            if minimum >= 1:
                candidates.append(_required_literals_of(subpattern))
    if run:
        candidates.append({run})
    candidates = [c for c in candidates if c]
    return max(candidates, key=lambda c: min(map(len, c)), default=None)


def _could_match(literals, text):
    return literals is None or any(literal in text for literal in literals)


def _replace_in_file(file_path, replaces, log_message=False, required_literals=None):
    """Apply the `replaces` {pattern: replacement} on the file content.
    `required_literals` {pattern: literals} allows to skip the patterns
    that can not match (see `_required_literals`)."""
    current_text = _read_content(file_path)
    new_text = current_text
    required_literals = required_literals or {}

    for old_term, new_term in replaces.items():
        if not _could_match(required_literals.get(old_term), new_text):
            continue
        new_text = re.sub(old_term, new_term or "", new_text)

    # Write file if changed
    if new_text != current_text:
        if not log_message:
            log_message = "Changing content of file: %s" % file_path.name
        logger.info(log_message)
        _write_content(file_path, new_text)
    return new_text


def get_files(module_path, extensions):
    """
    Returns a list of files with the specified extensions within the module_path.
    """
    file_paths = []
    module_dir = pathlib.Path(module_path)

    if not module_dir.is_dir():
        raise Exception(f"'{module_path}' is not a valid directory.")

    for ext in extensions:
        file_paths.extend(module_dir.rglob(f"*{ext}"))

    return file_paths
