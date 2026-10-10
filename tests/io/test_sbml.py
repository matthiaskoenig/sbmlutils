"""Test SBML reading and writing."""

import logging
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import libsbml
import pytest
from paths import NON_ASCII_DIR, SPACE_DIR

from sbmlutils.io.sbml import read_sbml, validate_sbml, write_sbml
from sbmlutils.resources import BASIC_SBML, GZ_SBML


@pytest.mark.parametrize("source", [BASIC_SBML, GZ_SBML])
def test_sbml_input_limit(source: Path) -> None:
    """Both reading and validation enforce a caller's decompressed byte limit."""
    assert read_sbml(source, max_bytes=10_000_000).getModel()
    with pytest.raises(ValueError, match="exceeds max_bytes"):
        read_sbml(source, max_bytes=1)
    with pytest.raises(ValueError, match="exceeds max_bytes"):
        validate_sbml(source, max_bytes=1)


def test_xml_string_input_limit() -> None:
    """XML strings obey the same byte limit as files."""
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
        'level="3" version="2"><model id="m"/></sbml>'
    )
    assert read_sbml(xml, max_bytes=len(xml)).getModel().getId() == "m"
    with pytest.raises(ValueError, match="exceeds max_bytes"):
        read_sbml(xml, max_bytes=len(xml) - 1)


