"""Python source text must not be confused with executable operations."""

import pytest

from gitskills.analysis.analyzer import SkillAnalyzer
from gitskills.analysis.comparator import compare_results
from gitskills.analysis.risk_assessor import RiskAssessor


def _review(source: str, *, filename: str = "scripts/example.py"):
    analyzer = SkillAnalyzer()
    base = analyzer.scan("", filename=filename)
    derived = analyzer.scan(source, filename=filename)
    return derived, RiskAssessor().assess(compare_results(base, derived))


@pytest.mark.parametrize(("source", "context"), [
    ('print("FastAPI não instalado. Execute: pip install fastapi uvicorn")',
     "source_literal"),
    ('"""Usage:\npython scripts/export.py --format json\n"""', "source_docstring"),
    ('def usage():\n    """Run python scripts/install.py --force"""\n    return None',
     "source_docstring"),
    ('print("example")  # pip install pandas pyarrow', "source_comment"),
    ('command = "pip install pandas"\nsubprocess.run(command, shell=True)',
     "source_literal"),
])
def test_non_executable_python_text_never_supports_install_or_script_execution(source, context):
    scan, assessment = _review(source)
    assert scan.evidence
    assert scan.evidence[0].context.kind == context
    assert scan.rule_match_count > 0  # Retain raw detection and review evidence.
    assert not any(item.indicator_id in {"RI-005", "RI-010"}
                   for item in assessment.supported)
    assert any(item.indicator_id in {"RI-005", "RI-010"}
               for item in assessment.uncertain)
    assert assessment.coverage == "complete"  # Source was captured fully.


def test_python_docstring_with_multiple_script_examples_remains_uncertain():
    source = ('"""\npython scripts/export.py --format json\n'
              'python scripts/export.py --format csv\n"""\n')
    scan, assessment = _review(source)
    assert len(scan.evidence) == 2
    assert all(item.context.kind == "source_docstring" for item in scan.evidence)
    assert not assessment.supported
    assert {item.indicator_id for item in assessment.uncertain} == {"RI-010"}


@pytest.mark.parametrize("source", [
    'import subprocess\nsubprocess.run("pip install requests", shell=True)',
    'import os\nos.system("pip install requests")',
    'import subprocess\nsubprocess.run(f"pip install {package}", shell=True)',
])
def test_direct_python_execution_calls_retain_supported_install_indicators(source):
    scan, assessment = _review(source)
    assert any(item.indicator_id == "RI-005" for item in assessment.supported)
    assert any(item.context.kind == "source_code" and item.kind == "api_call"
               for item in scan.evidence)


def test_nested_print_inside_execution_call_is_not_an_executable_command():
    scan, assessment = _review(
        'import subprocess\nsubprocess.run(print("pip install requests"), shell=True)'
    )
    # The outer subprocess call absorbs the nested string into one API record.
    assert scan.evidence[0].kind == "api_call"
    assert not any(item.indicator_id == "RI-005" for item in assessment.supported)
    assert any(item.indicator_id == "RI-005" for item in assessment.uncertain)


def test_python_utf8_offset_mapping_finds_the_correct_string():
    scan, assessment = _review('print("ação: pip install requests")')
    command = next(item for item in scan.evidence if "pip install" in item.raw_text)
    assert command.context.kind == "source_literal"
    assert not any(item.indicator_id == "RI-005" for item in assessment.supported)


def test_markdown_instruction_remains_supported():
    _, assessment = _review('```bash\npip install fastapi\npython scripts/setup.py\n```',
                            filename="SKILL.md")
    assert {"RI-005", "RI-010"}.issubset(
        {item.indicator_id for item in assessment.supported}
    )


def test_python_comment_classification_uses_position_not_entire_line():
    scan, assessment = _review('subprocess.run("pip install requests", shell=True)  # unrelated')
    install = next(item for item in scan.evidence if "pip install" in item.raw_text)
    assert install.context.kind == "source_code"
    assert any(item.indicator_id == "RI-005" for item in assessment.supported)


def test_python_literal_context_distinguishes_direct_execution_from_printing():
    from gitskills.analysis.python_source_context import PythonSourceContext

    source = ('import subprocess\n'
              'subprocess.run("pip install requests", shell=True)\n'
              'print("pip install pandas")\n')
    first = source.index("pip install")
    second = source.index("pip install", first + 1)
    contexts = PythonSourceContext(source)
    assert contexts.kind_at(first) == "source_execution"
    assert contexts.kind_at(second) == "source_literal"
