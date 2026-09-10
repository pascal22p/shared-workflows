import sys
from pathlib import Path

# Add scripts directory to sys.path to allow importing publish_review
scripts_dir = str(Path(__file__).resolve().parent.parent.parent / "scala-ai-review-publish" / "scripts")
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from publish_review import parse_diff, map_findings


def test_parse_diff():
    diff = """diff --git a/file1.scala b/file1.scala
index 1234567..89abcdef 100644
--- a/file1.scala
+++ b/file1.scala
@@ -1,5 +1,6 @@
 unchanged line 1
 unchanged line 2
-removed line 3
+added line 3
+added line 4
 unchanged line 5
 unchanged line 6
"""
    valid_lines = parse_diff(diff)
    
    assert "file1.scala" in valid_lines
    # Lines in new file (RIGHT side):
    # 1: unchanged line 1
    # 2: unchanged line 2
    # 3: added line 3
    # 4: added line 4
    # 5: unchanged line 5
    # 6: unchanged line 6
    assert valid_lines["file1.scala"] == {1, 2, 3, 4, 5, 6}


def test_map_findings_exact_match():
    valid_lines = {"file1.scala": {1, 2, 3, 4}}
    findings = [
        {"file": "file1.scala", "line": 3, "title": "Test Finding", "body": "Body", "severity": "HIGH"}
    ]
    
    comments = map_findings(findings, valid_lines, "test-model", "high")
    
    assert len(comments) == 1
    assert comments[0]["path"] == "file1.scala"
    assert comments[0]["line"] == 3
    assert "test-model" in comments[0]["body"]
    assert "high" in comments[0]["body"]


def test_map_findings_snap_to_nearest():
    # Finding is on line 5, but only lines 1-4 and 7-10 are valid
    valid_lines = {"file1.scala": {1, 2, 3, 4, 7, 8, 9, 10}}
    findings = [
        {"file": "file1.scala", "line": 5, "title": "Off-by-one", "body": "Body"}
    ]
    
    comments = map_findings(findings, valid_lines, "test-model", "high")
    
    assert len(comments) == 1
    assert comments[0]["line"] == 4  # Snapped to nearest valid line (4 is closer to 5 than 7)


def test_map_findings_too_far():
    valid_lines = {"file1.scala": {1, 2, 10, 11}}
    findings = [
        {"file": "file1.scala", "line": 6, "title": "Too far", "body": "Body"}
    ]
    
    comments = map_findings(findings, valid_lines, "test-model", "high")
    
    assert len(comments) == 0  # 6 is > 3 away from any valid line