def test_external_models_can_be_refused_before_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An untrusted comp document is rejected before resolving external models."""
    ns = libsbml.SBMLNamespaces(3, 2)
    ns.addPackageNamespace("comp", 1)
    doc = libsbml.SBMLDocument(ns)
    doc.setPackageRequired("comp", True)
    doc.createModel().setId("m")
    external = doc.getPlugin("comp").createExternalModelDefinition()
    external.setId("external")
    external.setSource("file:///untrusted/model.xml")
    xml = libsbml.writeSBMLToString(doc)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Validation was attempted")

    monkeypatch.setattr("sbmlutils.io.sbml.validate_doc", forbidden)
    with pytest.raises(ValueError, match="External comp model references are disabled"):
        read_sbml(xml, validate=True, allow_external_models=False)
    with pytest.raises(ValueError, match="External comp model references are disabled"):
        validate_sbml(xml, allow_external_models=False)


def test_read_sbml_from_path() -> None:
    """Read from path."""
    doc = read_sbml(BASIC_SBML)
    assert doc
    assert doc.getModel()


def test_read_sbml_from_strpath() -> None:
    """Read from strpath (os.path)."""
    doc = read_sbml(str(BASIC_SBML))
    assert doc
    assert doc.getModel()


def test_string_path_does_not_log_an_error(caplog: pytest.LogCaptureFixture) -> None:
    """A documented string filename is an ordinary successful read."""
    with caplog.at_level(logging.ERROR, logger="sbmlutils.io.sbml"):
        assert read_sbml(str(BASIC_SBML)).getModel()
    assert not caplog.records


@pytest.mark.parametrize(
    "module", ["sbmlutils.io.sbml", "sbmlutils.factory", "sbmlutils.parser"]
)
def test_converters_are_imported_only_when_used(module: str) -> None:
    """Ordinary IO, factory and parser imports do not load optional workflows."""
    subprocess.run(
        [
            sys.executable,
            "-c",
            f"import {module}; import sys; "
            "assert 'antimony' not in sys.modules; assert 'sbmlode' not in sys.modules",
        ],
        check=True,
    )


def test_prefixed_sbml_string() -> None:
    """XML namespace prefixes do not turn SBML content into a filename."""
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<s:sbml xmlns:s="http://www.sbml.org/sbml/level3/version2/core" '
        'level="3" version="2"><s:model id="prefixed"/></s:sbml>'
    )
    assert read_sbml(xml).getModel().getId() == "prefixed"
    assert validate_sbml(xml).is_valid()


def test_malformed_xml_string_is_validated_as_content() -> None:
    """Malformed XML produces validation errors, rather than a missing file."""
    assert not validate_sbml("<s:sbml broken").is_valid()


def test_read_sbml_from_str() -> None:
    """Read SBML str."""
    doc1 = read_sbml(str(BASIC_SBML))
    sbml_str = write_sbml(doc1)
    assert sbml_str

    if sbml_str:
        doc = read_sbml(sbml_str)
        assert doc
        assert doc.getModel()


def test_read_sbml_from_gz() -> None:
    """Read SBML str."""
    doc1 = read_sbml(GZ_SBML)
    sbml_str = write_sbml(doc1)
    assert sbml_str

    if sbml_str:
        doc = read_sbml(sbml_str)
        assert doc
        assert doc.getModel()


def test_read_sbml_from_gzstr() -> None:
    """Read SBML str."""
    doc1 = read_sbml(str(GZ_SBML))
    sbml_str = write_sbml(doc1)

    assert sbml_str
    if sbml_str:
        doc = read_sbml(sbml_str)
        assert doc
        assert doc.getModel()


def test_read_sbml_validate() -> None:
    """Read and validate."""
    doc = read_sbml(BASIC_SBML, validate=True)
    assert doc
    assert doc.getModel()


def test_write_sbml(tmp_path: Path) -> None:
    """Test writing SBML."""
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    model.setId("test_id")

    sbml_path = tmp_path / "tests.xml"
    write_sbml(doc=doc, filepath=sbml_path)
    assert sbml_path.exists()

    doc2 = read_sbml(source=sbml_path)
    assert doc2
    assert doc2.getModel()


def test_write_sbml_creates_the_parent_directory(tmp_path: Path) -> None:
    """Test that a write into a directory which does not exist yet creates it.

    `libsbml.SBMLWriter.writeSBMLToFile` answers `False` for a path whose
    parent does not exist and writes nothing, which the writer used to
    discard: no file was written and nothing was reported.
    """
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    model.setId("test_id")

    sbml_path = tmp_path / "does" / "not" / "exist" / "model.xml"
    write_sbml(doc=doc, filepath=sbml_path)

    assert sbml_path.exists()
    assert read_sbml(source=sbml_path).getModel().getId() == "test_id"


def test_write_sbml_raises_when_the_file_cannot_be_written(tmp_path: Path) -> None:
    """Test that a write which cannot be repaired raises, naming the path.

    A directory which does not exist is the one failure a writer can repair;
    a parent which is a file is not. Such a write used to be discarded, and
    `create_model` went on to report `valid: TRUE` for a file it never wrote:
    the validation re-reads the path, and an unreadable file gives an empty
    document, which is valid.
    """
    blocking_file = tmp_path / "a_file"
    blocking_file.write_text("not a directory", encoding="utf-8")
    sbml_path = blocking_file / "model.xml"

    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    doc.createModel().setId("test_id")

    with pytest.raises(OSError, match=re.escape(str(sbml_path))):
        write_sbml(doc=doc, filepath=sbml_path)

    assert not sbml_path.exists()


_SBML_WITHOUT_MODEL = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
    'level="3" version="2"/>'
)

_SBML_COMP_LIBRARY = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
    'xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" '
    'level="3" version="2" comp:required="true">'
    "<comp:listOfModelDefinitions>"
    '<comp:modelDefinition id="md"/>'
    "</comp:listOfModelDefinitions>"
    "</sbml>"
)

_SBML_TRUNCATED = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
    'level="3" version="2"><model id="m"><listOfParameters>'
)


@pytest.mark.parametrize("promote", [False, True])
def test_read_sbml_raises_for_a_file_which_does_not_exist(
    tmp_path: Path, promote: bool
) -> None:
    """An unreadable file raises with the libsbml error instead of only logging it.

    The error used to be logged and a document without a model returned, on
    which the promotion of local parameters crashed with an AttributeError.
    """
    with pytest.raises(ValueError, match=r"does_not_exist\.xml.*\n.*E2 "):
        read_sbml(tmp_path / "does_not_exist.xml", promote=promote)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("<sbml garbage", id="unclosed"),
        pytest.param(_SBML_TRUNCATED, id="truncated"),
    ],
)
def test_read_sbml_raises_for_malformed_xml(source: str) -> None:
    """A string which is not well-formed XML raises and names the libsbml errors."""
    with pytest.raises(ValueError, match=r"could not be read:\n.*E\d+"):
        read_sbml(source)


@pytest.mark.parametrize("promote", [False, True])
@pytest.mark.parametrize(
    "source",
    [
        pytest.param(_SBML_WITHOUT_MODEL, id="without-model"),
        pytest.param(_SBML_COMP_LIBRARY, id="comp-library"),
    ],
)
def test_read_sbml_returns_a_valid_document_without_a_model(
    source: str, promote: bool
) -> None:
    """A document without a model is valid SBML from L3V2 on and is read as it is."""
    doc = read_sbml(source, promote=promote)
    assert doc.getModel() is None
    assert doc.getNumErrors() == 0


def test_read_sbml_reads_a_document_with_errors_in_its_content() -> None:
    """Errors in the SBML content are for the validation, the document is read."""
    doc = read_sbml(
        _SBML_WITHOUT_MODEL.replace("/>", '><model id="m" foo="1"/></sbml>')
    )
    assert doc.getModel().getId() == "m"
    assert doc.getError(0).getErrorId() == libsbml.AllowedAttributesOnModel


def test_read_sbml_error_does_not_repeat_long_source() -> None:
    """A non-SBML string treated as a path is shortened in the message."""
    from sbmlutils.io.sbml import validate_sbml

    source = "x" * 5000
    with pytest.raises(FileNotFoundError) as excinfo:
        validate_sbml(source)
    assert len(str(excinfo.value)) < 300
    assert "..." in str(excinfo.value)


def _raise_name_too_long(self: Path, *_args: object, **_kwargs: object) -> bool:
    """Answer a file system check as python < 3.14 does for a very long name."""
    raise OSError(36, "File name too long", str(self))


def test_validate_sbml_raises_for_a_long_string_the_file_system_rejects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A string the file system rejects as a path is no file, it does not crash.

    Before python 3.14 `Path.exists()` and `Path.is_file()` raise
    `OSError: [Errno 36] File name too long` for a string longer than a file
    name may be, instead of answering `False`; the check is emulated here so
    that the behaviour of every python version is tested on every version.
    """
    from sbmlutils.io.sbml import validate_sbml

    monkeypatch.setattr(Path, "exists", _raise_name_too_long)
    monkeypatch.setattr(Path, "is_file", _raise_name_too_long)
    with pytest.raises(FileNotFoundError, match="SBML file does not exist"):
        validate_sbml("x" * 5000)


