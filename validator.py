import re

class ICE_Validator:
    def __init__(self, raw_content, filename):
        self.raw_content = raw_content
        self.filename = filename
        self.lines = raw_content.splitlines()
        self.errors = []
        self.warnings = []

    def run(self):
        if not self.lines:
            self.errors.append("File is empty.")
            return False

        self._check_filename()
        self._check_file_format()
        self._check_hdr()
        self._check_integrity()
        
        return len(self.errors) == 0

    def _check_filename(self):
        # Format: CW[YY][nnnn]LUM_319.V22
        pattern = r"^CW\d{2}\d{4}LUM_319\.V22$"
        if not re.match(pattern, self.filename.strip(), flags=re.IGNORECASE):
            self.errors.append(f"Filename Error: '{self.filename}' violates CW[YY][nnnn]LUM_319.V22 convention.")

    def _check_file_format(self):
        # Enforce CRLF as per CWR Standard
        if "\r\n" not in self.raw_content and "\n" in self.raw_content:
            self.errors.append("Format Error: Invalid line endings. CWR v2.2 requires CRLF (\\r\\n).")

    def _check_hdr(self):
        hdr = self.lines[0]
        if not hdr.startswith("HDR"):
            self.errors.append("Critical: HDR record missing.")
            return
        # Offset 4-5: Sender Type
        if hdr[3:5] != "01":
            self.errors.append(f"HDR Error: Sender Type (Pos 4-5) must be '01'. Found '{hdr[3:5]}'.")
        # Offset 60-64: EDI Version
        if hdr[59:64] != "01.10":
            self.errors.append(f"HDR Alignment Error: EDI Version '01.10' (Pos 60-64) missing. Found '{hdr[59:64]}'.")

    def _check_integrity(self):
        """Strict Coordinate Validation per CWR v2.2 Manual"""
        for idx, line in enumerate(self.lines):
            line_num = idx + 1
            if not line.strip(): continue
            rectype = line[0:3]

            # SPU: Publisher Record (Strict 182 chars)
            if rectype == "SPU":
                if len(line) != 182:
                    self.errors.append(f"Line {line_num} (SPU): Invalid record length ({len(line)}). Must be 182.")
                
                # SPU IPI: Pos 88-98
                ipi = line[87:98].strip()
                if ipi and (not ipi.isdigit() or len(ipi) != 11):
                    self.errors.append(f"Line {line_num} (SPU): IPI '{ipi}' at Pos 88-98 must be 11 digits.")

            # SWR: Writer Record
            if rectype == "SWR":
                # SWR IPI: Pos 116-126
                ipi = line[115:126].strip()
                if ipi and (not ipi.isdigit() or len(ipi) != 11):
                    self.errors.append(f"Line {line_num} (SWR): IPI '{ipi}' at Pos 116-126 must be 11 digits.")

            # REC: Recording Detail
            if rectype == "REC":
                # ISRC: Pos 250-261
                isrc = line[249:261].strip()
                if isrc:
                    if len(isrc) != 12:
                        self.errors.append(f"Line {line_num} (REC): ISRC '{isrc}' at Pos 250-261 must be 12 chars.")
                    if not isrc.startswith("USSHD"):
                        self.errors.append(f"Line {line_num} (REC): ISRC '{isrc}' must start with 'USSHD'.")
                
                # ISRC Validity: Pos 507
                validity = line[506:507]
                if validity != 'Y':
                    self.errors.append(f"Line {line_num} (REC): ISRC Validity (Pos 507) must be 'Y'.")

            # ORN: Work Origin
            if rectype == "ORN":
                # Cut Number: Pos 98-101
                cut_no = line[97:101].strip()
                if cut_no and not cut_no.isdigit():
                    self.errors.append(f"Line {line_num} (ORN): Cut Number (Pos 98-101) must be numeric. Found '{cut_no}'.")
