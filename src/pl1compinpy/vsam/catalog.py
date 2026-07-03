from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
from pathlib import Path


class VSAMError(ValueError):
    pass


class VSAMType(str, Enum):
    KSDS = "KSDS"
    ESDS = "ESDS"
    RRDS = "RRDS"
    LDS = "LDS"


@dataclass
class VSAMDefinition:
    name: str
    organization: str
    key_offset: int = 0
    key_length: int = 0
    record_length: int | None = None
    catalog_file: str = "catalog.json"
    data_file: str = "data.bin"
    index: dict[str, tuple[int, int]] = field(default_factory=dict)
    rrds_slots: dict[str, tuple[int, int]] = field(default_factory=dict)
    next_rrn: int = 1


class VSAMCatalog:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.catalog_path = self.root / "catalog.json"
        self.data_path = self.root / "data.bin"
        self.definition = self._load()

    @classmethod
    def define(
        cls,
        root: Path | str,
        name: str,
        organization: VSAMType | str,
        *,
        key_offset: int = 0,
        key_length: int = 0,
        record_length: int | None = None,
    ) -> "VSAMCatalog":
        catalog = cls(root)
        catalog.definition = VSAMDefinition(
            name=name,
            organization=VSAMType(organization).value,
            key_offset=key_offset,
            key_length=key_length,
            record_length=record_length,
        )
        catalog.data_path.write_bytes(b"")
        catalog._save()
        return catalog

    def write(self, record: bytes, *, key: bytes | str | None = None, rrn: int | None = None, rba: int | None = None) -> int:
        organization = VSAMType(self.definition.organization)
        if organization == VSAMType.KSDS:
            return self._write_ksds(record, key)
        if organization == VSAMType.ESDS:
            return self._append_record(record)
        if organization == VSAMType.RRDS:
            return self._write_rrds(record, rrn)
        if organization == VSAMType.LDS:
            return self._write_lds(record, rba)
        raise VSAMError(f"Unsupported VSAM organization: {organization}")

    def read(self, *, key: bytes | str | None = None, rrn: int | None = None, rba: int | None = None, length: int | None = None) -> bytes:
        organization = VSAMType(self.definition.organization)
        if organization == VSAMType.KSDS:
            if key is None:
                raise VSAMError("KSDS read requires key")
            return self._read_at(*self.definition.index[self._key_text(key)])
        if organization == VSAMType.ESDS:
            if rba is None:
                raise VSAMError("ESDS read requires RBA")
            return self._read_record_at(rba)
        if organization == VSAMType.RRDS:
            if rrn is None:
                raise VSAMError("RRDS read requires RRN")
            return self._read_at(*self.definition.rrds_slots[str(rrn)])
        if organization == VSAMType.LDS:
            if rba is None or length is None:
                raise VSAMError("LDS read requires RBA and length")
            with self.data_path.open("rb") as handle:
                handle.seek(rba)
                return handle.read(length)
        raise VSAMError(f"Unsupported VSAM organization: {organization}")

    def _write_ksds(self, record: bytes, key: bytes | str | None) -> int:
        key_text = self._key_text(key) if key is not None else self._key_text(
            record[self.definition.key_offset : self.definition.key_offset + self.definition.key_length]
        )
        if key_text in self.definition.index:
            raise VSAMError(f"Duplicate KSDS key: {key_text}")
        rba = self._append_record(record)
        self.definition.index[key_text] = (rba, len(record))
        self._save()
        return rba

    def _write_rrds(self, record: bytes, rrn: int | None) -> int:
        rrn = rrn or self.definition.next_rrn
        if rrn <= 0:
            raise VSAMError("RRN is one-based")
        if self.definition.record_length:
            record = record[: self.definition.record_length].ljust(self.definition.record_length, b"\0")
        rba = self._append_raw(record)
        self.definition.rrds_slots[str(rrn)] = (rba, len(record))
        self.definition.next_rrn = max(self.definition.next_rrn, rrn + 1)
        self._save()
        return rrn

    def _write_lds(self, payload: bytes, rba: int | None) -> int:
        rba = rba or 0
        with self.data_path.open("r+b" if self.data_path.exists() else "w+b") as handle:
            handle.seek(rba)
            handle.write(payload)
        return rba

    def _append_record(self, record: bytes) -> int:
        rba = self._append_raw(len(record).to_bytes(4, "big") + record)
        self._save()
        return rba

    def _append_raw(self, payload: bytes) -> int:
        with self.data_path.open("ab") as handle:
            rba = handle.tell()
            handle.write(payload)
        return rba

    def _read_record_at(self, rba: int) -> bytes:
        with self.data_path.open("rb") as handle:
            handle.seek(rba)
            length_data = handle.read(4)
            if len(length_data) != 4:
                raise VSAMError(f"No record at RBA {rba}")
            length = int.from_bytes(length_data, "big")
            return handle.read(length)

    def _read_at(self, rba: int, length: int) -> bytes:
        with self.data_path.open("rb") as handle:
            handle.seek(rba)
            header = handle.read(4)
            if len(header) == 4 and int.from_bytes(header, "big") == length:
                return handle.read(length)
            handle.seek(rba)
            return handle.read(length)

    def _key_text(self, key: bytes | str) -> str:
        return key.hex() if isinstance(key, bytes) else key

    def _load(self) -> VSAMDefinition | None:
        if not self.catalog_path.exists():
            return None
        payload = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        return VSAMDefinition(**payload)

    def _save(self) -> None:
        if self.definition is None:
            return
        self.catalog_path.write_text(json.dumps(asdict(self.definition), indent=2, sort_keys=True), encoding="utf-8")