PATH_DIRS = [SPACE_DIR, NON_ASCII_DIR]


def _model_doc(model_id: str = "m") -> libsbml.SBMLDocument:
    """Create a document with a model which has a non-ASCII name."""
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    model.setId(model_id)
    model.setName("über")
    return doc


@pytest.mark.parametrize("path_dir", PATH_DIRS)
def test_write_and_read_sbml_in_a_directory_with_a_special_character(
    tmp_path: Path, path_dir: str
) -> None:
    """A path with a space or a non-ASCII character is written, read and validated."""
    from sbmlutils.io.sbml import validate_sbml

    sbml_path = tmp_path / path_dir / "model.xml"
    write_sbml(_model_doc(), filepath=sbml_path, validate=True)

    doc = read_sbml(sbml_path)
    assert doc.getModel().getName() == "über"
    assert doc.getLocationURI() == f"file:{sbml_path.resolve()}"
    assert validate_sbml(sbml_path).is_valid()


def _unreadable(*_args: object) -> libsbml.SBMLDocument:
    """Answer as `libsbml.readSBMLFromFile` does for a path it cannot open."""
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    doc.getErrorLog().add(
        libsbml.SBMLError(libsbml.XMLFileUnreadable, doc.getLevel(), doc.getVersion())
    )
    return doc


def test_a_non_ascii_path_does_not_use_the_file_functions_of_libsbml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-ASCII path is written and read by python, as it works on Windows.

    libsbml cannot open a path with a non-ASCII character on Windows:
    `readSBMLFromFile` answers "File unreadable" and `writeSBMLToFile` answers
    `False`. Both failures are emulated here, so that the fallback is known to
    work without them on every platform.
    """
    from sbmlutils.io.sbml import validate_sbml

    monkeypatch.setattr(libsbml.SBMLWriter, "writeSBMLToFile", lambda *_args: False)
    monkeypatch.setattr(libsbml, "readSBMLFromFile", _unreadable)
    sbml_path = tmp_path / "ü" / "model.xml"

    write_sbml(_model_doc("m1"), filepath=sbml_path)

    assert read_sbml(sbml_path).getModel().getId() == "m1"
    assert validate_sbml(sbml_path).is_valid()


def test_an_ascii_path_uses_the_file_functions_of_libsbml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A path libsbml can open on every platform is read and written by libsbml."""
    monkeypatch.setattr(libsbml.SBMLWriter, "writeSBMLToFile", lambda *_args: False)
    monkeypatch.setattr(libsbml, "readSBMLFromFile", _unreadable)
    sbml_path = tmp_path / "model.xml"

    with pytest.raises(OSError, match="libsbml's writer refused the path"):
        write_sbml(_model_doc(), filepath=sbml_path)
    sbml_path.write_text(libsbml.writeSBMLToString(_model_doc()), encoding="utf-8")
    with pytest.raises(ValueError, match="E2 "):
        read_sbml(sbml_path)


