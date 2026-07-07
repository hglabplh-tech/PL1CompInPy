import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = PROJECT_ROOT / "scripts" / "generate_api_docs.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_api_docs", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DocumentationTests(unittest.TestCase):
    def test_api_doc_generator_documents_project_surface(self):
        generator = load_generator()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "API.md"
            docs = generator.write_api_docs(PROJECT_ROOT / "src" / "pl1compinpy", output)
            text = output.read_text(encoding="utf-8")

        self.assertGreaterEqual(docs.class_count, 100)
        self.assertGreaterEqual(docs.function_count, 390)
        self.assertIn("`pl1compinpy.codegen.runtime_link`", text)
        self.assertIn("`RuntimeLinkage`", text)
        self.assertIn("`Parser.parse`", text)
        self.assertIn("`compile_source`", text)
        self.assertIn("`IncludeExpander`", text)
        self.assertIn("`DynamicLoadRuntime`", text)
        self.assertIn("`emit_library`", text)
        self.assertIn("`StructureRuntime`", text)
        self.assertIn("`FieldReference`", text)


if __name__ == "__main__":
    unittest.main()