@pytest.mark.parametrize("path_dir", ["ascii", "ü"])
@pytest.mark.parametrize(
    "filename", ["m.xml.gz", "m.xml.bz2", "m.xml.zip", "m.zip", "m.xml.GZ"]
)
def test_compressed_files_are_compatible_with_libsbml(
    tmp_path: Path, path_dir: str, filename: str
) -> None:
    """A compressed file is written and read as libsbml writes and reads it.

    libsbml compresses by the suffix of the path, `.gz`, `.bz2` or `.zip`, in
    lower case only, and names the entry of a zip archive after the path
    without `.zip`, with `.xml` added unless it ends in `.xml` or `.sbml`. The
    non-ASCII directory is written and read by python; libsbml writes and reads
    its own files in an ASCII directory, which it can open on every platform.
    """
    ours = tmp_path / path_dir / filename
    theirs = tmp_path / "theirs" / filename
    theirs.parent.mkdir()
    write_sbml(_model_doc("ours"), filepath=ours)
    assert libsbml.writeSBMLToFile(_model_doc("theirs"), str(theirs))

    assert read_sbml(theirs).getModel().getId() == "theirs"
    assert read_sbml(ours).getModel().getId() == "ours"
    assert ours.read_bytes()[:2] == theirs.read_bytes()[:2]
    if filename.endswith(".zip"):
        with zipfile.ZipFile(ours) as z_ours, zipfile.ZipFile(theirs) as z_theirs:
            assert z_ours.namelist() == z_theirs.namelist()


_SBML_UTF8 = libsbml.writeSBMLToString(_model_doc())
_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>\n'
assert _SBML_UTF8.startswith(_DECLARATION)

#: files which libsbml's reader reads in its own way, which reading a path has
#: to keep: with a byte order mark, without an XML declaration (libsbml reports
#: it missing), and in a declared encoding other than UTF-8
_FILE_CONTENTS: dict[str, bytes] = {
    "bom": b"\xef\xbb\xbf" + _SBML_UTF8.encode("utf-8"),
    "no-declaration": _SBML_UTF8.removeprefix(_DECLARATION).encode("utf-8"),
    "iso-8859-1": _SBML_UTF8.replace("UTF-8", "ISO-8859-1").encode("latin-1"),
}


def _errors(doc: libsbml.SBMLDocument) -> list[tuple[int, int, int]]:
    """Get the id, line and severity of every error of a document."""
    return [
        (e.getErrorId(), e.getLine(), e.getSeverity())
        for e in (doc.getError(k) for k in range(doc.getNumErrors()))
    ]


@pytest.mark.parametrize("content", _FILE_CONTENTS.values(), ids=_FILE_CONTENTS)
def test_a_file_is_read_as_libsbml_reads_it(tmp_path: Path, content: bytes) -> None:
    """A path libsbml can open is read with the result of libsbml's reader.

    Compared are the document and the errors of the read, which `read_sbml`
    raises or logs and `validate_sbml` reports, down to their line numbers.
    """
    from sbmlutils.io.sbml import _read_document

    sbml_path = tmp_path / "model.xml"
    sbml_path.write_bytes(content)
    theirs: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path.resolve()))

    ours, _ = _read_document(sbml_path)

    assert ours.getModel().getName() == theirs.getModel().getName() == "über"
    assert _errors(ours) == _errors(theirs)
    assert ours.getLocationURI() == theirs.getLocationURI()


@pytest.mark.parametrize("content_id", ["bom", "iso-8859-1"])
def test_read_sbml_reads_a_file_libsbml_reads(tmp_path: Path, content_id: str) -> None:
    """A byte order mark and a declared encoding other than UTF-8 are read."""
    sbml_path = tmp_path / "model.xml"
    sbml_path.write_bytes(_FILE_CONTENTS[content_id])

    assert read_sbml(sbml_path).getModel().getName() == "über"


def test_read_sbml_reads_a_file_with_a_byte_order_mark_from_a_non_ascii_path(
    tmp_path: Path,
) -> None:
    """The python fallback for a non-ASCII path reads a UTF-8 byte order mark."""
    sbml_path = tmp_path / "ü" / "model.xml"
    sbml_path.parent.mkdir()
    sbml_path.write_bytes(_FILE_CONTENTS["bom"])

    doc = read_sbml(sbml_path)

    assert doc.getModel().getName() == "über"
    assert doc.getNumErrors() == 0


def test_read_sbml_raises_for_a_non_ascii_path_to_a_file_which_is_not_utf8(
    tmp_path: Path,
) -> None:
    """The python fallback reads UTF-8, the encoding SBML requires."""
    sbml_path = tmp_path / "ü" / "latin1.xml"
    sbml_path.parent.mkdir()
    sbml_path.write_bytes(_FILE_CONTENTS["iso-8859-1"])
    with pytest.raises(
        ValueError, match=r"latin1\.xml.*could not be read:\n.*E1017 .*utf-8"
    ):
        read_sbml(sbml_path)


def test_read_sbml_reports_a_file_error_which_is_no_decoding_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only a decoding error is invalid UTF-8, any other is an unreadable file."""
    from sbmlutils.io import files

    def raise_value_error(_path: Path) -> str:
        raise ValueError("embedded null byte")

    monkeypatch.setattr(files, "read_text", raise_value_error)
    with pytest.raises(ValueError, match=r"could not be read:\n.*E2 .*null byte"):
        read_sbml(tmp_path / "ü" / "model.xml")


def test_validate_sbml_reports_a_truncated_gzip_file(tmp_path: Path) -> None:
    """A compressed file which cannot be decompressed is reported, not raised."""
    from sbmlutils.io.sbml import validate_sbml

    sbml_path = tmp_path / "ü" / "model.xml.gz"
    write_sbml(_model_doc(), filepath=sbml_path)
    sbml_path.write_bytes(sbml_path.read_bytes()[:-20])

    result = validate_sbml(sbml_path)

    assert not result.is_valid()


def test_validate_sbml_raises_for_a_directory(tmp_path: Path) -> None:
    """A directory is no SBML file, and the error says so."""
    from sbmlutils.io.sbml import validate_sbml

    with pytest.raises(IsADirectoryError, match="is a directory"):
        validate_sbml(tmp_path)


_SBML_NO_DECLARATION = _SBML_WITHOUT_MODEL.removeprefix(
    '<?xml version="1.0" encoding="UTF-8"?>'
)


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(
            _SBML_NO_DECLARATION.replace("/>", '><model id="m"/></sbml>'),
            id="model",
        ),
        pytest.param(
            _SBML_COMP_LIBRARY.removeprefix('<?xml version="1.0" encoding="UTF-8"?>'),
            id="comp-library",
        ),
    ],
)
def test_read_sbml_reads_a_file_without_an_xml_declaration(
    tmp_path: Path, content: str
) -> None:
    """A missing declaration is an error of the document, it was read in full.

    libsbml reports `MissingXMLEncoding` and `BadXMLDecl` for it, both of
    severity error; the document is kept with them for the validation.
    """
    sbml_path = tmp_path / "model.xml"
    sbml_path.write_text(content, encoding="utf-8")

    doc = read_sbml(sbml_path)

    assert doc.getModel() is not None or (
        doc.getPlugin("comp").getNumModelDefinitions() == 1
    )
    assert libsbml.BadXMLDecl in {e[0] for e in _errors(doc)}


@pytest.mark.parametrize("encoding", ["FOO", "UTF-16"])
def test_read_sbml_raises_for_a_file_with_an_unknown_encoding(
    tmp_path: Path, encoding: str
) -> None:
    """A declaration libsbml cannot read leaves no document, which raises."""
    sbml_path = tmp_path / "model.xml"
    sbml_path.write_text(
        _SBML_WITHOUT_MODEL.replace("UTF-8", encoding).replace(
            "/>", '><model id="m"/></sbml>'
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"could not be read:\n.*E1003 "):
        read_sbml(sbml_path)
